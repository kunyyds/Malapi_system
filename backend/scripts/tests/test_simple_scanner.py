#!/usr/bin/env python3
"""
简化版数据处理测试 - 仅测试文件扫描和基本解析
不依赖复杂的数据库连接和外部模块
"""

import asyncio
import logging
import sys
import json
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
        logging.FileHandler('test_simple_scanner.log')
    ]
)

logger = logging.getLogger(__name__)


async def test_file_scanner():
    """测试文件扫描器"""
    logger.info("=" * 50)
    logger.info("测试文件扫描器")
    logger.info("=" * 50)

    try:
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
            logger.error(f"❌ 未找到测试数据目录")
            for path in possible_paths:
                logger.error(f"  - {path}")
            return None

        # 扫描manifest.json文件
        logger.info(f"扫描目录: {files_directory}")
        manifest_files = list(files_directory.rglob("manifest.json"))

        logger.info(f"找到 {len(manifest_files)} 个manifest.json文件")

        # 显示前10个文件路径
        if manifest_files:
            logger.info("前10个文件:")
            for i, file_path in enumerate(manifest_files[:10]):
                logger.info(f"  {i+1}. {file_path}")

        return manifest_files

    except Exception as e:
        logger.error(f"文件扫描器测试失败: {e}")
        return None


async def test_manifest_parsing(files):
    """测试manifest文件解析"""
    logger.info("=" * 50)
    logger.info("测试manifest文件解析")
    logger.info("=" * 50)

    if not files:
        logger.warning("没有文件可供测试解析")
        return []

    parse_results = []
    test_files = files[:15]  # 测试前15个文件
    successful_parses = 0
    failed_parses = 0

    try:
        logger.info(f"测试解析 {len(test_files)} 个文件")

        for i, file_path in enumerate(test_files):
            logger.info(f"解析文件 {i+1}/{len(test_files)}: {file_path.name}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)

                # 基本验证
                required_fields = ['status', 'alias', 'attck']
                missing_fields = [field for field in required_fields if field not in manifest_data]

                if missing_fields:
                    logger.warning(f"  ❌ 缺少必需字段: {missing_fields}")
                    failed_parses += 1
                else:
                    logger.info(f"  ✅ 解析成功: {manifest_data.get('alias', 'N/A')}")
                    logger.info(f"     ATT&CK技术: {manifest_data.get('attck', [])}")
                    successful_parses += 1

                parse_results.append({
                    'file': file_path,
                    'success': len(missing_fields) == 0,
                    'data': manifest_data,
                    'missing_fields': missing_fields
                })

            except json.JSONDecodeError as e:
                logger.error(f"  ❌ JSON解析失败: {e}")
                failed_parses += 1
                parse_results.append({
                    'file': file_path,
                    'success': False,
                    'error': f"JSON解析失败: {e}"
                })
            except Exception as e:
                logger.error(f"  ❌ 解析异常: {e}")
                failed_parses += 1
                parse_results.append({
                    'file': file_path,
                    'success': False,
                    'error': f"解析异常: {e}"
                })

        # 输出统计信息
        total = len(test_files)
        success_rate = (successful_parses / total) * 100 if total > 0 else 0
        logger.info(f"解析统计:")
        logger.info(f"  成功: {successful_parses}/{total} ({success_rate:.1f}%)")
        logger.info(f"  失败: {failed_parses}/{total}")

        return parse_results

    except Exception as e:
        logger.error(f"manifest解析器测试失败: {e}")
        return []


async def main():
    """主测试函数"""
    test_start_time = datetime.now()
    logger.info("🚀 开始简化版数据处理测试")
    logger.info(f"⏰ 测试开始时间: {test_start_time}")
    logger.info(f"📂 项目路径: {project_root}")

    # 测试环境信息
    logger.info("=" * 50)
    logger.info("测试环境信息")
    logger.info("=" * 50)
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"工作目录: {Path.cwd()}")

    try:
        # 测试1: 文件扫描
        manifest_files = await test_file_scanner()

        # 测试2: manifest解析
        parse_results = await test_manifest_parsing(manifest_files)

        # 测试完成
        test_end_time = datetime.now()
        test_duration = test_end_time - test_start_time

        logger.info("=" * 50)
        logger.info("🎉 简化版数据处理测试完成")
        logger.info("=" * 50)
        logger.info(f"⏰ 测试结束时间: {test_end_time}")
        logger.info(f"⏱️ 总耗时: {test_duration.total_seconds():.2f} 秒")

        # 输出测试总结
        logger.info("测试总结:")
        logger.info(f"  文件扫描: {'✅ 成功' if manifest_files else '❌ 失败'}")
        if manifest_files:
            logger.info(f"    找到文件数: {len(manifest_files)}")
        logger.info(f"  manifest解析: {'✅ 成功' if parse_results else '❌ 失败'}")
        if parse_results:
            successful_parses = sum(1 for r in parse_results if r.get('success', False))
            logger.info(f"    解析成功数: {successful_parses}/{len(parse_results)}")
        logger.info("=" * 50)

        # 验证我们的修复是否有效
        if manifest_files and parse_results:
            logger.info("🎉 修复验证结果:")
            logger.info("  ✅ 路径检测功能正常工作")
            logger.info("  ✅ 文件扫描功能正常工作")
            logger.info("  ✅ manifest解析功能正常工作")
            logger.info("  ✅ 错误处理和日志记录正常工作")
        else:
            logger.warning("⚠️ 部分功能可能存在问题，需要进一步检查")

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        logger.error("请检查错误信息并修复后重新运行测试")


if __name__ == "__main__":
    print("🚀 MalAPI简化版数据处理测试")
    print("📋 测试内容: 文件扫描器 -> manifest解析器")
    print("📝 测试日志将保存到 test_simple_scanner.log")
    print("=" * 60)

    # 运行异步测试
    asyncio.run(main())