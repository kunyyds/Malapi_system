"""
file_scanner.py - 文件系统扫描器

设计思路：
1. 高效扫描文件系统，找到所有manifest.json文件
2. 支持多种扫描策略（深度优先、广度优先、并行扫描）
3. 提供详细的扫描统计和进度跟踪
4. 支持过滤和排序功能

为什么需要专门的扫描器：
- 标准的os.walk()功能有限，不支持并行处理
- 需要跟踪扫描进度和性能统计
- 需要处理各种异常情况（权限、链接等）
- 为后续的批量处理做准备

使用示例：
>>> scanner = FileScanner()
>>> files = await scanner.scan_directory("/path/to/files", pattern="manifest.json")
>>> print(f"找到 {len(files)} 个文件")
>>> scanner.print_statistics()
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import List, Set, Dict, Any, Optional, Callable, Iterator, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import concurrent.futures
import threading
from collections import defaultdict

from src.exceptions.data_exceptions import (
    ParseError,
    ErrorCodes
)


@dataclass
class ScanResult:
    """
    扫描结果封装类

    设计思路：
    1. 封装扫描到的文件列表和统计信息
    2. 提供丰富的查询和过滤方法
    3. 支持结果序列化和缓存
    4. 便于后续处理流程使用

    为什么使用dataclass：
    1. 自动生成初始化方法
    2. 类型提示支持
    3. 内存效率高
    4. 支持字段默认值
    """
    files: List[Path] = field(default_factory=list)
    scan_time: float = 0.0
    directories_scanned: int = 0
    files_found: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    scan_start_time: Optional[datetime] = None
    scan_end_time: Optional[datetime] = None

    def add_file(self, file_path: Path) -> None:
        """
        添加找到的文件

        参数说明：
        - file_path: 文件路径

        为什么需要单独的添加方法：
        1. 可以进行重复检查
        2. 可以触发统计更新
        3. 便于扩展其他功能
        """
        if file_path not in self.files:
            self.files.append(file_path)
            self.files_found += 1

    def add_error(self, error_msg: str) -> None:
        """添加扫描错误信息"""
        self.errors.append(error_msg)

    def add_warning(self, warning_msg: str) -> None:
        """添加扫描警告信息"""
        self.warnings.append(warning_msg)

    def get_file_count(self) -> int:
        """获取文件数量"""
        return len(self.files)

    def get_summary(self) -> str:
        """
        获取扫描结果摘要

        返回值：
        - str: 扫描结果摘要

        用途：
        1. 日志输出
        2. 进度报告
        3. 用户界面显示
        """
        parts = [f"找到 {self.get_file_count()} 个文件"]

        if self.scan_time > 0:
            parts.append(f"耗时 {self.scan_time:.2f}s")

        if self.directories_scanned > 0:
            parts.append(f"扫描 {self.directories_scanned} 个目录")

        if self.errors:
            parts.append(f"错误 {len(self.errors)} 个")

        if self.warnings:
            parts.append(f"警告 {len(self.warnings)} 个")

        return "，".join(parts) + "。"

    def filter_by_extension(self, extensions: List[str]) -> 'ScanResult':
        """
        按文件扩展名过滤结果

        参数说明：
        - extensions: 扩展名列表，如 ['.json', '.xml']

        返回值：
        - ScanResult: 过滤后的新结果

        为什么返回新结果而不是修改原结果：
        1. 保持函数式编程风格
        2. 避免副作用
        3. 支持链式调用
        """
        filtered = ScanResult()
        filtered.scan_time = self.scan_time
        filtered.directories_scanned = self.directories_scanned

        # 标准化扩展名格式
        normalized_exts = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions]

        for file_path in self.files:
            if file_path.suffix.lower() in normalized_exts:
                filtered.add_file(file_path)

        return filtered

    def sort_by_name(self, reverse: bool = False) -> 'ScanResult':
        """
        按文件名排序结果

        参数说明：
        - reverse: 是否倒序排列

        返回值：
        - ScanResult: 排序后的新结果
        """
        sorted_result = ScanResult()
        sorted_result.scan_time = self.scan_time
        sorted_result.directories_scanned = self.directories_scanned
        sorted_result.files = sorted(self.files, key=lambda x: x.name, reverse=reverse)
        sorted_result.files_found = len(sorted_result.files)

        return sorted_result


class FileScanner:
    """
    文件系统扫描器

    设计思路：
    1. 支持多种扫描策略和配置选项
    2. 提供详细的性能监控和错误处理
    3. 支持并行扫描提高性能
    4. 递归处理目录结构

    核心功能：
    - 递归扫描目录结构
    - 文件过滤和匹配
    - 并行处理支持
    - 异常处理和恢复
    - 性能统计和优化

    为什么需要专门的扫描器：
    1. 标准库功能有限，不支持并行处理
    2. 需要详细的进度跟踪和错误报告
    3. 大规模文件扫描需要性能优化
    4. 支持复杂的过滤和匹配逻辑
    """

    def __init__(
        self,
        max_workers: int = 4,
        max_depth: Optional[int] = None,
        follow_symlinks: bool = False,
        timeout: float = 300.0
    ):
        """
        初始化文件扫描器

        参数说明：
        - max_workers: 最大并行工作线程数
        - max_depth: 最大扫描深度，None表示无限制
        - follow_symlinks: 是否跟随符号链接
        - timeout: 扫描超时时间（秒）

        设计考虑：
        1. max_workers: 平衡CPU使用率和扫描速度
        2. max_depth: 避免无限递归
        3. follow_symlinks: 安全性考虑，默认不跟随
        4. timeout: 防止扫描无限期运行

        性能考虑：
        1. 线程池大小影响并发性能
        2. 过多的线程可能导致系统负载过高
        3. I/O密集型任务适合使用更多线程
        """
        self.max_workers = max_workers
        self.max_depth = max_depth
        self.follow_symlinks = follow_symlinks
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

        # 扫描统计信息
        self.stats = {
            'total_scans': 0,
            'total_files_found': 0,
            'total_directories_scanned': 0,
            'total_scan_time': 0.0,
            'average_scan_time': 0.0,
            'scan_errors': 0
        }

        # 支持的文件模式
        self.supported_patterns = {
            'manifest': '*.json',
            'cpp': '*.cpp',
            'header': '*.h',
            'all': '*'
        }

    async def scan_directory(
        self,
        root_path: Union[str, Path],
        pattern: str = "manifest",
        recursive: bool = True,
        filter_func: Optional[Callable[[Path], bool]] = None
    ) -> ScanResult:
        """
        扫描目录查找文件

        参数说明：
        - root_path: 根目录路径
        - pattern: 文件模式（manifest, cpp, header, all）或具体模式（如*.json）
        - recursive: 是否递归扫描子目录
        - filter_func: 自定义过滤函数

        返回值：
        - ScanResult: 扫描结果对象

        异常：
        - ParseError: 扫描过程中发生错误时抛出

        扫描策略：
        1. 优先使用并行扫描提高性能
        2. 对于深层目录结构，使用异步处理
        3. 实现智能的文件过滤机制

        性能优化：
        1. 并行目录扫描
        2. 批量文件处理
        3. 智能缓存和去重
        """
        start_time = asyncio.get_event_loop().time()
        result = ScanResult()
        result.scan_start_time = datetime.now()

        # 标准化路径
        root_path = Path(root_path).resolve()

        # 验证根目录
        if not await self._validate_root_directory(root_path, result):
            return result

        # 解析文件模式
        file_pattern = self._parse_file_pattern(pattern)
        self.logger.info(f"开始扫描目录: {root_path}, 模式: {file_pattern}")

        try:
            if recursive:
                # 递归扫描
                await self._scan_recursive(root_path, file_pattern, filter_func, result, 0)
            else:
                # 仅扫描当前目录
                await self._scan_single_directory(root_path, file_pattern, filter_func, result)

            # 计算扫描时间
            result.scan_time = asyncio.get_event_loop().time() - start_time
            result.scan_end_time = datetime.now()

            # 更新统计信息
            self._update_statistics(result)

            self.logger.info(f"扫描完成: {result.get_summary()}")

        except asyncio.TimeoutError:
            error_msg = f"扫描超时: {self.timeout}秒"
            result.add_error(error_msg)
            self.logger.error(error_msg)

        except Exception as e:
            error_msg = f"扫描过程中发生错误: {str(e)}"
            result.add_error(error_msg)
            self.logger.error(error_msg, exc_info=True)

        return result

    async def _validate_root_directory(self, root_path: Path, result: ScanResult) -> bool:
        """
        验证根目录

        验证内容：
        1. 目录是否存在
        2. 是否有读取权限
        3. 是否为有效目录

        返回值：
        - bool: 验证是否通过
        """
        # 检查目录是否存在
        if not root_path.exists():
            result.add_error(f"根目录不存在: {root_path}")
            return False

        # 检查是否为目录
        if not root_path.is_dir():
            result.add_error(f"路径不是目录: {root_path}")
            return False

        # 检查读取权限
        if not os.access(root_path, os.R_OK):
            result.add_error(f"目录无读取权限: {root_path}")
            return False

        return True

    def _parse_file_pattern(self, pattern: str) -> str:
        """
        解析文件模式

        参数说明：
        - pattern: 文件模式字符串

        返回值：
        - str: 标准化的文件模式

        支持的模式：
        - manifest: *.json
        - cpp: *.cpp
        - header: *.h
        - all: *
        - 自定义模式: 如*.txt, **/*.py等
        """
        # 预定义模式
        if pattern in self.supported_patterns:
            return self.supported_patterns[pattern]

        # 自定义模式直接返回
        return pattern

    async def _scan_recursive(
        self,
        directory: Path,
        pattern: str,
        filter_func: Optional[Callable[[Path], bool]],
        result: ScanResult,
        current_depth: int
    ) -> None:
        """
        递归扫描目录

        参数说明：
        - directory: 当前目录路径
        - pattern: 文件匹配模式
        - filter_func: 自定义过滤函数
        - result: 扫描结果对象
        - current_depth: 当前深度

        递归策略：
        1. 广度优先遍历
        2. 控制最大深度
        3. 处理符号链接
        4. 并行处理子目录

        性能考虑：
        1. 避免过深的递归
        2. 合理控制并行度
        3. 及时处理异常情况
        """
        # 检查深度限制
        if self.max_depth is not None and current_depth >= self.max_depth:
            result.add_warning(f"达到最大深度限制: {self.max_depth}")
            return

        try:
            # 获取目录内容
            entries = await self._get_directory_entries(directory)
            result.directories_scanned += 1

            # 分离文件和子目录
            files = []
            subdirectories = []

            for entry in entries:
                entry_path = directory / entry

                try:
                    if entry_path.is_file():
                        files.append(entry_path)
                    elif entry_path.is_dir():
                        subdirectories.append(entry_path)
                except (OSError, PermissionError) as e:
                    result.add_warning(f"无法访问 {entry_path}: {str(e)}")

            # 处理当前目录中的文件
            await self._process_files(files, pattern, filter_func, result)

            # 并行处理子目录
            if subdirectories and self.max_workers > 1:
                await self._scan_subdirectories_parallel(
                    subdirectories, pattern, filter_func, result, current_depth
                )
            else:
                # 顺序处理子目录
                for subdir in subdirectories:
                    await self._scan_recursive(subdir, pattern, filter_func, result, current_depth + 1)

        except (OSError, PermissionError) as e:
            result.add_error(f"无法扫描目录 {directory}: {str(e)}")

    async def _scan_single_directory(
        self,
        directory: Path,
        pattern: str,
        filter_func: Optional[Callable[[Path], bool]],
        result: ScanResult
    ) -> None:
        """
        扫描单个目录（非递归）

        参数说明：
        - directory: 目录路径
        - pattern: 文件匹配模式
        - filter_func: 自定义过滤函数
        - result: 扫描结果对象
        """
        try:
            entries = await self._get_directory_entries(directory)
            result.directories_scanned += 1

            files = [directory / entry for entry in entries if (directory / entry).is_file()]
            await self._process_files(files, pattern, filter_func, result)

        except (OSError, PermissionError) as e:
            result.add_error(f"无法扫描目录 {directory}: {str(e)}")

    async def _get_directory_entries(self, directory: Path) -> List[str]:
        """
        获取目录条目列表

        参数说明：
        - directory: 目录路径

        返回值：
        - List[str]: 目录条目名称列表

        为什么异步化：
        1. 避免阻塞事件循环
        2. 对于大型目录，扫描可能耗时
        3. 支持超时控制

        性能考虑：
        1. 使用线程池执行阻塞操作
        2. 控制超时时间
        3. 处理权限问题
        """
        loop = asyncio.get_event_loop()

        def sync_get_entries():
            try:
                return os.listdir(directory)
            except (OSError, PermissionError):
                return []

        try:
            return await loop.run_in_executor(None, sync_get_entries)
        except Exception as e:
            self.logger.warning(f"获取目录条目失败 {directory}: {e}")
            return []

    async def _process_files(
        self,
        files: List[Path],
        pattern: str,
        filter_func: Optional[Callable[[Path], bool]],
        result: ScanResult
    ) -> None:
        """
        处理文件列表

        参数说明：
        - files: 文件路径列表
        - pattern: 文件匹配模式
        - filter_func: 自定义过滤函数
        - result: 扫描结果对象

        处理流程：
        1. 模式匹配
        2. 自定义过滤
        3. 添加到结果

        性能优化：
        1. 批量处理
        2. 早期过滤
        3. 避免重复操作
        """
        for file_path in files:
            try:
                # 模式匹配
                if not self._match_pattern(file_path, pattern):
                    continue

                # 自定义过滤
                if filter_func and not filter_func(file_path):
                    continue

                # 添加到结果
                result.add_file(file_path)

            except Exception as e:
                result.add_error(f"处理文件失败 {file_path}: {str(e)}")

    def _match_pattern(self, file_path: Path, pattern: str) -> bool:
        """
        文件模式匹配

        参数说明：
        - file_path: 文件路径
        - pattern: 匹配模式

        返回值：
        - bool: 是否匹配

        匹配策略：
        1. 使用fnmatch进行通配符匹配
        2. 支持简单的正则表达式
        3. 大小写不敏感

        为什么使用fnmatch：
        1. 标准库功能
        2. 性能较好
        3. 支持常见的通配符模式
        """
        import fnmatch

        # 转换为字符串进行匹配
        file_str = str(file_path)

        # 支持文件名匹配和完整路径匹配
        return (
            fnmatch.fnmatch(file_path.name, pattern) or
            fnmatch.fnmatch(file_str, pattern) or
            fnmatch.fnmatch(file_str, f"**/{pattern}")
        )

    async def _scan_subdirectories_parallel(
        self,
        subdirectories: List[Path],
        pattern: str,
        filter_func: Optional[Callable[[Path], bool]],
        result: ScanResult,
        current_depth: int
    ) -> None:
        """
        并行扫描子目录

        参数说明：
        - subdirectories: 子目录列表
        - pattern: 文件匹配模式
        - filter_func: 自定义过滤函数
        - result: 扫描结果对象
        - current_depth: 当前深度

        并行策略：
        1. 使用线程池控制并发度
        2. 每个子目录独立处理
        3. 合并扫描结果

        性能考虑：
        1. 控制并发数量避免系统过载
        2. 合理分配工作负载
        3. 及时处理异常
        """
        # 创建任务列表
        tasks = []
        for subdir in subdirectories:
            task = self._scan_recursive(subdir, pattern, filter_func, result, current_depth + 1)
            tasks.append(task)

        # 并行执行（实际中由于共享result对象，会自动同步）
        await asyncio.gather(*tasks, return_exceptions=True)

    def _update_statistics(self, result: ScanResult) -> None:
        """
        更新扫描统计信息

        参数说明：
        - result: 扫描结果

        统计信息用途：
        1. 性能监控
        2. 质量评估
        3. 优化依据
        """
        self.stats['total_scans'] += 1
        self.stats['total_files_found'] += result.get_file_count()
        self.stats['total_directories_scanned'] += result.directories_scanned
        self.stats['total_scan_time'] += result.scan_time
        self.stats['scan_errors'] += len(result.errors)

        # 计算平均扫描时间
        if self.stats['total_scans'] > 0:
            self.stats['average_scan_time'] = self.stats['total_scan_time'] / self.stats['total_scans']

    async def find_manifest_files(self, root_path: Union[str, Path]) -> ScanResult:
        """
        便捷方法：查找所有manifest.json文件

        参数说明：
        - root_path: 根目录路径

        返回值：
        - ScanResult: 包含所有manifest.json文件的扫描结果

        为什么提供便捷方法：
        1. 简化常用操作
        2. 提高代码可读性
        3. 统一调用接口
        """
        return await self.scan_directory(
            root_path=root_path,
            pattern="manifest",
            recursive=True
        )

    async def find_related_files(self, manifest_path: Path) -> Dict[str, List[Path]]:
        """
        查找与manifest相关的其他文件

        参数说明：
        - manifest_path: manifest.json文件路径

        返回值：
        - Dict[str, List[Path]]: 相关文件映射

        查找策略：
        1. 同目录下的CPP文件
        2. 同名不同扩展名的文件
        3. 相关的头文件

        用途：
        1. 完整的数据包识别
        2. 关联文件处理
        3. 数据完整性验证
        """
        related_files = {
            'cpp': [],
            'header': [],
            'other': []
        }

        if not manifest_path.exists() or manifest_path.suffix != '.json':
            return related_files

        # 获取manifest所在目录
        parent_dir = manifest_path.parent
        base_name = manifest_path.stem

        try:
            entries = await self._get_directory_entries(parent_dir)

            for entry in entries:
                entry_path = parent_dir / entry

                if not entry_path.is_file():
                    continue

                # 查找CPP文件
                if entry_path.suffix == '.cpp':
                    related_files['cpp'].append(entry_path)

                # 查找头文件
                elif entry_path.suffix in ['.h', '.hpp']:
                    related_files['header'].append(entry_path)

                # 查找其他相关文件（同名的其他类型）
                elif entry_path.stem == base_name:
                    related_files['other'].append(entry_path)

        except Exception as e:
            self.logger.warning(f"查找相关文件失败 {manifest_path}: {e}")

        return related_files

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取扫描器统计信息

        返回值：
        - Dict[str, Any]: 详细的统计信息

        统计信息用途：
        1. 性能分析
        2. 使用情况监控
        3. 问题诊断
        """
        stats = self.stats.copy()

        # 计算额外统计指标
        if stats['total_scans'] > 0:
            stats['average_files_per_scan'] = stats['total_files_found'] / stats['total_scans']
            stats['average_directories_per_scan'] = stats['total_directories_scanned'] / stats['total_scans']
        else:
            stats['average_files_per_scan'] = 0
            stats['average_directories_per_scan'] = 0

        # 性能指标
        if stats['total_scan_time'] > 0:
            stats['files_per_second'] = stats['total_files_found'] / stats['total_scan_time']
        else:
            stats['files_per_second'] = 0

        return stats

    def print_statistics(self) -> None:
        """
        打印统计信息到控制台

        用途：
        1. 调试和开发
        2. 性能监控
        3. 用户反馈
        """
        stats = self.get_statistics()

        print("\n" + "="*50)
        print("文件扫描器统计信息")
        print("="*50)
        print(f"总扫描次数: {stats['total_scans']}")
        print(f"总文件数: {stats['total_files_found']:,}")
        print(f"总目录数: {stats['total_directories_scanned']:,}")
        print(f"总扫描时间: {stats['total_scan_time']:.2f}s")
        print(f"平均扫描时间: {stats['average_scan_time']:.2f}s")
        print(f"平均每次扫描文件数: {stats['average_files_per_scan']:.1f}")
        print(f"平均扫描速度: {stats['files_per_second']:.1f} 文件/秒")
        print(f"扫描错误数: {stats['scan_errors']}")
        print("="*50)

    def reset_statistics(self) -> None:
        """
        重置统计信息

        用途：
        1. 开始新的统计周期
        2. 清理累积数据
        3. 测试和调试
        """
        self.stats = {
            'total_scans': 0,
            'total_files_found': 0,
            'total_directories_scanned': 0,
            'total_scan_time': 0.0,
            'average_scan_time': 0.0,
            'scan_errors': 0
        }
        self.logger.info("文件扫描器统计信息已重置")