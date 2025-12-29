-- MalAPI系统数据库Schema (PostgreSQL版本)
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
    cpp_code TEXT,                                   -- C++源代码
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
ALTER TABLE malapi_functions ADD CONSTRAINT unique_function UNIQUE (hash_id, alias);

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

-- ATT&CK技术映射表
CREATE TABLE IF NOT EXISTS attck_mappings (
    id BIGSERIAL PRIMARY KEY,
    function_id BIGINT NOT NULL,
    technique_id VARCHAR(20) NOT NULL,               -- T1059, T1490等
    technique_name VARCHAR(255),                     -- Command and Scripting Interpreter等
    tactic_name VARCHAR(255),                        -- 持久化、执行等战术名称
    description TEXT,                                -- 技术描述
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_attck_mappings_function_id ON attck_mappings(function_id);
CREATE INDEX IF NOT EXISTS idx_attck_mappings_technique_id ON attck_mappings(technique_id);
CREATE INDEX IF NOT EXISTS idx_attck_mappings_tactic_name ON attck_mappings(tactic_name);

-- 子函数关系表
CREATE TABLE IF NOT EXISTS function_children (
    id BIGSERIAL PRIMARY KEY,
    parent_function_id BIGINT NOT NULL,
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
    function_id BIGINT NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,              -- code_explanation, attack_scenario, mitigation
    llm_model VARCHAR(100),                          -- 使用的LLM模型
    analysis_result TEXT,                            -- 分析结果
    confidence_score DECIMAL(3,2),                   -- 置信度分数
    token_usage INTEGER DEFAULT 0,                   -- Token使用量
    cost_usd DECIMAL(10,4) DEFAULT 0,              -- 成本（美元）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP                             -- 过期时间
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
ALTER TABLE usage_statistics ADD CONSTRAINT unique_date UNIQUE (date);

-- 创建触发器
CREATE TRIGGER update_usage_statistics_updated_at BEFORE UPDATE
    ON usage_statistics FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- 创建全文搜索索引
CREATE INDEX IF NOT EXISTS idx_malapi_functions_search ON malapi_functions USING GIN(
    to_tsvector('english', COALESCE(alias, '') || ' ' || COALESCE(summary, '') || ' ' || COALESCE(cpp_code, ''))
);

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

-- 插入一些初始数据（ATT&CK技术信息）
-- 注意：这些是示例数据，实际使用时需要真实的function_id
COMMIT;