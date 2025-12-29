"""
数据库连接和初始化
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
import asyncio
from typing import AsyncGenerator

from src.database.models import Base
from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# 异步引擎和会话（优化的SQLite配置）
print(settings.database_url_async)
async_engine = create_async_engine(
    settings.database_url_async,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,  # 1小时回收连接
    # SQLite特有配置 - 优化性能
    connect_args={
        "check_same_thread": False,
        "timeout": 30,  # 30秒超时
    } if "sqlite" in settings.database_url_async else {
        "server_settings": {
            "application_name": "malapi_backend",
            "jit": "off",  # 开发环境关闭JIT
        }
    }
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 同步引擎（用于初始化和迁移）
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    pool_pre_ping=True,
    # SQLite特有配置
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url_sync else {}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"数据库会话错误: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session():
    """获取同步数据库会话"""
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        logger.error(f"数据库会话错误: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


async def init_db():
    """初始化数据库"""
    try:
        logger.info("正在初始化数据库...")

        # 导入所有模型确保它们被注册
        from src.database.models import (
            MalAPIFunction, AttCKMapping, FunctionChild,
            MalAPIMetadata, LLMAnalysisCache, AttackPlanHistory, UsageStatistics
        )

        # 创建所有表
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # 检查并初始化 ATT&CK 表
        await init_attack_tables()

        logger.info("数据库初始化完成")

    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise


async def init_attack_tables():
    """
    检查并初始化 ATT&CK 表

    如果表不存在或数据为空，则提示用户运行导入脚本
    """
    try:
        async with async_engine.begin() as conn:
            # 检查表是否存在
            result = await conn.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('attack_tactics', 'attack_techniques')
            """))
            existing_tables = [row[0] for row in result.fetchall()]

            # 如果表不存在，使用原始SQL创建
            if 'attack_tactics' not in existing_tables:
                logger.info("创建 attack_tactics 表...")
                await conn.execute(text("""
                    CREATE TABLE attack_tactics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tactic_id VARCHAR(20) UNIQUE NOT NULL,
                        tactic_name_en VARCHAR(255) NOT NULL,
                        tactic_name_cn VARCHAR(255),
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                # 创建索引
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_attack_tactics_tactic_id
                    ON attack_tactics(tactic_id)
                """))
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_attack_tactics_name_en
                    ON attack_tactics(tactic_name_en)
                """))

            if 'attack_techniques' not in existing_tables:
                logger.info("创建 attack_techniques 表...")
                await conn.execute(text("""
                    CREATE TABLE attack_techniques (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        technique_id VARCHAR(20) UNIQUE NOT NULL,
                        technique_name VARCHAR(255) NOT NULL,
                        tactic_id VARCHAR(20) NOT NULL,
                        is_sub_technique BOOLEAN DEFAULT 0,
                        parent_technique_id VARCHAR(20),
                        description TEXT,
                        mitre_description TEXT,
                        mitre_url VARCHAR(500),
                        mitre_detection TEXT,
                        mitre_mitigation TEXT,
                        mitre_data_sources TEXT,
                        mitre_updated_at TIMESTAMP,
                        data_source VARCHAR(50) DEFAULT 'matrix_enterprise',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(tactic_id) REFERENCES attack_tactics(tactic_id) ON DELETE CASCADE
                    )
                """))
                # 创建索引
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_attack_techniques_technique_id
                    ON attack_techniques(technique_id)
                """))
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_attack_techniques_tactic_id
                    ON attack_techniques(tactic_id)
                """))
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_attack_techniques_is_sub
                    ON attack_techniques(is_sub_technique)
                """))
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_attack_techniques_parent_id
                    ON attack_techniques(parent_technique_id)
                """))
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_attack_techniques_name
                    ON attack_techniques(technique_name)
                """))

            # 检查表中是否有数据
            tactics_count = await conn.execute(text("SELECT COUNT(*) FROM attack_tactics"))
            tactics_count = tactics_count.scalar()

            techniques_count = await conn.execute(text("SELECT COUNT(*) FROM attack_techniques"))
            techniques_count = techniques_count.scalar()

            if tactics_count == 0 or techniques_count == 0:
                logger.warning(
                    "ATT&CK 表已创建但数据为空。请运行导入脚本: "
                    "cd /home/mine/workspace/MalAPI_system && python backend/scripts/maintenance/import_attack.py"
                )

            logger.info(f"ATT&CK 表状态: tactics={tactics_count}, techniques={techniques_count}")

    except Exception as e:
        logger.error(f"初始化 ATT&CK 表失败: {str(e)}")
        # 不抛出异常，允许应用继续启动


async def check_db_connection():
    """检查数据库连接"""
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            logger.info("数据库连接正常")
            return True
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return False


async def close_db():
    """关闭数据库连接"""
    try:
        await async_engine.dispose()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {str(e)}")


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.async_engine = async_engine
        self.sync_engine = sync_engine

    async def create_tables(self):
        """创建所有表"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # 同时初始化 ATT&CK 表
            await init_attack_tables()

    async def drop_tables(self):
        """删除所有表（谨慎使用）"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def reset_database(self):
        """重置数据库（删除并重新创建）"""
        logger.warning("正在重置数据库...")
        await self.drop_tables()
        await self.create_tables()
        logger.info("数据库重置完成")

    async def get_table_info(self, table_name: str = None):
        """获取表信息"""
        if table_name:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")
                )
                return result.fetchall()
        else:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                )
                return result.fetchall()

    async def execute_raw_sql(self, sql: str):
        """执行原始SQL"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text(sql))
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                raise e


# 全局数据库管理器实例
db_manager = DatabaseManager()