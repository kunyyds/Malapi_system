"""
日志配置工具
"""

import sys
from loguru import logger
from src.utils.config import settings


def setup_logger(name: str = None):
    """设置日志配置"""
    # 移除默认的处理器
    logger.remove()

    # print(settings.log_level)
    # 添加控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level.upper(),
        colorize=True
    )

    # 添加文件输出
    if settings.log_file:
        logger.add(
            settings.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=settings.log_level.upper(),
            rotation="10 MB",
            retention="30 days",
            compression="zip"
        )

    # 返回指定名称的logger
    if name:
        return logger.bind(name=name)
    return logger