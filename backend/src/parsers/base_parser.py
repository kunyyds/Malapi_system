"""
解析器基类模块
设计思路：
1. 定义所有解析器的通用接口和行为规范
2. 提供可复用的基础功能和工具方法
3. 实现统一的错误处理和日志记录
4. 支持插件化的解析器扩展机制

为什么需要基类：
1. 确保所有解析器有一致的行为模式
2. 避免重复代码，提高开发效率
3. 便于添加新的解析器类型
4. 统一测试和验证接口

基类职责：
- 定义解析器标准接口
- 提供通用工具方法
- 处理文件I/O操作
- 统一错误处理机制
- 管理解析状态和统计
- 支持配置和选项

使用示例：
>>> class MyParser(BaseParser):
...     async def parse(self, file_path: str) -> Any:
...         await self._validate_file(file_path)
...         data = await self._read_file(file_path)
...         return await self._process_data(data)
"""

import abc
import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
from datetime import datetime
from dataclasses import dataclass, field

from src.exceptions.data_exceptions import (
    DataProcessingError,
    ParseError,
    ValidationError,
    ErrorCodes
)


T = TypeVar('T')


@dataclass
class ParseStatistics:
    """
    解析统计信息类

    设计思路：
    1. 统计解析过程中的各种指标
    2. 提供详细的性能和错误信息
    3. 支持统计信息的序列化和持久化
    4. 便于监控和优化解析性能

    为什么使用dataclass：
    1. 自动生成__init__、__repr__等方法
    2. 类型提示支持
    3. 比手动定义类更简洁
    4. 支持字段默认值
    """
    total_files: int = 0
    successful_parses: int = 0
    failed_parses: int = 0
    total_records: int = 0
    processed_records: int = 0
    parse_time: float = 0.0
    error_count: int = 0
    warning_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """计算解析成功率"""
        if self.total_files == 0:
            return 0.0
        return (self.successful_parses / self.total_files) * 100

    @property
    def records_per_second(self) -> float:
        """计算每秒处理的记录数"""
        if self.parse_time == 0.0:
            return 0.0
        return self.processed_records / self.parse_time

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "total_files": self.total_files,
            "successful_parses": self.successful_parses,
            "failed_parses": self.failed_parses,
            "total_records": self.total_records,
            "processed_records": self.processed_records,
            "parse_time": self.parse_time,
            "success_rate": self.success_rate,
            "records_per_second": self.records_per_second,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


@dataclass
class ParserConfig:
    """
    解析器配置类

    设计思路：
    1. 集中管理解析器的配置选项
    2. 支持不同类型的配置源（文件、环境变量、参数）
    3. 提供配置验证和默认值
    4. 支持配置的动态更新

    配置说明：
    - strict_mode: 严格模式，任何错误都导致解析失败
    - max_file_size: 最大文件大小限制，防止内存溢出
    - timeout: 解析超时时间，防止无限等待
    - encoding: 文件编码，统一处理文件编码问题
    - validate_after_parse: 解析后是否进行验证
    """
    strict_mode: bool = False
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    timeout: int = 300  # 5分钟
    encoding: str = "utf-8"
    validate_after_parse: bool = True
    log_level: str = "INFO"
    max_concurrent_tasks: int = 10
    retry_attempts: int = 3
    retry_delay: float = 1.0


