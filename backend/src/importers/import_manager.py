"""
import_manager.py - 数据导入管理器

设计思路：
1. 整合文件扫描、解析、验证、导入的完整流程
2. 提供统一的高级接口，简化使用复杂度
3. 支持大规模数据处理和进度监控
4. 实现完整的错误处理和恢复机制

为什么需要导入管理器：
- 协调各个组件的工作
- 提供简单的统一接口
- 处理复杂的流程控制
- 集中管理和监控

使用示例：
>>> manager = ImportManager(session_factory)
>>> result = await manager.import_from_directory("/path/to/files")
>>> print(f"处理完成: {result.get_summary()}")
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.parsers.file_scanner import FileScanner, ScanResult
from src.parsers.manifest_parser import ManifestParser, ManifestParseResult
from src.importers.batch_importer import BatchImporter, ImportResult
from src.exceptions.data_exceptions import (
    DataImportError,
    ParseError,
    ErrorCodes
)


@dataclass
class ImportProcessResult:
    """
    完整导入流程结果封装类

    设计思路：
    1. 封装从扫描到导入的完整流程结果
    2. 提供详细的统计数据和错误信息
    3. 支持分阶段结果查询
    4. 便于生成报告和用户反馈

    为什么使用dataclass：
    1. 自动生成初始化方法
    2. 类型提示支持
    3. 内存效率高
    4. 支持字段默认值
    """
    # 扫描阶段结果
    scan_result: Optional[ScanResult] = None

    # 解析阶段结果
    parse_results: List[ManifestParseResult] = field(default_factory=list)
    successful_parses: int = 0
    failed_parses: int = 0

    # 导入阶段结果
    import_result: Optional[ImportResult] = None

    # 整体统计
    total_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # 配置信息
    source_directory: Optional[str] = None
    total_files_found: int = 0

    def get_overall_summary(self) -> str:
        """
        获取整体处理摘要

        返回值：
        - str: 整体处理摘要

        摘要内容：
        1. 文件扫描结果
        2. 数据解析结果
        3. 数据库导入结果
        4. 总体处理时间
        5. 成功率统计
        """
        parts = []

        # 扫描结果
        if self.scan_result:
            parts.append(f"扫描找到{self.scan_result.get_file_count()}个文件")

        # 解析结果
        if self.total_files_found > 0:
            parse_success_rate = (self.successful_parses / self.total_files_found) * 100
            parts.append(f"解析成功{self.successful_parses}个文件({parse_success_rate:.1f}%)")

            if self.failed_parses > 0:
                parts.append(f"解析失败{self.failed_parses}个文件")

        # 导入结果
        if self.import_result:
            parts.append(f"导入{self.import_result.get_summary()}")

        # 总体时间
        if self.total_time > 0:
            parts.append(f"总耗时{self.total_time:.2f}s")

            # 计算总体速度
            if self.successful_parses > 0:
                speed = self.successful_parses / self.total_time
                parts.append(f"平均速度{speed:.1f}文件/秒")

        return "，".join(parts) + "。"

    def get_stage_statistics(self) -> Dict[str, Any]:
        """
        获取各阶段统计信息

        返回值：
        - Dict[str, Any]: 各阶段详细统计

        统计内容：
        1. 扫描阶段统计
        2. 解析阶段统计
        3. 导入阶段统计
        4. 总体性能指标
        """
        stats = {
            'total_time': self.total_time,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'source_directory': self.source_directory
        }

        # 扫描统计
        if self.scan_result:
            stats['scan'] = {
                'files_found': self.scan_result.get_file_count(),
                'directories_scanned': self.scan_result.directories_scanned,
                'scan_time': self.scan_result.scan_time,
                'scan_errors': len(self.scan_result.errors),
                'scan_warnings': len(self.scan_result.warnings)
            }

        # 解析统计
        stats['parse'] = {
            'total_files': self.total_files_found,
            'successful_parses': self.successful_parses,
            'failed_parses': self.failed_parses,
            'parse_success_rate': (self.successful_parses / max(1, self.total_files_found)) * 100
        }

        # 导入统计
        if self.import_result:
            stats['import'] = {
                'total_records': self.import_result.total_records,
                'successful_imports': self.import_result.successful_imports,
                'failed_imports': self.import_result.failed_imports,
                'skipped_imports': self.import_result.skipped_imports,
                'duplicate_imports': self.import_result.duplicate_imports,
                'import_time': self.import_result.processing_time,
                'import_success_rate': self.import_result.get_success_rate()
            }

        return stats


class ImportManager:
    """
    数据导入管理器

    设计思路：
    1. 整合文件扫描、解析、导入的完整工作流
    2. 提供简单易用的高级接口
    3. 支持灵活的配置和选项
    4. 实现完整的进度监控和错误处理

    核心功能：
    - 自动化文件发现和处理
    - 智能错误处理和恢复
    - 详细的进度跟踪和报告
    - 性能优化和资源管理

    为什么需要管理器：
    1. 降低使用复杂度
    2. 统一错误处理策略
    3. 优化整体性能
    4. 提供完整的监控能力

    使用场景：
    1. 批量导入新数据
    2. 定期数据更新
    3. 数据迁移和备份
    4. 系统初始化
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        scanner_config: Optional[Dict[str, Any]] = None,
        parser_config: Optional[Dict[str, Any]] = None,
        importer_config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化导入管理器

        参数说明：
        - session_factory: SQLAlchemy异步会话工厂
        - scanner_config: 文件扫描器配置
        - parser_config: 解析器配置
        - importer_config: 导入器配置

        配置说明：
        1. scanner_config: 控制文件扫描行为
        2. parser_config: 控制数据解析策略
        3. importer_config: 控制数据库导入性能

        设计考虑：
        1. 各组件独立配置，提高灵活性
        2. 默认配置确保开箱即用
        3. 支持运行时配置修改
        4. 配置验证和错误处理
        """
        self.session_factory = session_factory
        self.logger = logging.getLogger(__name__)

        # 初始化各个组件
        self._initialize_components(scanner_config, parser_config, importer_config)

        # 管理器统计信息
        self.stats = {
            'total_imports': 0,
            'total_files_processed': 0,
            'total_time': 0.0,
            'last_import_time': None
        }

        # 进度回调函数
        self.progress_callback: Optional[Callable[[int, int, str], None]] = None

    def _initialize_components(
        self,
        scanner_config: Optional[Dict[str, Any]],
        parser_config: Optional[Dict[str, Any]],
        importer_config: Optional[Dict[str, Any]]
    ) -> None:
        """
        初始化各个组件

        参数说明：
        - scanner_config: 扫描器配置
        - parser_config: 解析器配置
        - importer_config: 导入器配置

        初始化策略：
        1. 使用默认配置
        2. 应用用户自定义配置
        3. 验证配置有效性
        4. 设置组件间的连接

        为什么分离初始化：
        1. 便于配置管理
        2. 支持运行时重置
        3. 便于单元测试
        4. 清晰的组件边界
        """
        # 初始化文件扫描器
        scanner_config = scanner_config or {}
        self.scanner = FileScanner(
            max_workers=scanner_config.get('max_workers', 4),
            max_depth=scanner_config.get('max_depth', None),
            follow_symlinks=scanner_config.get('follow_symlinks', False),
            timeout=scanner_config.get('timeout', 300.0)
        )

        # 初始化解析器
        parser_config = parser_config or {}
        self.parser = ManifestParser(
            strict_mode=parser_config.get('strict_mode', False),
            validate_attack_ids=parser_config.get('validate_attack_ids', True)
        )

        # 初始化导入器
        importer_config = importer_config or {}
        self.importer = BatchImporter(
            session_factory=self.session_factory,
            batch_size=importer_config.get('batch_size', 1000),
            max_retries=importer_config.get('max_retries', 3),
            retry_delay=importer_config.get('retry_delay', 1.0),
            enable_progress_tracking=importer_config.get('enable_progress_tracking', True)
        )

        # 设置进度回调
        self.importer.set_progress_callback(self._on_import_progress)

    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """
        设置进度回调函数

        参数说明：
        - callback: 回调函数，参数为(current, total, message)

        回调时机：
        1. 文件扫描阶段
        2. 数据解析阶段
        3. 数据库导入阶段

        用途：
        1. 实时进度显示
        2. 用户界面更新
        3. 日志记录
        4. 监控系统集成
        """
        self.progress_callback = callback

    def _on_import_progress(self, current: int, total: int, message: str = "") -> None:
        """
        内部进度回调处理

        参数说明：
        - current: 当前进度
        - total: 总数
        - message: 附加消息

        处理逻辑：
        1. 转发给用户设置的回调
        2. 添加管理器级别的日志
        3. 处理异常情况
        """
        try:
            if self.progress_callback:
                self.progress_callback(current, total, message)
        except Exception as e:
            self.logger.warning(f"进度回调执行失败: {e}")

    async def import_from_directory(
        self,
        directory_path: Union[str, Path],
        pattern: str = "manifest",
        recursive: bool = True
    ) -> ImportProcessResult:
        """
        从目录导入数据的完整流程

        参数说明：
        - directory_path: 源目录路径
        - pattern: 文件匹配模式
        - recursive: 是否递归扫描

        返回值：
        - ImportProcessResult: 完整的处理结果

        处理流程：
        1. 文件扫描：找到所有符合条件的文件
        2. 数据解析：解析manifest.json文件
        3. 数据验证：验证解析结果的质量
        4. 数据导入：批量导入到数据库
        5. 结果统计：生成详细的处理报告

        性能优化：
        1. 并行处理各阶段
        2. 智能资源管理
        3. 内存使用优化
        4. 错误恢复机制

        错误处理：
        1. 阶段性错误隔离
        2. 详细错误信息记录
        3. 支持部分成功处理
        4. 自动重试机制
        """
        start_time = datetime.now()
        result = ImportProcessResult()
        result.start_time = start_time
        result.source_directory = str(directory_path)

        self.logger.info(f"开始从目录导入数据: {directory_path}")

        try:
            # 阶段1: 文件扫描
            self.logger.info("阶段1: 文件扫描")
            result.scan_result = await self._scan_files(directory_path, pattern, recursive)
            result.total_files_found = result.scan_result.get_file_count()

            if result.total_files_found == 0:
                self.logger.warning(f"在目录 {directory_path} 中未找到符合条件的文件")
                result.end_time = datetime.now()
                result.total_time = (result.end_time - start_time).total_seconds()
                return result

            # 报告扫描完成
            self._on_import_progress(0, result.total_files_found, f"扫描完成，找到{result.total_files_found}个文件")

            # 阶段2: 数据解析
            self.logger.info("阶段2: 数据解析")
            result.parse_results = await self._parse_files(result.scan_result.files, result)

            # 阶段3: 数据导入
            if result.successful_parses > 0:
                self.logger.info("阶段3: 数据导入")
                result.import_result = await self._import_data(result.parse_results, result)
            else:
                self.logger.warning("没有成功解析的数据，跳过导入阶段")

            # 完成处理
            result.end_time = datetime.now()
            result.total_time = (result.end_time - start_time).total_seconds()

            # 更新统计信息
            self._update_manager_statistics(result)

            self.logger.info(f"导入流程完成: {result.get_overall_summary()}")

        except Exception as e:
            # 处理整体流程异常
            result.end_time = datetime.now()
            result.total_time = (result.end_time - start_time).total_seconds()

            error_msg = f"导入流程异常: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            # 添加到相应的错误列表
            if result.import_result:
                result.import_result.add_error(error_msg)

        return result

    async def _scan_files(
        self,
        directory_path: Union[str, Path],
        pattern: str,
        recursive: bool
    ) -> ScanResult:
        """
        文件扫描阶段

        参数说明：
        - directory_path: 目录路径
        - pattern: 文件模式
        - recursive: 是否递归

        返回值：
        - ScanResult: 扫描结果

        扫描策略：
        1. 使用FileScanner进行高效扫描
        2. 支持多种文件模式
        3. 处理各种异常情况
        4. 提供详细的扫描统计
        """
        try:
            scan_result = await self.scanner.scan_directory(
                root_path=directory_path,
                pattern=pattern,
                recursive=recursive
            )

            self.logger.info(f"文件扫描完成: {scan_result.get_summary()}")

            # 报告扫描进度
            if scan_result.errors:
                self.logger.warning(f"扫描过程中发现{len(scan_result.errors)}个错误")

            if scan_result.warnings:
                self.logger.info(f"扫描过程中发现{len(scan_result.warnings)}个警告")

            return scan_result

        except Exception as e:
            self.logger.error(f"文件扫描失败: {e}")
            raise DataImportError(
                f"文件扫描失败: {str(e)}",
                record_identifier=str(directory_path),
                original_error=e
            )

    async def _parse_files(
        self,
        file_paths: List[Path],
        result: ImportProcessResult
    ) -> List[ManifestParseResult]:
        """
        数据解析阶段

        参数说明：
        - file_paths: 文件路径列表
        - result: 处理结果对象

        返回值：
        - List[ManifestParseResult]: 解析结果列表

        解析策略：
        1. 并行解析提高性能
        2. 限制并发数避免资源耗尽
        3. 详细的错误处理和日志
        4. 支持断点续传

        性能考虑：
        1. 使用信号量控制并发
        2. 批量处理减少开销
        3. 异步I/O避免阻塞
        4. 内存使用监控
        """
        parse_results = []
        successful_count = 0
        failed_count = 0

        # 控制并发数量
        semaphore = asyncio.Semaphore(10)  # 最多10个并发解析任务

        async def parse_single_file(file_path: Path) -> Optional[ManifestParseResult]:
            """解析单个文件"""
            nonlocal successful_count, failed_count
            async with semaphore:
                try:
                    parse_result = await self.parser.parse_file(file_path)

                    # 更新进度
                    if parse_result.is_valid:
                        successful_count += 1
                    else:
                        failed_count += 1

                    # 报告解析进度
                    current = successful_count + failed_count
                    self._on_import_progress(current, len(file_paths), f"解析中: {file_path.name}")

                    return parse_result

                except Exception as e:
                    failed_count += 1

                    self.logger.error(f"解析文件失败 {file_path}: {e}")
                    return None

        # 创建解析任务
        self.logger.info(f"开始并行解析 {len(file_paths)} 个文件")
        tasks = [parse_single_file(file_path) for file_path in file_paths]

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for item in results:
            if isinstance(item, Exception):
                self.logger.error(f"解析任务异常: {item}")
                failed_count += 1
            elif item is not None:
                parse_results.append(item)

        # 更新统计
        result.successful_parses = successful_count
        result.failed_parses = failed_count

        self.logger.info(f"数据解析完成: 成功{successful_count}个, 失败{failed_count}个")

        return parse_results

    async def _import_data(
        self,
        parse_results: List[ManifestParseResult],
        result: ImportProcessResult
    ) -> ImportResult:
        """
        数据导入阶段

        参数说明：
        - parse_results: 解析结果列表
        - result: 处理结果对象

        返回值：
        - ImportResult: 导入结果

        导入策略：
        1. 使用BatchImporter进行高效导入
        2. 智能批处理和事务管理
        3. 完善的错误处理和重试
        4. 详细的导入统计

        性能优化：
        1. 批量数据库操作
        2. 连接池优化
        3. 事务管理
        4. 内存使用控制
        """
        try:
            # 过滤有效的解析结果
            valid_results = [r for r in parse_results if r.is_valid]

            if not valid_results:
                self.logger.warning("没有有效的解析结果可以导入")
                return ImportResult(total_records=0)

            self.logger.info(f"开始导入 {len(valid_results)} 条有效记录")

            # 报告导入开始
            self._on_import_progress(0, len(valid_results), "开始数据库导入")

            # 执行批量导入
            import_result = await self.importer.import_manifest_data(valid_results)

            self.logger.info(f"数据导入完成: {import_result.get_summary()}")

            return import_result

        except Exception as e:
            self.logger.error(f"数据导入失败: {e}")
            raise DataImportError(
                f"数据导入失败: {str(e)}",
                original_error=e
            )

    def _update_manager_statistics(self, result: ImportProcessResult) -> None:
        """
        更新管理器统计信息

        参数说明：
        - result: 处理结果

        统计内容：
        1. 导入次数
        2. 处理文件总数
        3. 总处理时间
        4. 最后导入时间

        用途：
        1. 性能监控
        2. 使用情况分析
        3. 系统优化依据
        """
        self.stats['total_imports'] += 1
        self.stats['total_files_processed'] += result.total_files_found
        self.stats['total_time'] += result.total_time
        self.stats['last_import_time'] = result.end_time

    async def import_from_file_list(
        self,
        file_paths: List[Union[str, Path]]
    ) -> ImportProcessResult:
        """
        从文件列表导入数据

        参数说明：
        - file_paths: 文件路径列表

        返回值：
        - ImportProcessResult: 处理结果

        使用场景：
        1. 手动指定文件列表
        2. 增量导入
        3. 测试和调试
        4. 重新导入失败的文件

        与import_from_directory的区别：
        1. 跳过扫描阶段
        2. 直接进入解析阶段
        3. 更精确的控制
        4. 适合小批量处理
        """
        start_time = datetime.now()
        result = ImportProcessResult()
        result.start_time = start_time
        result.total_files_found = len(file_paths)

        self.logger.info(f"开始从文件列表导入数据: {len(file_paths)}个文件")

        try:
            # 转换路径格式
            file_paths = [Path(fp) for fp in file_paths]

            # 跳过扫描阶段，直接解析
            result.parse_results = await self._parse_files(file_paths, result)

            # 导入阶段
            if result.successful_parses > 0:
                result.import_result = await self._import_data(result.parse_results, result)

            # 完成处理
            result.end_time = datetime.now()
            result.total_time = (result.end_time - start_time).total_seconds()

            # 更新统计
            self._update_manager_statistics(result)

            self.logger.info(f"文件列表导入完成: {result.get_overall_summary()}")

        except Exception as e:
            self.logger.error(f"文件列表导入失败: {e}")
            result.end_time = datetime.now()
            result.total_time = (result.end_time - start_time).total_seconds()

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取管理器统计信息

        返回值：
        - Dict[str, Any]: 详细统计信息

        统计内容：
        1. 管理器级别统计
        2. 各组件统计
        3. 性能指标
        4. 使用情况
        """
        stats = self.stats.copy()

        # 添加各组件统计
        stats['scanner'] = self.scanner.get_statistics()
        stats['parser'] = self.parser.get_statistics()
        stats['importer'] = self.importer.get_statistics()

        # 计算平均性能指标
        if stats['total_imports'] > 0:
            stats['average_files_per_import'] = stats['total_files_processed'] / stats['total_imports']
            stats['average_time_per_import'] = stats['total_time'] / stats['total_imports']
        else:
            stats['average_files_per_import'] = 0
            stats['average_time_per_import'] = 0

        if stats['total_time'] > 0:
            stats['overall_files_per_second'] = stats['total_files_processed'] / stats['total_time']
        else:
            stats['overall_files_per_second'] = 0

        return stats

    def print_statistics(self) -> None:
        """
        打印统计信息到控制台

        用途：
        1. 性能监控
        2. 调试和开发
        3. 用户反馈
        4. 系统维护
        """
        stats = self.get_statistics()

        print("\n" + "="*70)
        print("数据导入管理器统计信息")
        print("="*70)

        # 管理器统计
        print(f"总导入次数: {stats['total_imports']}")
        print(f"总处理文件数: {stats['total_files_processed']:,}")
        print(f"总处理时间: {stats['total_time']:.2f}s")
        print(f"平均每次导入文件数: {stats['average_files_per_import']:.1f}")
        print(f"平均每次导入时间: {stats['average_time_per_import']:.2f}s")
        print(f"总体处理速度: {stats['overall_files_per_second']:.1f} 文件/秒")

        if stats['last_import_time']:
            print(f"最后导入时间: {stats['last_import_time']}")

        print("-"*70)

        # 组件统计
        scanner_stats = stats['scanner']
        print(f"文件扫描器: {scanner_stats.get('total_files_found', 0)} 个文件, "
              f"平均扫描时间 {scanner_stats.get('average_scan_time', 0):.2f}s")

        parser_stats = stats['parser']
        print(f"解析器: {parser_stats.get('total_files_found', 0)} 个文件, "
              f"成功率 {parser_stats.get('success_rate', 0):.1f}%")

        importer_stats = stats['importer']
        print(f"导入器: {importer_stats.get('total_successful', 0)} 条记录, "
              f"成功率 {importer_stats.get('success_rate', 0):.1f}%")

        print("="*70)

    def reset_statistics(self) -> None:
        """
        重置所有统计信息

        用途：
        1. 开始新的统计周期
        2. 清理累积数据
        3. 测试和调试
        4. 性能基准测试
        """
        self.stats = {
            'total_imports': 0,
            'total_files_processed': 0,
            'total_time': 0.0,
            'last_import_time': None
        }

        # 重置各组件统计
        self.scanner.reset_statistics()
        self.parser.reset_statistics()
        self.importer.reset_statistics()

        self.logger.info("导入管理器统计信息已重置")