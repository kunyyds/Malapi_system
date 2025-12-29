-- MalAPI系统ATT&CK数据库架构重构迁移脚本
-- 创建时间: 2024-12-26
-- 目的: 简化attck_mappings表，创建独立的attack_tactics和attack_tactics表

-- ====================================================================
-- 步骤1：备份现有数据
-- ====================================================================

-- 备份现有attck_mappings表
CREATE TABLE IF NOT EXISTS attck_mappings_backup AS
SELECT * FROM attck_mappings;

-- 验证备份
SELECT COUNT(*) AS backup_count FROM attck_mappings_backup;

-- ====================================================================
-- 步骤2：创建attack_tactics表（战术表）
-- ====================================================================

CREATE TABLE IF NOT EXISTS attack_tactics (
    id BIGSERIAL PRIMARY KEY,
    tactic_id VARCHAR(20) NOT NULL UNIQUE,
    tactic_name_en VARCHAR(255) NOT NULL,
    tactic_name_cn VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_attack_tactics_tactic_id ON attack_tactics(tactic_id);
CREATE INDEX idx_attack_tactics_name_en ON attack_tactics(tactic_name_en);

-- 创建触发器自动更新updated_at
CREATE TRIGGER update_attack_tactics_updated_at
    BEFORE UPDATE ON attack_tactics
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- ====================================================================
-- 步骤3：创建attack_techniques表（技术表）
-- ====================================================================

CREATE TABLE IF NOT EXISTS attack_techniques (
    id BIGSERIAL PRIMARY KEY,
    technique_id VARCHAR(20) NOT NULL UNIQUE,
    technique_name VARCHAR(255) NOT NULL,
    tactic_id VARCHAR(20) NOT NULL,
    is_sub_technique BOOLEAN DEFAULT FALSE,
    parent_technique_id VARCHAR(20),

    -- 基础描述
    description TEXT,

    -- MITRE官方数据字段（预留，暂不填充）
    mitre_description TEXT,
    mitre_url VARCHAR(500),
    mitre_detection TEXT,
    mitre_mitigation TEXT,
    mitre_data_sources TEXT,
    mitre_updated_at TIMESTAMP,

    -- 元数据
    data_source VARCHAR(50) DEFAULT 'matrix_enterprise',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (tactic_id) REFERENCES attack_tactics(tactic_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_technique_id) REFERENCES attack_techniques(technique_id) ON DELETE SET NULL
);

-- 创建索引
CREATE INDEX idx_attack_techniques_technique_id ON attack_techniques(technique_id);
CREATE INDEX idx_attack_techniques_tactic_id ON attack_techniques(tactic_id);
CREATE INDEX idx_attack_techniques_is_sub ON attack_techniques(is_sub_technique);
CREATE INDEX idx_attack_techniques_parent_id ON attack_techniques(parent_technique_id);
CREATE INDEX idx_attack_techniques_name ON attack_techniques(technique_name);

-- 创建复合索引（优化常见查询）
CREATE INDEX idx_attack_techniques_tactic_sub ON attack_techniques(tactic_id, is_sub_technique);

-- 创建触发器自动更新updated_at
CREATE TRIGGER update_attack_techniques_updated_at
    BEFORE UPDATE ON attack_techniques
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- ====================================================================
-- 步骤4：重建简化的attck_mappings表
-- ====================================================================

-- 删除旧表
DROP TABLE IF EXISTS attck_mappings CASCADE;

-- 创建新的简化映射表（仅存储映射关系）
CREATE TABLE IF NOT EXISTS attck_mappings (
    id BIGSERIAL PRIMARY KEY,
    function_id BIGINT NOT NULL,
    technique_id VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (function_id) REFERENCES malapi_functions(id) ON DELETE CASCADE,
    FOREIGN KEY (technique_id) REFERENCES attack_techniques(technique_id) ON DELETE CASCADE,

    -- 唯一约束：一个函数不能重复映射同一个技术
    UNIQUE (function_id, technique_id)
);

-- 创建索引
CREATE INDEX idx_attck_mappings_function_id ON attck_mappings(function_id);
CREATE INDEX idx_attck_mappings_technique_id ON attck_mappings(technique_id);

-- 创建复合索引（优化JOIN查询）
CREATE INDEX idx_attck_mappings_func_tech ON attck_mappings(function_id, technique_id);

-- ====================================================================
-- 步骤5：创建兼容视图（保持API兼容性）
-- ====================================================================

-- 创建兼容视图，模拟旧的attck_mappings结构
CREATE OR REPLACE VIEW v_attck_mappings_legacy AS
SELECT
    am.id,
    am.function_id,
    am.technique_id,
    at.technique_name,
    att.tactic_name_en AS tactic_name,
    at.description,
    at.is_sub_technique,
    at.parent_technique_id,
    at.mitre_description,
    at.mitre_url,
    at.mitre_detection,
    at.mitre_mitigation,
    at.mitre_updated_at,
    am.created_at
FROM attck_mappings am
INNER JOIN attack_techniques at ON am.technique_id = at.technique_id
INNER JOIN attack_tactics att ON at.tactic_id = att.tactic_id;

-- 创建增强的函数-技术映射视图
CREATE OR REPLACE VIEW v_function_techniques AS
SELECT
    f.id AS function_id,
    f.hash_id,
    f.alias,
    f.summary,
    at.technique_id,
    at.technique_name,
    att.tactic_id,
    att.tactic_name_en,
    att.tactic_name_cn,
    at.is_sub_technique,
    at.parent_technique_id,
    at.mitre_description,
    at.mitre_url
FROM malapi_functions f
INNER JOIN attck_mappings am ON f.id = am.function_id
INNER JOIN attack_techniques at ON am.technique_id = at.technique_id
INNER JOIN attack_tactics att ON at.tactic_id = att.tactic_id;

-- ====================================================================
-- 步骤6：数据迁移（需要先运行import_attack_data.py填充基础数据）
-- ====================================================================

-- 注意：此步骤需要在运行import_attack_data.py之后执行
-- 迁移现有映射关系（仅迁移有效的technique_id）

-- 迁移映射数据（过滤无效的technique_id）
INSERT INTO attck_mappings (function_id, technique_id, created_at)
SELECT DISTINCT
    am.function_id,
    am.technique_id,
    am.created_at
FROM attck_mappings_backup am
WHERE EXISTS (
    SELECT 1 FROM attack_techniques at
    WHERE at.technique_id = am.technique_id
)
ON CONFLICT (function_id, technique_id) DO NOTHING;

-- ====================================================================
-- 步骤7：验证数据完整性
-- ====================================================================

DO $$
DECLARE
    old_count INTEGER;
    new_count INTEGER;
    invalid_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO old_count FROM attck_mappings_backup;
    SELECT COUNT(*) INTO new_count FROM attck_mappings;
    SELECT COUNT(*) INTO invalid_count FROM attck_mappings_backup am
    WHERE NOT EXISTS (
        SELECT 1 FROM attack_techniques at
        WHERE at.technique_id = am.technique_id
    );

    RAISE NOTICE '========================================';
    RAISE NOTICE '数据迁移验证报告';
    RAISE NOTICE '========================================';
    RAISE NOTICE '原始映射数: %', old_count;
    RAISE NOTICE '新映射数: %', new_count;
    RAISE NOTICE '清理的无效映射数: %', invalid_count;

    IF invalid_count > 0 THEN
        RAISE NOTICE '✓ 已清理无效映射（technique_id不在matrix-enterprise.json中）';
    END IF;

    IF new_count = old_count - invalid_count THEN
        RAISE NOTICE '✓ 数据迁移验证通过';
    ELSE
        RAISE NOTICE '⚠ 警告: 数据迁移数量不匹配';
    END IF;

    RAISE NOTICE '========================================';
END $$;

-- ====================================================================
-- 步骤8：更新sequence
-- ====================================================================

SELECT setval('attck_mappings_id_seq', (SELECT MAX(id) FROM attck_mappings));

-- ====================================================================
-- 完成
-- ====================================================================

-- 显示迁移完成信息
SELECT
    'ATT&CK数据库架构重构完成' AS status,
    (SELECT COUNT(*) FROM attack_tactics) AS tactics_count,
    (SELECT COUNT(*) FROM attack_techniques) AS techniques_count,
    (SELECT COUNT(*) FROM attck_mappings) AS mappings_count;
