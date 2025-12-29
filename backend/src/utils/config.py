"""
应用配置管理
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置类"""

    # 应用基本配置
    app_name: str = "MalAPI System"
    debug: bool = False
    version: str = "1.0.0"

    # 数据库配置
    database_url: str = "sqlite:///./malapi.db"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "malapi"
    database_user: str = "malapi_user"
    database_password: str = "malapi_password"

    # Redis配置
    redis_url: str = "redis://localhost:6379"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # 文件路径配置
    files_base_path: str = "/home/mine/workspace/MalAPI_system/files"

    # LLM配置
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000

    # 缓存配置
    cache_ttl_seconds: int = 3600  # 1小时
    llm_cache_ttl_hours: int = 24   # 24小时

    # 日志配置
    log_level: str = "INFO"
    log_file: str = "malapi.log"

    # API配置
    api_prefix: str = "/api/v1"
    max_request_size: int = 10 * 1024 * 1024  # 10MB

    # 分页配置
    default_page_size: int = 20
    max_page_size: int = 100

    # 成本控制配置
    daily_llm_budget: float = 100.0  # 每日LLM预算（美元）
    cost_per_token_gpt4: float = 0.00003  # GPT-4每token成本
    cost_per_token_gpt35: float = 0.000002  # GPT-3.5每token成本

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def database_url_sync(self) -> str:
        """同步数据库URL"""
        if self.database_url.startswith("sqlite"):
            return self.database_url
        return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"

    @property
    def database_url_async(self) -> str:
        """异步数据库URL"""
        if self.database_url.startswith("sqlite"):
            return self.database_url#.replace("sqlite://", "sqlite+aiosqlite://")
        return f"postgresql+asyncpg://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"


# 全局配置实例
settings = Settings()