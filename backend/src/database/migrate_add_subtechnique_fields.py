"""
数据库迁移脚本：添加子技术支持字段

运行方式：
    python -m src.database.migrate_add_subtechnique_fields
"""

import asyncio
from sqlalchemy import text
from src.database.connection import async_engine
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


async def migrate():
    """执行数据库迁移"""
    try:
        async with async_engine.begin() as conn:
            # 检查表是否存在
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='attck_mappings'")
            )
            table_exists = result.fetchone()

            if not table_exists:
                logger.info("表 attck_mappings 不存在，跳过迁移")
                return

            # 获取现有列
            result = await conn.execute(text("PRAGMA table_info(attck_mappings)"))
            existing_columns = {row[1] for row in result.fetchall()}
            logger.info(f"现有列: {existing_columns}")

            # 添加子技术支持字段
            new_columns = {
                'is_sub_technique': "BOOLEAN DEFAULT 0",
                'parent_technique_id': "VARCHAR(20)",
                'mitre_description': "TEXT",
                'mitre_url': "VARCHAR(500)",
                'mitre_detection': "TEXT",
                'mitre_mitigation': "TEXT",
                'mitre_updated_at': "DATETIME"
            }

            for column_name, column_def in new_columns.items():
                if column_name not in existing_columns:
                    logger.info(f"添加列: {column_name}")
                    await conn.execute(
                        text(f"ALTER TABLE attck_mappings ADD COLUMN {column_name} {column_def}")
                    )
                else:
                    logger.info(f"列 {column_name} 已存在，跳过")

            # 为现有数据更新 is_sub_technique 字段
            logger.info("更新现有数据的 is_sub_technique 字段")
            await conn.execute(
                text("""
                    UPDATE attck_mappings
                    SET is_sub_technique = CASE
                        WHEN technique_id LIKE '%.%' THEN 1
                        ELSE 0
                    END
                    WHERE is_sub_technique IS NULL OR is_sub_technique = 0
                """)
            )

            # 为现有子技术数据更新 parent_technique_id 字段
            logger.info("更新现有子技术的 parent_technique_id 字段")
            await conn.execute(
                text("""
                    UPDATE attck_mappings
                    SET parent_technique_id = SUBSTR(technique_id, 1, INSTR(technique_id, '.') - 1)
                    WHERE technique_id LIKE '%.%' AND (parent_technique_id IS NULL OR parent_technique_id = '')
                """)
            )

            # 创建索引
            logger.info("创建索引")
            indexes = [
                ("idx_attck_is_sub_technique", "CREATE INDEX IF NOT EXISTS idx_attck_is_sub_technique ON attck_mappings(is_sub_technique)"),
                ("idx_attck_parent_technique_id", "CREATE INDEX IF NOT EXISTS idx_attck_parent_technique_id ON attck_mappings(parent_technique_id)")
            ]

            for index_name, sql in indexes:
                try:
                    await conn.execute(text(sql))
                    logger.info(f"索引 {index_name} 创建成功")
                except Exception as e:
                    logger.warning(f"索引 {index_name} 创建失败（可能已存在）: {e}")

            await conn.commit()
            logger.info("数据库迁移完成！")

    except Exception as e:
        logger.error(f"数据库迁移失败: {str(e)}")
        raise


async def verify_migration():
    """验证迁移结果"""
    try:
        async with async_engine.begin() as conn:
            # 检查新字段是否添加成功
            result = await conn.execute(text("PRAGMA table_info(attck_mappings)"))
            columns = result.fetchall()
            column_names = {col[1] for col in columns}

            expected_columns = {
                'is_sub_technique', 'parent_technique_id',
                'mitre_description', 'mitre_url', 'mitre_detection', 'mitre_mitigation', 'mitre_updated_at'
            }

            missing_columns = expected_columns - column_names
            if missing_columns:
                logger.warning(f"缺少的列: {missing_columns}")
            else:
                logger.info("所有新字段都已添加")

            # 统计子技术数量
            result = await conn.execute(
                text("SELECT COUNT(*) FROM attck_mappings WHERE is_sub_technique = 1")
            )
            sub_count = result.scalar()
            logger.info(f"数据库中共有 {sub_count} 个子技术记录")

    except Exception as e:
        logger.error(f"验证迁移失败: {str(e)}")


if __name__ == "__main__":
    logger.info("开始数据库迁移...")
    asyncio.run(migrate())
    logger.info("开始验证迁移...")
    asyncio.run(verify_migration())
