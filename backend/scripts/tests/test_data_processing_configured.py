#!/usr/bin/env python3
"""
配置化数据处理层测试脚本

特性：
1. 集中配置管理
2. 环境变量支持
3. 智能路径检测
4. 详细的测试报告
5. 性能统计和分析

使用方法：
1. 默认配置: python test_data_processing_configured.py
2. 自定义配置: MALAPI_TEST_PARSER_FILES=20 python test_data_processing_configured.py
3. 显示配置: python test_config.py
"""

import asyncio
import logging
import sys
import json
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入配置
from test_config import get_config, TestConfig

# 配置日志
def setup_logging(config: TestConfig):
    """设置日志系统"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    handlers = [
        logging.StreamHandler(),
        logging.FileHandler(config.log_file)
    ]

    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format=log_format,
        handlers=handlers
    )

logger = logging.getLogger(__name__)


async def test_file_scanner(config: TestConfig):
    """测试文件扫描器"""
    logger.info("=" * 50)
    logger.info("测试文件扫描器")
    logger.info("=" * 50)

    try:
        from src.parsers.file_scanner import FileScanner

        # 创建扫描器（使用配置参数）
        scanner = FileScanner(
            max_workers=config.scanner_max_workers,
            max_depth=config.scanner_max_depth
        )

        # 智能检测测试目录路径（使用配置的候选路径）
        files_directory = None
        possible_paths = config.get_possible_files_paths()

        for path in possible_paths:
            if path.exists() and path.is_dir():
                files_directory = path
                logger.info(f"找到测试数据目录: {files_directory}")
                break

        if not files_directory:
            logger.error(f"❌ 未找到测试数据目录，尝试了以下路径:")
            for path in possible_paths:
                logger.error(f"  - {path}")
            logger.error(f"请确保 files 目录存在且包含 manifest.json 文件")
            return None

        # 扫描manifest.json文件
        logger.info(f"扫描目录: {files_directory}")
        scan_result = await scanner.scan_directory(
            root_path=files_directory,
            pattern="manifest",
            recursive=True
        )

        # 输出扫描结果
        logger.info(f"扫描结果: {scan_result.get_summary()}")
        logger.info(f"找到文件数: {scan_result.get_file_count()}")

        # 显示前N个文件路径（使用配置的显示限制）
        if scan_result.files:
            logger.info(f"前{config.scan_result_display_limit}个文件:")
            display_limit = min(config.scan_result_display_limit, len(scan_result.files))
            for i, file_path in enumerate(scan_result.files[:display_limit]):
                logger.info(f"  {i+1}. {file_path}")

        # 打印统计信息
        scanner.print_statistics()

        return scan_result

    except Exception as e:
        logger.error(f"文件扫描器测试失败: {e}")
        logger.error("可能的原因:")
        logger.error("  1. 依赖模块未正确安装")
        logger.error("  2. 文件系统权限问题")
        logger.error("  3. 模块导入路径错误")
        return None


async def test_manifest_parser(scan_result, config: TestConfig):
    """测试manifest解析器"""
    logger.info("=" * 50)
    logger.info("测试manifest解析器")
    logger.info("=" * 50)

    if not scan_result or not scan_result.files:
        logger.warning("没有文件可供测试解析器")
        return []

    try:
        from src.parsers.manifest_parser import ManifestParser

        # 创建解析器（使用配置参数）
        parser = ManifestParser(
            strict_mode=config.strict_validation,
            validate_attack_ids=config.validate_attack_ids
        )

        parse_results = []
        test_files_count = min(config.parser_test_files_count, len(scan_result.files))
        test_files = scan_result.files[:test_files_count]

        logger.info(f"测试解析 {test_files_count} 个文件")

        for i, file_path in enumerate(test_files):
            logger.info(f"解析文件 {i+1}/{test_files_count}: {file_path.name}")

            try:
                parse_result = await parser.parse_file(file_path)

                if parse_result.is_valid:
                    logger.info(f"  ✅ 解析成功: {parse_result.data.get('alias', 'N/A')}")
                    logger.info(f"     ATT&CK技术: {parse_result.data.get('attck', [])}")
                else:
                    logger.warning(f"  ❌ 解析失败: {parse_result.get_error_summary()}")

                parse_results.append(parse_result)

            except Exception as e:
                logger.error(f"  ❌ 解析异常: {e}")

        # 输出统计信息
        parser_stats = parser.get_statistics()
        success_rate = parser_stats.get('success_rate', 0)
        logger.info(f"解析统计: 成功率 {success_rate:.1f}%")
        logger.info(f"平均错误数: {parser_stats.get('average_errors_per_file', 0):.1f}")

        return parse_results

    except Exception as e:
        logger.error(f"manifest解析器测试失败: {e}")
        logger.error("可能的原因:")
        logger.error("  1. JSON格式错误")
        logger.error("  2. 数据验证规则问题")
        logger.error("  3. 文件编码问题")
        return []


async def test_database_connection(config: TestConfig):
    """测试数据库连接"""
    logger.info("=" * 50)
    logger.info("测试数据库连接")
    logger.info("=" * 50)

    try:
        from src.database.connection import async_engine, AsyncSessionLocal

        # 测试数据库连接
        async with AsyncSessionLocal() as session:
            # 执行简单查询测试连接
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            logger.info("✅ 数据库连接成功")

            # 检查表是否存在 - 支持多种数据库类型
            from src.database.models import MalAPIFunction

            # 检测数据库类型
            db_url = str(async_engine.url).lower()
            logger.info(f"数据库类型: {db_url.split('://')[0] if '://' in db_url else 'unknown'}")

            if 'sqlite' in db_url:
                # SQLite 查询
                result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='malapi_functions'"))
            elif 'postgresql' in db_url:
                # PostgreSQL 查询
                result = await session.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE tablename = 'malapi_functions'"))
            else:
                # 通用查询 - 尝试直接查询表
                try:
                    result = await session.execute(text("SELECT COUNT(*) FROM malapi_functions LIMIT 1"))
                    table_exists = True
                except Exception:
                    table_exists = False
                logger.info(f"数据库类型检测: {db_url}")

            if 'sqlite' in db_url or 'postgresql' in db_url:
                table_exists = result.fetchone() is not None

            if table_exists:
                logger.info("✅ 数据库表已创建")
            else:
                logger.info("🔧 数据库表未创建，正在初始化...")
                from src.database.connection import init_db
                await init_db()
                logger.info("✅ 数据库初始化完成")

        return True

    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        logger.error("请检查以下配置:")
        logger.error("  1. 数据库服务是否运行")
        logger.error(f"  2. 数据库URL配置: {config.database_url}")
        logger.error("  3. 网络连接是否正常")
        if config.use_sqlite_fallback and 'postgresql' in str(config.database_url).lower():
            logger.info("💡 建议使用SQLite作为测试数据库")
        return False


async def test_full_import_workflow(config: TestConfig, scan_result):
    """测试完整的导入工作流程"""
    logger.info("=" * 50)
    logger.info("测试完整导入工作流程")
    logger.info("=" * 50)

    if not scan_result or scan_result.get_file_count() == 0:
        logger.warning("没有文件可供导入测试")
        return None

    try:
        from src.database.connection import AsyncSessionLocal
        from src.importers.import_manager import ImportManager

        # 创建导入管理器
        session_factory = AsyncSessionLocal
        manager = ImportManager(session_factory)

        # 设置进度回调（如果启用）
        if config.enable_progress_callback:
            def progress_callback(current, total, message):
                percentage = (current / total) * 100
                logger.info(f"进度: {percentage:.1f}% - {message}")

            manager.set_progress_callback(progress_callback)

        # 智能检测测试目录路径（复用配置的候选路径）
        files_directory = None
        possible_paths = config.get_possible_files_paths()

        for path in possible_paths:
            if path.exists() and path.is_dir():
                files_directory = path
                logger.info(f"使用测试数据目录: {files_directory}")
                break

        if not files_directory:
            logger.error(f"❌ 未找到测试数据目录，导入流程测试取消")
            return None

        # 限制测试文件数量（使用配置）
        original_files = scan_result.files.copy()
        test_files_count = min(config.import_test_files_count, len(original_files))

        scan_result.files = original_files[:test_files_count]
        scan_result.files_found = test_files_count

        # 执行导入流程
        logger.info(f"开始完整导入流程测试（{test_files_count}个文件）...")
        result = await manager.import_from_directory(
            directory_path=files_directory,
            pattern="manifest",
            recursive=True
        )

        # 输出结果
        logger.info(f"导入流程完成: {result.get_overall_summary()}")

        # 输出详细统计
        stats = result.get_stage_statistics()
        logger.info("详细统计信息:")
        for stage, stage_stats in stats.items():
            if isinstance(stage_stats, dict):
                logger.info(f"  {stage}:")
                for key, value in stage_stats.items():
                    logger.info(f"    {key}: {value}")

        # 打印管理器统计
        manager.print_statistics()

        # 恢复原始文件列表（用于统计）
        scan_result.files = original_files
        scan_result.files_found = len(original_files)

        return result

    except Exception as e:
        logger.error(f"❌ 完整导入流程测试失败: {e}")
        logger.error("可能的原因:")
        logger.error("  1. 数据库连接问题")
        logger.error("  2. 内存不足")
        logger.error("  3. 并发处理问题")
        return None


async def main():
    """主测试函数"""
    # 加载配置
    config = get_config()
    setup_logging(config)

    test_start_time = datetime.now()
    logger.info("🚀 开始配置化数据处理层测试")
    logger.info(f"⏰ 测试开始时间: {test_start_time}")
    logger.info(f"📂 项目路径: {config.project_root}")

    # 测试环境信息
    logger.info("=" * 50)
    logger.info("测试环境信息")
    logger.info("=" * 50)
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"工作目录: {Path.cwd()}")
    logger.info(f"环境变量: MALAPI_TEST_PARSER_FILES={os.getenv('MALAPI_TEST_PARSER_FILES', 'not set')}")

    # 检查关键依赖
    try:
        import sqlalchemy
        logger.info(f"SQLAlchemy版本: {sqlalchemy.__version__}")
    except ImportError:
        logger.warning("SQLAlchemy 未安装 - 请激活malapi-backend环境: conda activate malapi-backend")

    try:
        from src.parsers.manifest_parser import ManifestParser
        from src.parsers.file_scanner import FileScanner
        from src.importers.import_manager import ImportManager
        logger.info("✅ 核心模块导入成功")
    except ImportError as e:
        logger.error(f"❌ 核心模块导入失败: {e}")
        logger.error("解决方案:")
        logger.error("  1. 确保已激活conda环境: conda activate malapi-backend")
        logger.error("  2. 确保在正确的目录中运行测试")
        return

    try:
        # 测试1: 文件扫描器
        scan_result = await test_file_scanner(config)

        # 测试2: manifest解析器
        parse_results = await test_manifest_parser(scan_result, config)

        # 测试3: 数据库连接
        db_connected = await test_database_connection(config)

        # 测试4: 完整导入流程（仅在数据库连接成功且找到文件时执行）
        if db_connected and scan_result and scan_result.get_file_count() > 0:
            import_result = await test_full_import_workflow(config, scan_result)
        else:
            skip_reasons = []
            if not db_connected:
                skip_reasons.append("数据库连接失败")
            if not scan_result or scan_result.get_file_count() == 0:
                skip_reasons.append("没有找到文件")
            logger.warning(f"跳过完整导入流程测试（{'、'.join(skip_reasons)}）")

        # 测试完成
        test_end_time = datetime.now()
        test_duration = test_end_time - test_start_time

        logger.info("=" * 50)
        logger.info("🎉 配置化数据处理层测试完成")
        logger.info("=" * 50)
        logger.info(f"⏰ 测试结束时间: {test_end_time}")
        logger.info(f"⏱️ 总耗时: {test_duration.total_seconds():.2f} 秒")

        # 输出测试总结
        logger.info("测试总结:")
        logger.info(f"  文件扫描: {'✅ 成功' if scan_result else '❌ 失败'}")
        if scan_result:
            logger.info(f"    找到文件数: {scan_result.get_file_count()}")
        logger.info(f"  manifest解析: {'✅ 成功' if parse_results else '❌ 失败'}")
        if parse_results:
            successful_parses = sum(1 for r in parse_results if r.is_valid)
            logger.info(f"    解析成功数: {successful_parses}/{len(parse_results)}")
        logger.info(f"  数据库连接: {'✅ 成功' if db_connected else '❌ 失败'}")

        # 配置使用说明
        logger.info("=" * 50)
        logger.info("📋 配置使用说明")
        logger.info("=" * 50)
        logger.info("环境变量配置示例:")
        logger.info("  MALAPI_TEST_PARSER_FILES=20    # 测试文件数量")
        logger.info("  MALAPI_TEST_MAX_WORKERS=8      # 并发工作线程数")
        logger.info("  MALAPI_TEST_DATABASE_URL=sqlite:///./test.db  # 数据库URL")
        logger.info("  MALAPI_TEST_STRICT=true         # 严格验证模式")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        logger.error("请检查:")
        logger.error("  1. 错误日志详情")
        logger.error("  2. 依赖是否正确安装")
        logger.error("  3. 配置是否正确")


if __name__ == "__main__":
    print("🚀 MalAPI配置化数据处理层测试")
    print("📋 特性: 集中配置管理、环境变量支持、智能路径检测、详细报告")
    print("📝 测试日志将保存到 test_data_processing.log")
    print("⚙️  运行 'python test_config.py' 查看当前配置")
    print("=" * 80)

    # 运行异步测试
    asyncio.run(main())