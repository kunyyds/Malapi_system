-- MalAPI系统数据库Schema
-- 创建时间: 2024-12-19

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 恶意软件API函数主表
CREATE TABLE IF NOT EXISTS malapi_functions (
    id BIGSERIAL PRIMARY KEY,
    hash_id VARCHAR(40) NOT NULL,                    -- 目录哈希ID
    alias VARCHAR(255) NOT NULL,                     -- 功能别名
    root_function VARCHAR(255),                      -- 原始函数名
    summary TEXT,                                    -- 功能描述
    cpp_code LONGTEXT,                              -- C++源代码
    cpp_filepath VARCHAR(500),                      -- C++文件路径
    manifest_json JSONB,                            -- 完整manifest内容
    tries INTEGER DEFAULT 1,                        -- 尝试次数
    status VARCHAR(20) DEFAULT 'ok',                -- 状态
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_malapi_functions_hash_id ON malapi_functions(hash_id);
CREATE INDEX IF NOT EXISTS idx_malapi_functions_alias ON malapi_functions(alias);
CREATE INDEX IF NOT EXISTS idx_malapi_functions_root_function ON malapi_functions(root_function);
CREATE INDEX IF NOT EXISTS idx_malapi_functions_status ON malapi_functions(status);
CREATE INDEX IF NOT EXISTS idx_malapi_functions_manifest_json ON malapi_functions USING GIN(manifest_json);

-- 创建唯一约束
ALTER TABLE malapi_functions ADD CONSTRAINT unique_hash_id IF NOT EXISTS UNIQUE (hash_id);
ALTER TABLE malapi_functions ADD CONSTRAINT unique_alias IF NOT EXISTS UNIQUE (alias);

-- 创建触发器自动更新updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_malapi_functions_updated_at BEFORE UPDATE
    ON malapi_functions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- ATT&CK技术映射表 (多对多关系表)
CREATE TABLE IF NOT EXISTS attck_mappings (
    id BIGSERIAL PRIMARY KEY,
    function_id BIGINT NOT NULL REFERENCES malapi_functions(id) ON DELETE CASCADE,
    technique_id VARCHAR(20) NOT NULL,               -- T1059, T1490等
    technique_name VARCHAR(255),                     -- Command and Scripting Interpreter等
    tactic_name VARCHAR(255),                        -- 持久化、执行等战术名称
    description TEXT,                                -- 技术描述

    -- 子技术支持字段
    is_sub_technique BOOLEAN DEFAULT FALSE,          -- 是否为子技术
    parent_technique_id VARCHAR(20),                 -- 父技术ID（用于子技术，如T1055.001的父技术是T1055）

    -- MITRE官方数据缓存字段（可选，用于缓存MITRE官网数据）
    mitre_description TEXT,                          -- MITRE官方描述
    mitre_url VARCHAR(500),                          -- MITRE官方URL
    mitre_detection TEXT,                            -- MITRE检测建议
    mitre_mitigation TEXT,                           -- MITRE缓解措施
    mitre_updated_at TIMESTAMP,                      -- MITRE数据更新时间

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_attck_mappings_function_id ON attck_mappings(function_id);
CREATE INDEX IF NOT EXISTS idx_attck_mappings_technique_id ON attck_mappings(technique_id);
CREATE INDEX IF NOT EXISTS idx_attck_mappings_tactic_name ON attck_mappings(tactic_name);
CREATE INDEX IF NOT EXISTS idx_attck_mappings_sub_technique ON attck_mappings(is_sub_technique);
CREATE INDEX IF NOT EXISTS idx_attck_mappings_parent_technique ON attck_mappings(parent_technique_id);

-- 子函数关系表
CREATE TABLE IF NOT EXISTS function_children (
    id BIGSERIAL PRIMARY KEY,
    parent_function_id BIGINT NOT NULL REFERENCES malapi_functions(id) ON DELETE CASCADE,
    child_function_name VARCHAR(255) NOT NULL,       -- sub_41316d等
    child_alias VARCHAR(255),                        -- LzmaDecoder等
    child_description TEXT,                          -- 子函数描述
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_function_children_parent_id ON function_children(parent_function_id);
CREATE INDEX IF NOT EXISTS idx_function_children_child_name ON function_children(child_function_name);

-- 元数据表（存储文件路径、版本等信息）
CREATE TABLE IF NOT EXISTS malapi_metadata (
    id BIGSERIAL PRIMARY KEY,
    hash_id VARCHAR(40) NOT NULL UNIQUE,
    source_hlil_path VARCHAR(500),                   -- HLIL源文件路径
    alias_map_json_path VARCHAR(500),                -- 别名映射文件路径
    generated_cpp_path VARCHAR(500),                 -- 生成的CPP文件路径
    total_functions INTEGER DEFAULT 0,               -- 总函数数量
    processing_status VARCHAR(20) DEFAULT 'pending', -- 处理状态
    error_message TEXT,                              -- 错误信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_malapi_metadata_hash_id ON malapi_metadata(hash_id);
CREATE INDEX IF NOT EXISTS idx_malapi_metadata_processing_status ON malapi_metadata(processing_status);

-- 创建触发器
CREATE TRIGGER update_malapi_metadata_updated_at BEFORE UPDATE
    ON malapi_metadata FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- LLM分析结果缓存表
CREATE TABLE IF NOT EXISTS llm_analysis_cache (
    id BIGSERIAL PRIMARY KEY,
    function_id BIGINT NOT NULL REFERENCES malapi_functions(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,              -- code_explanation, attack_scenario, mitigation
    llm_model VARCHAR(100),                          -- 使用的LLM模型
    analysis_result LONGTEXT,                        -- 分析结果
    confidence_score DECIMAL(3,2),                   -- 置信度分数
    token_usage INTEGER DEFAULT 0,                   -- Token使用量
    cost_usd DECIMAL(10,4) DEFAULT 0,              -- 成本（美元）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP                            -- 过期时间
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_llm_analysis_cache_function_type ON llm_analysis_cache(function_id, analysis_type);
CREATE INDEX IF NOT EXISTS idx_llm_analysis_cache_expires_at ON llm_analysis_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_llm_analysis_cache_model ON llm_analysis_cache(llm_model);

-- 攻击方案历史表
CREATE TABLE IF NOT EXISTS attack_plan_history (
    id BIGSERIAL PRIMARY KEY,
    plan_id VARCHAR(100) NOT NULL UNIQUE,           -- 方案唯一标识
    objective TEXT NOT NULL,                         -- 攻击目标
    selected_techniques JSONB,                       -- 选择的技术列表
    constraints JSONB,                              -- 约束条件
    environment TEXT,                                -- 环境描述
    plan_result JSONB,                              -- 生成的方案结果
    risk_assessment TEXT,                            -- 风险评估
    llm_model VARCHAR(100),                          -- 使用的LLM模型
    token_usage INTEGER DEFAULT 0,                   -- Token使用量
    cost_usd DECIMAL(10,4) DEFAULT 0,              -- 成本
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_attack_plan_history_plan_id ON attack_plan_history(plan_id);
CREATE INDEX IF NOT EXISTS idx_attack_plan_history_created_at ON attack_plan_history(created_at);
CREATE INDEX IF NOT EXISTS idx_attack_plan_history_selected_techniques ON attack_plan_history USING GIN(selected_techniques);

-- 使用统计表
CREATE TABLE IF NOT EXISTS usage_statistics (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    total_requests INTEGER DEFAULT 0,
    llm_requests INTEGER DEFAULT 0,
    search_requests INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10,4) DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建唯一约束
ALTER TABLE usage_statistics ADD CONSTRAINT unique_date IF NOT EXISTS UNIQUE (date);

-- 创建触发器
CREATE TRIGGER update_usage_statistics_updated_at BEFORE UPDATE
    ON usage_statistics FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- 创建全文搜索索引
CREATE INDEX IF NOT EXISTS idx_malapi_functions_search ON malapi_functions USING GIN(
    to_tsvector('english', COALESCE(alias, '') || ' ' || COALESCE(summary, '') || ' ' || COALESCE(cpp_code, ''))
);

-- 创建分区表（如果需要处理大量数据，可以考虑按哈希ID分区）
-- ALTER TABLE malapi_functions PARTITION BY HASH (hash_id);
-- CREATE TABLE malapi_functions_p0 PARTITION OF malapi_functions FOR VALUES WITH (MODULUS 4, REMAINDER 0);
-- CREATE TABLE malapi_functions_p1 PARTITION OF malapi_functions FOR VALUES WITH (MODULUS 4, REMAINDER 1);
-- CREATE TABLE malapi_functions_p2 PARTITION OF malapi_functions FOR VALUES WITH (MODULUS 4, REMAINDER 2);
-- CREATE TABLE malapi_functions_p3 PARTITION OF malapi_functions FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- 插入一些初始数据（ATT&CK技术信息）
-- 注意: function_id=0 为示例数据,实际使用时应替换为真实的function_id
INSERT INTO attck_mappings (function_id, technique_id, technique_name, tactic_name, description) VALUES
(0, 'T1027', 'Obfuscated Files or Information', 'Defense Evasion', 'Adversaries may attempt to make an executable or file difficult to discover or analyze by encrypting, encoding, or otherwise obfuscating its contents on the system.'),
(0, 'T1055', 'Process Injection', 'Defense Evasion', 'Adversaries may inject code into processes in order to evade process-based defenses as well as possibly elevate privileges.'),
(0, 'T1140', 'Deobfuscate/Decode Files or Information', 'Defense Evasion', 'Adversaries may use Obfuscated Files or Information to hide malicious code from security tools.'),
(0, 'T1497', 'Virtualization/Sandbox Evasion', 'Defense Evasion', 'Adversaries may employ various means to detect and avoid virtualization and analysis environments.')
ON CONFLICT DO NOTHING;

-- 创建视图以便查询
CREATE OR REPLACE VIEW function_with_attack AS
SELECT
    f.id,
    f.hash_id,
    f.alias,
    f.root_function,
    f.summary,
    f.created_at,
    f.updated_at,
    array_agg(DISTINCT am.technique_id) as technique_ids,
    array_agg(DISTINCT am.technique_name) as technique_names,
    array_agg(DISTINCT am.tactic_name) as tactic_names
FROM malapi_functions f
LEFT JOIN attck_mappings am ON f.id = am.function_id
GROUP BY f.id, f.hash_id, f.alias, f.root_function, f.summary, f.created_at, f.updated_at;

-- 创建用于统计的函数
CREATE OR REPLACE FUNCTION update_function_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE malapi_metadata SET total_functions = total_functions + 1 WHERE hash_id = NEW.hash_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE malapi_metadata SET total_functions = total_functions - 1 WHERE hash_id = OLD.hash_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器自动更新函数计数
CREATE TRIGGER trigger_update_function_count
    AFTER INSERT OR DELETE ON malapi_functions
    FOR EACH ROW EXECUTE PROCEDURE update_function_count();

COMMIT;