class BaseParser(Generic[T], abc.ABC):
    """
    解析器基类

    设计思路：
    1. 定义所有解析器必须实现的核心接口
    2. 提供通用功能和默认实现
    3. 统一错误处理和日志记录
    4. 支持异步操作和并发处理
    5. 提供可配置的解析选项

    核心接口：
    - parse(): 解析文件或数据的主要方法
    - parse_batch(): 批量解析方法
    - validate(): 数据验证方法
    - get_statistics(): 获取统计信息

    扩展点：
    - _parse_content(): 解析具体内容的核心逻辑
    - _validate_parsed_data(): 验证解析后的数据
    - _process_parsed_data(): 处理解析后的数据
    """

    def __init__(self, config: Optional[ParserConfig] = None):
        """
        初始化解析器

        参数说明：
        - config: 解析器配置对象，为None时使用默认配置

        初始化步骤：
        1. 设置配置对象
        2. 初始化日志记录器
        3. 初始化统计信息
        4. 验证配置有效性
        """
        self.config = config or ParserConfig()
        self.logger = self._setup_logger()
        self.statistics = ParseStatistics()

        # 验证配置
        self._validate_config()

        self.logger.info(f"初始化解析器: {self.__class__.__name__}")
        self.logger.debug(f"解析器配置: {self.config}")

    def _setup_logger(self) -> logging.Logger:
        """
        设置日志记录器

        设计思路：
        1. 使用解析器类名作为日志器名称
        2. 根据配置设置日志级别
        3. 保持与项目日志系统的一致性

        返回值：
        - logging.Logger: 配置好的日志记录器
        """
        logger = logging.getLogger(self.__class__.__module__ + "." + self.__class__.__name__)

        # 设置日志级别
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logger.setLevel(log_level)

        return logger

    def _validate_config(self) -> None:
        """
        验证配置对象

        验证规则：
        1. 检查必需的配置项
        2. 验证配置值的有效性
        3. 检查配置之间的兼容性
        4. 记录配置警告信息

        异常：
        - ValidationError: 配置验证失败时抛出
        """
        if self.config.max_file_size <= 0:
            raise ValidationError(
                "max_file_size必须大于0",
                field_name="max_file_size",
                field_value=self.config.max_file_size,
                validation_rule="max_file_size > 0"
            )

        if self.config.timeout <= 0:
            raise ValidationError(
                "timeout必须大于0",
                field_name="timeout",
                field_value=self.config.timeout,
                validation_rule="timeout > 0"
            )

        if self.config.max_concurrent_tasks <= 0:
            raise ValidationError(
                "max_concurrent_tasks必须大于0",
                field_name="max_concurrent_tasks",
                field_value=self.config.max_concurrent_tasks,
                validation_rule="max_concurrent_tasks > 0"
            )

    async def parse_file(self, file_path: Union[str, Path]) -> Optional[T]:
        """
        解析单个文件

        设计思路：
        1. 统一的文件解析流程
        2. 完整的错误处理和重试机制
        3. 详细的日志记录
        4. 性能监控和统计

        参数说明：
        - file_path: 要解析的文件路径

        返回值：
        - Optional[T]: 解析后的数据对象，解析失败时返回None

        异常：
        - ParseError: 解析过程中发生错误时抛出
        - ValidationError: 数据验证失败时抛出

        处理流程：
        1. 文件存在性和可读性检查
        2. 文件大小和格式预检查
        3. 读取文件内容
        4. 调用具体解析逻辑
        5. 验证解析结果
        6. 更新统计信息
        """
        self.statistics.total_files += 1
        self.statistics.start_time = datetime.now()

        # 标准化文件路径
        file_path = Path(file_path)

        try:
            self.logger.info(f"开始解析文件: {file_path}")

            # 步骤1: 文件预检查
            await self._pre_validate_file(file_path)

            # 步骤2: 读取文件内容
            content = await self._read_file(file_path)

            # 步骤3: 解析文件内容
            start_time = asyncio.get_event_loop().time()
            parsed_data = await self._parse_content(content, file_path)
            parse_time = asyncio.get_event_loop().time() - start_time

            # 步骤4: 验证解析结果
            if self.config.validate_after_parse:
                await self._validate_parsed_data(parsed_data, file_path)

            # 步骤5: 处理解析结果
            processed_data = await self._process_parsed_data(parsed_data, file_path)

            # 更新统计信息
            self.statistics.successful_parses += 1
            self.statistics.parse_time += parse_time
            if hasattr(processed_data, '__len__'):
                self.statistics.processed_records += len(processed_data)

            self.logger.info(f"成功解析文件: {file_path}, 耗时: {parse_time:.2f}s")

            return processed_data

        except (ParseError, ValidationError) as e:
            self.statistics.failed_parses += 1
            self.statistics.error_count += 1
            self.logger.error(f"解析文件失败: {file_path} - {e}")

            if self.config.strict_mode:
                raise

            return None

        except Exception as e:
            self.statistics.failed_parses += 1
            self.statistics.error_count += 1
            error_msg = f"解析文件时发生未知错误: {file_path} - {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            if self.config.strict_mode:
                raise ParseError(
                    error_msg,
                    file_path=str(file_path),
                    original_error=e
                )

            return None

        finally:
            self.statistics.end_time = datetime.now()

    async def parse_file_with_retry(self, file_path: Union[str, Path]) -> Optional[T]:
        """
        带重试机制的文件解析

        设计思路：
        1. 实现自动重试机制，处理临时性错误
        2. 指数退避重试策略，避免过度重试
        3. 支持自定义重试逻辑
        4. 记录重试过程的详细日志

        参数说明：
        - file_path: 要解析的文件路径

        返回值：
        - Optional[T]: 解析后的数据对象

        重试策略：
        - 默认重试3次，每次延迟1秒
        - 指数退避：第n次重试延迟2^n秒
        - 只对特定异常类型进行重试
        """
        last_exception = None

        for attempt in range(self.config.retry_attempts + 1):
            try:
                return await self.parse_file(file_path)

            except (FileNotFoundError, PermissionError) as e:
                # 这些错误通常不会通过重试解决，直接抛出
                raise

            except Exception as e:
                last_exception = e
                if attempt < self.config.retry_attempts:
                    delay = self.config.retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"解析文件失败，{delay}秒后重试 (第{attempt + 1}次): {file_path} - {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"解析文件重试失败: {file_path}")
                    break

        # 抛出最后一次异常
        if last_exception:
            raise ParseError(
                f"解析文件重试失败: {file_path}",
                file_path=str(file_path),
                original_error=last_exception
            )

    async def parse_files(
        self,
        file_paths: List[Union[str, Path]]
    ) -> List[T]:
        """
        批量解析多个文件

        设计思路：
        1. 支持并发处理，提高解析效率
        2. 控制并发数量，避免资源耗尽
        3. 提供进度跟踪和错误隔离
        4. 支持取消操作和优雅中断

        参数说明：
        - file_paths: 要解析的文件路径列表

        返回值：
        - List[T]: 成功解析的数据对象列表

        并发控制：
        - 使用信号量限制并发数量
        - 支持可配置的最大并发数
        - 自动管理任务生命周期
        """
        self.logger.info(f"开始批量解析 {len(file_paths)} 个文件")

        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)

        async def parse_single_file(file_path: Union[str, Path]) -> Optional[T]:
            async with semaphore:
                return await self.parse_file(file_path)

        # 创建并发任务
        tasks = [
            parse_single_file(file_path)
            for file_path in file_paths
        ]

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果和异常
        successful_results = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"批量解析中发生异常: {result}")
                if self.config.strict_mode:
                    raise
            elif result is not None:
                successful_results.append(result)

        self.logger.info(f"批量解析完成，成功解析 {len(successful_results)} 个文件")
        return successful_results

    async def parse_content(
        self,
        content: str,
        source: Optional[Union[str, Path]] = None
    ) -> Optional[T]:
        """
        解析字符串内容

        设计思路：
        1. 直接解析内容，跳过文件I/O操作
        2. 用于测试或内存中的内容解析
        3. 保持与文件解析的一致性
        4. 支持来源标识用于日志记录

        参数说明：
        - content: 要解析的字符串内容
        - source: 内容来源标识，用于日志记录

        返回值：
        - Optional[T]: 解析后的数据对象
        """
        try:
            self.logger.debug(f"开始解析内容，来源: {source or '内存'}")

            # 解析内容
            parsed_data = await self._parse_content(content, source)

            # 验证结果
            if self.config.validate_after_parse:
                await self._validate_parsed_data(parsed_data, source)

            # 处理结果
            processed_data = await self._process_parsed_data(parsed_data, source)

            self.logger.debug(f"成功解析内容，来源: {source or '内存'}")
            return processed_data

        except Exception as e:
            self.logger.error(f"解析内容失败，来源: {source or '内存'} - {e}")

            if self.config.strict_mode:
                raise ParseError(
                    f"解析内容失败: {source or '内存'}",
                    original_error=e
                )

            return None

    async def _pre_validate_file(self, file_path: Path) -> None:
        """
        预验证文件

        验证规则：
        1. 检查文件是否存在
        2. 检查文件是否可读
        3. 检查文件大小是否在限制范围内
        4. 检查文件扩展名（如果需要）

        异常：
        - ParseError: 文件预验证失败时抛出
        """
        # 检查文件是否存在
        if not file_path.exists():
            raise ParseError(
                f"文件不存在: {file_path}",
                file_path=str(file_path),
                suggestion="请检查文件路径是否正确"
            )

        # 检查文件是否可读
        if not os.access(file_path, os.R_OK):
            raise ParseError(
                f"文件不可读: {file_path}",
                file_path=str(file_path),
                suggestion="请检查文件权限"
            )

        # 检查文件大小
        file_size = file_path.stat().st_size
        if file_size > self.config.max_file_size:
            raise ParseError(
                f"文件过大: {file_size} bytes (限制: {self.config.max_file_size} bytes)",
                file_path=str(file_path),
                suggestion="考虑分片处理大文件或增加大小限制"
            )

    async def _read_file(self, file_path: Path) -> str:
        """
        读取文件内容

        设计思路：
        1. 使用异步I/O避免阻塞
        2. 支持多种文件编码
        3. 处理读取超时
        4. 统一的错误处理

        参数说明：
        - file_path: 要读取的文件路径

        返回值：
        - str: 文件内容字符串

        异常：
        - ParseError: 文件读取失败时抛出
        """
        try:
            async with asyncio.wait_for(
                aiofiles.open(file_path, 'r', encoding=self.config.encoding),
                timeout=self.config.timeout
            ) as file:
                content = await file.read()
                return content

        except asyncio.TimeoutError:
            raise ParseError(
                f"读取文件超时: {file_path}",
                file_path=str(file_path),
                suggestion=f"检查文件大小或增加超时时间 (当前: {self.config.timeout}s)"
            )
        except UnicodeDecodeError as e:
            raise ParseError(
                f"文件编码错误: {file_path}",
                file_path=str(file_path),
                suggestion=f"尝试使用其他编码 (当前: {self.config.encoding})",
                original_error=e
            )
        except OSError as e:
            raise ParseError(
                f"读取文件失败: {file_path} - {str(e)}",
                file_path=str(file_path),
                original_error=e
            )

    @abc.abstractmethod
    async def _parse_content(self, content: str, source: Optional[Union[str, Path]] = None) -> T:
        """
        解析文件内容的核心逻辑 (抽象方法)

        设计思路：
        1. 子类必须实现的具体解析逻辑
        2. 将字符串内容转换为结构化数据
        3. 处理解析过程中的异常
        4. 返回解析后的数据对象

        参数说明：
        - content: 文件内容字符串
        - source: 文件来源信息，用于日志记录

        返回值：
        - T: 解析后的数据对象

        注意事项：
        - 这个方法是抽象的，子类必须实现
        - 可以抛出特定类型的解析异常
        - 异常会被基类统一处理
        """
        pass

    async def _validate_parsed_data(self, data: T, source: Optional[Union[str, Path]] = None) -> None:
        """
        验证解析后的数据 (可重写)

        设计思路：
        1. 提供默认的验证逻辑
        2. 子类可以重写以实现特定验证
        3. 验证数据结构和业务规则
        4. 统一的验证错误处理

        参数说明：
        - data: 解析后的数据对象
        - source: 数据来源信息

        默认实现：
        - 基本的数据结构验证
        - 必需字段检查
        """
        # 默认实现：检查数据不为空
        if data is None:
            raise ValidationError(
                "解析结果为空",
                source=str(source),
                validation_rule="解析结果不能为None"
            )

    async def _process_parsed_data(self, data: T, source: Optional[Union[str, Path]] = None) -> T:
        """
        处理解析后的数据 (可重写)

        设计思路：
        1. 提供默认的数据后处理逻辑
        2. 子类可以重写以实现特定处理
        3. 数据清洗和标准化
        4. 附加额外的元数据

        参数说明：
        - data: 解析后的数据对象
        - source: 数据来源信息

        返回值：
        - T: 处理后的数据对象

        默认实现：
        - 直接返回原数据，不做处理
        """
        return data

    def get_statistics(self) -> ParseStatistics:
        """
        获取解析统计信息

        返回值：
        - ParseStatistics: 包含详细统计信息的对象
        """
        return self.statistics

    def reset_statistics(self) -> None:
        """
        重置统计信息

        设计思路：
        1. 清零所有统计数据
        2. 重置时间戳
        3. 用于新的解析周期
        """
        self.statistics = ParseStatistics()
        self.logger.info("解析统计信息已重置")

    def get_supported_extensions(self) -> List[str]:
        """
        获取支持的文件扩展名列表 (可重写)

        返回值：
        - List[str]: 支持的文件扩展名列表

        默认实现：
        - 返回空列表，表示支持所有文件类型
        """
        return []

    def supports_file(self, file_path: Union[str, Path]) -> bool:
        """
        检查是否支持解析指定文件 (可重写)

        设计思路：
        1. 检查文件扩展名是否在支持列表中
        2. 支持子类自定义判断逻辑
        3. 用于文件过滤和路由

        参数说明：
        - file_path: 文件路径

        返回值：
        - bool: 是否支持解析该文件

        默认实现：
        - 如果支持列表为空，支持所有文件
        - 否则检查扩展名
        """
        if not self.get_supported_extensions():
            return True

        file_ext = Path(file_path).suffix.lower()
        return file_ext in [ext.lower() for ext in self.get_supported_extensions()]

    async def validate_file(self, file_path: Union[str, Path]) -> bool:
        """
        验证文件是否可以被解析

        设计思路：
        1. 检查文件是否存在和可读
        2. 验证文件格式是否支持
        3. 检查文件大小限制
        4. 返回验证结果而不抛出异常

        参数说明：
        - file_path: 文件路径

        返回值：
        - bool: 文件是否有效
        """
        try:
            await self._pre_validate_file(Path(file_path))
            return self.supports_file(file_path)
        except Exception as e:
            self.logger.warning(f"文件验证失败: {file_path} - {e}")
            return False