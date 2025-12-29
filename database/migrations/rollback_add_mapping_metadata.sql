-- 数据库迁移回滚脚本: 移除ATT&CK映射关系元数据
-- 创建时间: 2024-12-26
-- 说明: 回滚migrate_add_mapping_metadata.sql的更改

-- ⚠️ 警告: 此操作将删除mapping_type、confidence_score等字段及其相关数据
-- ⚠️ 请确认已备份重要数据后再执行

BEGIN;

-- 1. 删除视图
DROP VIEW IF EXISTS function_attack_mappings_enhanced;
DROP VIEW IF EXISTS technique_statistics;

-- 2. 删除触发器
DROP TRIGGER IF EXISTS update_attck_mappings_updated_at ON attck_mappings;

-- 3. 删除索引
DROP INDEX IF EXISTS idx_attck_mappings_mapping_type;
DROP INDEX IF EXISTS idx_attck_mappings_confidence;
DROP INDEX IF EXISTS idx_attck_mappings_verified;
DROP INDEX IF EXISTS idx_attck_mappings_sub_technique;
DROP INDEX IF EXISTS idx_attck_mappings_function_type;
DROP INDEX IF EXISTS idx_attck_mappings_technique_type;

-- 4. 删除新增的字段
ALTER TABLE attck_mappings
    DROP COLUMN IF EXISTS mapping_type,
    DROP COLUMN IF EXISTS confidence_score,
    DROP COLUMN IF EXISTS execution_context,
    DROP COLUMN IF EXISTS is_verified,
    DROP COLUMN IF EXISTS updated_at;

COMMIT;

-- 验证回滚
-- 检查字段是否已删除
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'attck_mappings'
ORDER BY ordinal_position;
