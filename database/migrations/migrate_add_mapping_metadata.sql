-- 数据库迁移脚本: 添加ATT&CK映射关系元数据
-- 创建时间: 2024-12-26
-- 说明: 为attck_mappings表添加映射类型、置信度、执行上下文等字段
--      支持多对多关系的语义增强

-- 开始事务
BEGIN;

-- 1. 添加新字段
ALTER TABLE attck_mappings
    ADD COLUMN IF NOT EXISTS mapping_type VARCHAR(20) DEFAULT 'related',
    ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(3,2) DEFAULT 0.50,
    ADD COLUMN IF NOT EXISTS execution_context TEXT,
    ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 2. 添加注释
COMMENT ON COLUMN attck_mappings.mapping_type IS '映射类型: primary(主要实现), secondary(辅助支持), related(相关涉及)';
COMMENT ON COLUMN attck_mappings.confidence_score IS '置信度分数: 0.00-1.00,表示该函数实现该技术的置信度';
COMMENT ON COLUMN attck_mappings.execution_context IS '执行上下文: 描述函数如何实现该技术';
COMMENT ON COLUMN attck_mappings.is_verified IS '是否已人工验证';

-- 3. 创建新索引
CREATE INDEX IF NOT EXISTS idx_attck_mappings_mapping_type ON attck_mappings(mapping_type);
CREATE INDEX IF NOT EXISTS idx_attck_mappings_confidence ON attck_mappings(confidence_score);
CREATE INDEX IF NOT EXISTS idx_attck_mappings_verified ON attck_mappings(is_verified);
CREATE INDEX IF NOT EXISTS idx_attck_mappings_sub_technique ON attck_mappings(is_sub_technique);

-- 4. 创建复合索引（优化常见查询）
CREATE INDEX IF NOT EXISTS idx_attck_mappings_function_type ON attck_mappings(function_id, mapping_type);
CREATE INDEX IF NOT EXISTS idx_attck_mappings_technique_type ON attck_mappings(technique_id, mapping_type);

-- 5. 创建触发器自动更新updated_at
CREATE TRIGGER update_attck_mappings_updated_at BEFORE UPDATE
    ON attck_mappings FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();

-- 6. 为现有数据设置默认值（可选）
-- 将所有现有映射的mapping_type设置为'related',置信度设置为0.50
UPDATE attck_mappings
SET
    mapping_type = 'related',
    confidence_score = 0.50,
    is_verified = FALSE
WHERE mapping_type IS NULL OR confidence_score IS NULL;

-- 7. 创建用于查询映射关系的视图（可选增强）
CREATE OR REPLACE VIEW function_attack_mappings_enhanced AS
SELECT
    f.id as function_id,
    f.hash_id,
    f.alias,
    f.root_function,
    f.summary,
    am.id as mapping_id,
    am.technique_id,
    am.technique_name,
    am.tactic_name,
    am.mapping_type,
    am.confidence_score,
    am.execution_context,
    am.is_verified,
    am.is_sub_technique,
    am.parent_technique_id,
    am.created_at as mapping_created_at,
    am.updated_at as mapping_updated_at
FROM malapi_functions f
INNER JOIN attck_mappings am ON f.id = am.function_id
ORDER BY f.id, am.mapping_type DESC, am.confidence_score DESC;

-- 8. 创建统计视图（可选）
CREATE OR REPLACE VIEW technique_statistics AS
SELECT
    technique_id,
    technique_name,
    tactic_name,
    COUNT(*) as total_functions,
    COUNT(*) FILTER (WHERE mapping_type = 'primary') as primary_functions,
    COUNT(*) FILTER (WHERE mapping_type = 'secondary') as secondary_functions,
    COUNT(*) FILTER (WHERE mapping_type = 'related') as related_functions,
    AVG(confidence_score) as avg_confidence_score,
    COUNT(*) FILTER (WHERE is_verified = TRUE) as verified_count
FROM attck_mappings
GROUP BY technique_id, technique_name, tactic_name
ORDER BY total_functions DESC;

COMMIT;

-- 验证迁移
-- 检查新字段是否添加成功
SELECT
    column_name,
    data_type,
    column_default
FROM information_schema.columns
WHERE table_name = 'attck_mappings'
AND column_name IN ('mapping_type', 'confidence_score', 'execution_context', 'is_verified', 'updated_at')
ORDER BY ordinal_position;

-- 检查索引是否创建成功
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'attck_mappings'
AND indexname LIKE 'idx_attck_mappings_%'
ORDER BY indexname;
