"""
测试配置管理模块
提供测试参数的集中管理，支持从环境变量和配置文件读取
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

@dataclass
class TestConfig:
    """测试配置数据类"""

    # 基础配置
    project_root: str = str(Path(__file__).parent)
    backend_root: str = str(Path(__file__).parent)

    # 文件扫描配置
    scanner_max_workers: int = 4
    scanner_max_depth: int = 10

    # 测试文件数量配置
    parser_test_files_count: int = 15
    import_test_files_count: int = 8
    scan_result_display_limit: int = 10

    # 路径配置 - 智能检测的候选路径
    files_search_paths: List[str] = None
    default_files_path: str = "/home/mine/workspace/MalAPI_system/files"

    # 数据库配置
    database_url: str = "sqlite:///./malapi.db"
    use_sqlite_fallback: bool = True

    # 日志配置
    log_level: str = "INFO"
    log_file: str = "test_data_processing.log"

    # 测试行为配置
    strict_validation: bool = False
    validate_attack_ids: bool = True
    enable_progress_callback: bool = True

    # 性能配置
    import_batch_size: int = 1000
    import_concurrent_limit: int = 10

    def __post_init__(self):
        """初始化后处理，填充默认值"""
        if self.files_search_paths is None:
            self.files_search_paths = [
                str(Path(self.project_root).parent / "files"),  # 默认位置
                str(Path(self.project_root) / "files"),        # 当前项目目录下
                self.default_files_path,                       # 绝对路径
            ]

        # 从环境变量覆盖配置
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置"""
        env_mappings = {
            'MALAPI_TEST_MAX_WORKERS': ('scanner_max_workers', int),
            'MALAPI_TEST_MAX_DEPTH': ('scanner_max_depth', int),
            'MALAPI_TEST_PARSER_FILES': ('parser_test_files_count', int),
            'MALAPI_TEST_IMPORT_FILES': ('import_test_files_count', int),
            'MALAPI_TEST_DATABASE_URL': ('database_url', str),
            'MALAPI_TEST_LOG_LEVEL': ('log_level', str),
            'MALAPI_TEST_FILES_PATH': ('default_files_path', str),
            'MALAPI_TEST_STRICT': ('strict_validation', lambda x: x.lower() == 'true'),
            'MALAPI_TEST_VALIDATE_ATTACK': ('validate_attack_ids', lambda x: x.lower() == 'true'),
        }

        for env_key, (attr_name, converter) in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                try:
                    setattr(self, attr_name, converter(env_value))
                except (ValueError, TypeError) as e:
                    print(f"警告: 环境变量 {env_key} 的值 '{env_value}' 无法转换，使用默认值: {e}")

    def get_possible_files_paths(self) -> List[Path]:
        """获取可能的文件路径列表"""
        return [Path(path) for path in self.files_search_paths]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'scanner_config': {
                'max_workers': self.scanner_max_workers,
                'max_depth': self.scanner_max_depth,
            },
            'test_counts': {
                'parser_files': self.parser_test_files_count,
                'import_files': self.import_test_files_count,
                'scan_display_limit': self.scan_result_display_limit,
            },
            'files_paths': self.files_search_paths,
            'database': {
                'url': self.database_url,
                'sqlite_fallback': self.use_sqlite_fallback,
            },
            'logging': {
                'level': self.log_level,
                'file': self.log_file,
            },
            'validation': {
                'strict': self.strict_validation,
                'attack_ids': self.validate_attack_ids,
            },
            'performance': {
                'batch_size': self.import_batch_size,
                'concurrent_limit': self.import_concurrent_limit,
            },
        }

    def print_config(self):
        """打印当前配置"""
        print("=" * 60)
        print("🔧 测试配置")
        print("=" * 60)
        config_dict = self.to_dict()
        for category, settings in config_dict.items():
            print(f"\n📁 {category}:")
            if isinstance(settings, dict):
                for key, value in settings.items():
                    print(f"  {key}: {value}")
            elif isinstance(settings, list):
                for i, value in enumerate(settings):
                    print(f"  [{i}]: {value}")
            else:
                print(f"  {settings}")
        print("=" * 60)


# 全局配置实例
test_config = TestConfig()


def get_config() -> TestConfig:
    """获取测试配置实例"""
    return test_config


def update_config(**kwargs):
    """更新配置"""
    global test_config
    for key, value in kwargs.items():
        if hasattr(test_config, key):
            setattr(test_config, key, value)
        else:
            print(f"警告: 未知的配置项 '{key}'")


if __name__ == "__main__":
    # 测试配置显示
    config = get_config()
    config.print_config()