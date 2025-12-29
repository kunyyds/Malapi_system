#!/usr/bin/env python3
"""
数据处理层测试脚本

设计思路：
1. 测试文件扫描、解析、导入的完整流程
2. 验证教学级注释代码的功能
3. 提供详细的测试报告和性能分析
4. 确保系统在真实数据上的表现

使用方法：
python test_data_processing.py
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_data_processing.log')
    ]
)

logger = logging.getLogger(__name__)


async def test_file_scanner():
    """测试文件扫描器"""
    logger.info("=" * 50)
    logger.info("测试文件扫描器")
    logger.info("=" * 50)

    from src.parsers.file_scanner import FileScanner

    # 创建扫描器
    scanner = FileScanner(max_workers=4, max_depth=10)

    # 智能检测测试目录路径
    files_directory = None
    possible_paths = [
        project_root.parent / "files",  # 默认位置
        project_root / "files",        # 当前项目目录下
        Path("/home/mine/workspace/MalAPI_system/files"),  # 绝对路径
    ]

    for path in possible_paths:
        if path.exists() and path.is_dir():
            files_directory = path
            logger.info(f"找到测试数据目录: {files_directory}")
            break

    if not files_directory:
        logger.error(f"❌ 未找到测试数据目录，尝试了以下路径:")
        for path in possible_paths:
            logger.error(f"  - {path}")
        logger.error("请确保 files 目录存在且包含 manifest.json 文件")
        return None

    try:
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

        # 显示前10个文件路径
        if scan_result.files:
            logger.info("前10个文件:")
            for i, file_path in enumerate(scan_result.files[:10]):
                logger.info(f"  {i+1}. {file_path}")

        # 打印统计信息
        scanner.print_statistics()

        return scan_result

    except Exception as e:
        logger.error(f"文件扫描器测试失败: {e}")
        return None


async def test_manifest_parser(scan_result):
    """测试manifest解析器"""
    logger.info("=" * 50)
    logger.info("测试manifest解析器")
    logger.info("=" * 50)

    if not scan_result or not scan_result.files:
        logger.warning("没有文件可供测试解析器")
        return []

    from src.parsers.manifest_parser import ManifestParser

    # 创建解析器
    parser = ManifestParser(strict_mode=False, validate_attack_ids=True)

    parse_results = []
    test_files = scan_result.files[:15]  # 测试前15个文件

    try:
        logger.info(f"测试解析 {len(test_files)} 个文件")

        for i, file_path in enumerate(test_files):
            logger.info(f"解析文件 {i+1}/{len(test_files)}: {file_path.name}")

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
        logger.info(f"解析统计: 成功率 {parser_stats.get('success_rate', 0):.1f}%")
        logger.info(f"平均错误数: {parser_stats.get('average_errors_per_file', 0):.1f}")

        return parse_results

    except Exception as e:
        logger.error(f"manifest解析器测试失败: {e}")
        return []


async def test_database_connection():
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
            from src.database.connection import async_engine

            # 检测数据库类型
            db_url = str(async_engine.url).lower()
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
        logger.error("  2. .env 文件中的数据库配置是否正确")
        logger.error("  3. 网络连接是否正常")
        return False


async def test_full_import_workflow():
    """测试完整的导入工作流程"""
    logger.info("=" * 50)
    logger.info("测试完整导入工作流程")
    logger.info("=" * 50)

    try:
        from src.database.connection import AsyncSessionLocal
        from src.importers.import_manager import ImportManager

        # 创建导入管理器
        session_factory = AsyncSessionLocal
        manager = ImportManager(session_factory)

        # 设置进度回调
        def progress_callback(current, total, message):
            percentage = (current / total) * 100
            logger.info(f"进度: {percentage:.1f}% - {message}")

        manager.set_progress_callback(progress_callback)

        # 智能检测测试目录路径（复用前面的逻辑）
        files_directory = None
        possible_paths = [
            project_root.parent / "files",  # 默认位置
            project_root / "files",        # 当前项目目录下
            Path("/home/mine/workspace/MalAPI_system/files"),  # 绝对路径
        ]

        for path in possible_paths:
            if path.exists() and path.is_dir():
                files_directory = path
                logger.info(f"使用测试数据目录: {files_directory}")
                break

        if not files_directory:
            logger.error(f"❌ 未找到测试数据目录，导入流程测试取消")
            return None

        # 执行导入流程（仅测试少量文件以节省时间）
        logger.info("开始完整导入流程测试...")
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

        return result

    except Exception as e:
        logger.error(f"❌ 完整导入流程测试失败: {e}")
        return None


async def main():
    """主测试函数"""
    test_start_time = datetime.now()
    logger.info("🚀 开始数据处理层测试")
    logger.info(f"⏰ 测试开始时间: {test_start_time}")
    logger.info(f"📂 项目路径: {project_root}")

    # 测试环境信息
    logger.info("=" * 50)
    logger.info("测试环境信息")
    logger.info("=" * 50)
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"工作目录: {Path.cwd()}")

    # 检查关键依赖
    try:
        import sqlalchemy
        logger.info(f"SQLAlchemy版本: {sqlalchemy.__version__}")
    except ImportError:
        logger.warning("SQLAlchemy 未安装")

    try:
        from src.parsers.manifest_parser import ManifestParser
        from src.parsers.file_scanner import FileScanner
        from src.importers.import_manager import ImportManager
        logger.info("✅ 核心模块导入成功")
    except ImportError as e:
        logger.error(f"❌ 核心模块导入失败: {e}")
        return

    try:
        # 测试1: 文件扫描器
        scan_result = await test_file_scanner()

        # 测试2: manifest解析器
        parse_results = await test_manifest_parser(scan_result)

        # 测试3: 数据库连接
        db_connected = await test_database_connection()

        # 测试4: 完整导入流程（仅在数据库连接成功时执行）
        if db_connected and scan_result and scan_result.get_file_count() > 0:
            # 限制测试文件数量以节省时间
            original_files = scan_result.files.copy()
            scan_result.files = original_files[:8]  # 测试前8个文件（合理数量的完整测试）
            scan_result.files_found = 8

            import_result = await test_full_import_workflow()

            # 恢复原始文件列表（用于统计）
            scan_result.files = original_files
            scan_result.files_found = len(original_files)
        else:
            logger.warning("跳过完整导入流程测试（数据库连接失败或没有文件）")

        test_end_time = datetime.now()
        test_duration = test_end_time - test_start_time

        logger.info("=" * 50)
        logger.info("🎉 数据处理层测试完成")
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
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        logger.error("请检查错误信息并修复后重新运行测试")


if __name__ == "__main__":
    print("🚀 MalAPI数据处理层测试")
    print("📋 测试内容: 文件扫描器 -> manifest解析器 -> 数据库连接 -> 完整导入流程")
    print("📝 测试日志将保存到 test_data_processing.log")
    print("=" * 60)

    # 运行异步测试
    asyncio.run(main())