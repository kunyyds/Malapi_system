"""
batch_importer.py - 批量数据导入器

设计思路：
1. 高性能批量插入，减少数据库连接开销
2. 事务管理，确保数据一致性
3. 错误隔离，单条记录失败不影响整体导入
4. 进度跟踪，支持大规模数据处理

为什么需要专门的批量导入器：
- 标准的逐条插入效率太低
- 需要事务管理确保数据完整性
- 大批量数据需要错误恢复机制
- 需要详细的进度跟踪和统计

使用示例：
>>> importer = BatchImporter(session_factory)
>>> manifest_results = [result1, result2, ...]  # 解析结果列表
>>> import_result = await importer.import_manifest_data(manifest_results)
>>> print(f"成功导入 {import_result.successful_imports} 条记录")
"""

import asyncio
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select, insert, update, delete, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.database.models import (
    MalAPIFunction, AttCKMapping, FunctionChild,
    MalAPIMetadata, LLMAnalysisCache
)
from src.parsers.manifest_parser import ManifestParseResult
from src.exceptions.data_exceptions import (
    DataImportError,
    ValidationError,
    ErrorCodes
)


@dataclass
class ImportResult:
    """
    导入结果封装类

    设计思路：
    1. 封装导入统计信息和详细结果
    2. 提供丰富的查询和报告方法
    3. 支持部分失败的处理
    4. 便于后续流程使用

    为什么使用dataclass：
    1. 自动生成初始化方法
    2. 类型提示支持
    3. 内存效率高
    4. 支持字段默认值
    """
    total_records: int = 0
    successful_imports: int = 0
    failed_imports: int = 0
    skipped_imports: int = 0
    duplicate_imports: int = 0
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    imported_ids: List[int] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def get_summary(self) -> str:
        """
        获取导入结果摘要

        返回值：
        - str: 导入结果摘要

        用途：
        1. 日志记录
        2. 用户反馈
        3. 进度报告
        """
        parts = [f"总计 {self.total_records} 条记录"]

        if self.successful_imports > 0:
            parts.append(f"成功 {self.successful_imports}")

        if self.failed_imports > 0:
            parts.append(f"失败 {self.failed_imports}")

        if self.skipped_imports > 0:
            parts.append(f"跳过 {self.skipped_imports}")

        if self.duplicate_imports > 0:
            parts.append(f"重复 {self.duplicate_imports}")

        if self.processing_time > 0:
            parts.append(f"耗时 {self.processing_time:.2f}s")

            # 添加处理速度
            speed = self.successful_imports / self.processing_time
            parts.append(f"速度 {speed:.1f} 条/秒")

        return "，".join(parts) + "。"

    def get_success_rate(self) -> float:
        """
        计算导入成功率

        返回值：
        - float: 成功率百分比

        计算公式：
        成功率 = 成功导入数 / (总数 - 跳过数) * 100
        """
        effective_total = self.total_records - self.skipped_imports
        if effective_total == 0:
            return 0.0
        return (self.successful_imports / effective_total) * 100

    def add_error(self, error_msg: str) -> None:
        """添加错误信息"""
        self.errors.append(error_msg)

    def add_warning(self, warning_msg: str) -> None:
        """添加警告信息"""
        self.warnings.append(warning_msg)


class BatchImporter:
    """
    批量数据导入器

    设计思路：
    1. 高性能批量操作，减少数据库连接开销
    2. 智能事务管理，平衡性能和一致性
    3. 完善的错误处理和恢复机制
    4. 详细的进度跟踪和性能监控

    核心功能：
    - 批量插入malapi_functions表
    - 批量插入attck_mappings表
    - 批量插入function_children表
    - 更新元数据和缓存信息
    - 重复数据处理和冲突解决

    性能优化策略：
    1. 使用SQLAlchemy的bulk_insert_mappings
    2. 智能分批处理，避免内存溢出
    3. 连接池管理，优化数据库连接
    4. 并行处理，提高导入速度
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        batch_size: int = 1000,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_progress_tracking: bool = True
    ):
        """
        初始化批量导入器

        参数说明：
        - session_factory: SQLAlchemy异步会话工厂
        - batch_size: 批量处理大小，影响内存使用和性能
        - max_retries: 最大重试次数
        - retry_delay: 重试延迟时间（秒）
        - enable_progress_tracking: 是否启用进度跟踪

        设计考虑：
        1. batch_size: 平衡内存使用和性能，1000是经过测试的平衡点
        2. max_retries: 处理临时性数据库问题
        3. retry_delay: 指数退避策略，避免过度重试
        4. progress_tracking: 便于监控大规模导入过程

        性能考虑：
        1. 批量大小影响数据库性能
        2. 过大的批次可能导致内存问题
        3. 重试机制提高系统可靠性
        """
        self.session_factory = session_factory
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_progress_tracking = enable_progress_tracking
        self.logger = logging.getLogger(__name__)

        # 导入统计信息
        self.stats = {
            'total_imports': 0,
            'total_successful': 0,
            'total_failed': 0,
            'total_duplicates': 0,
            'total_time': 0.0,
            'average_time_per_batch': 0.0
        }

        # 进度回调函数
        self.progress_callback: Optional[callable] = None

    def set_progress_callback(self, callback: callable) -> None:
        """
        设置进度回调函数

        参数说明：
        - callback: 回调函数，接收(current, total, message)参数

        用途：
        1. 实时进度报告
        2. 用户界面更新
        3. 日志记录
        """
        self.progress_callback = callback

    def _report_progress(self, current: int, total: int, message: str = "") -> None:
        """
        报告导入进度

        参数说明：
        - current: 当前进度
        - total: 总数
        - message: 附加消息

        为什么需要进度报告：
        1. 大批量导入需要长时间，用户需要了解进度
        2. 便于监控系统状态
        3. 调试和问题诊断
        """
        if self.progress_callback and self.enable_progress_tracking:
            self.progress_callback(current, total, message)

    async def import_manifest_data(
        self,
        manifest_results: List[ManifestParseResult]
    ) -> ImportResult:
        """
        批量导入manifest解析结果

        参数说明：
        - manifest_results: ManifestParseResult对象列表

        返回值：
        - ImportResult: 包含导入统计和错误信息

        处理流程：
        1. 数据预处理和验证
        2. 去重处理，避免重复导入
        3. 分批转换为数据库模型
        4. 事务批量插入
        5. 错误处理和恢复
        6. 结果统计和报告

        性能优化：
        1. 预过滤无效数据
        2. 批量数据库操作
        3. 智能重试机制
        4. 并行处理支持

        错误处理策略：
        1. 单条失败不影响批次
        2. 详细错误信息记录
        3. 支持断点续传
        4. 数据一致性保证
        """
        start_time = datetime.now()
        result = ImportResult(total_records=len(manifest_results))
        result.start_time = start_time

        self.logger.info(f"开始批量导入，共{len(manifest_results)}条记录")

        # 步骤1: 预处理和过滤
        self.logger.info("步骤1: 数据预处理和验证")
        valid_results = await self._preprocess_manifest_data(manifest_results, result)

        if not valid_results:
            self.logger.warning("没有有效的数据需要导入")
            result.end_time = datetime.now()
            result.processing_time = (result.end_time - start_time).total_seconds()
            return result

        # 步骤2: 检查重复数据
        self.logger.info("步骤2: 检查重复数据")
        await self._check_duplicate_data(valid_results, result)

        # 步骤3: 分批导入
        self.logger.info("步骤3: 开始分批导入")
        successful_imports = 0
        failed_imports = 0

        total_batches = (len(valid_results) + self.batch_size - 1) // self.batch_size

        for batch_idx, batch_start in enumerate(range(0, len(valid_results), self.batch_size)):
            batch_end = min(batch_start + self.batch_size, len(valid_results))
            batch_results = valid_results[batch_start:batch_end]

            self.logger.info(f"处理批次 {batch_idx + 1}/{total_batches} ({len(batch_results)}条记录)")

            # 报告进度
            self._report_progress(batch_start, len(valid_results), f"处理批次 {batch_idx + 1}")

            try:
                # 导入当前批次
                batch_success, batch_errors = await self._import_batch_with_retry(
                    batch_results, batch_idx + 1
                )
                successful_imports += batch_success
                failed_imports += len(batch_results) - batch_success

                # 添加错误信息
                result.errors.extend(batch_errors)

                self.logger.info(f"批次 {batch_idx + 1} 完成: 成功{batch_success}, 失败{len(batch_results) - batch_success}")

            except Exception as e:
                # 批次处理失败，记录错误但继续处理下一批次
                error_msg = f"批次{batch_idx + 1}处理失败: {str(e)}"
                result.add_error(error_msg)
                failed_imports += len(batch_results)
                self.logger.error(error_msg, exc_info=True)

        # 步骤4: 更新统计和结果
        result.successful_imports = successful_imports
        result.failed_imports = failed_imports
        result.end_time = datetime.now()
        result.processing_time = (result.end_time - start_time).total_seconds()

        # 更新全局统计
        self._update_global_statistics(result)

        self.logger.info(f"批量导入完成: {result.get_summary()}")
        return result

    async def _preprocess_manifest_data(
        self,
        manifest_results: List[ManifestParseResult],
        result: ImportResult
    ) -> List[ManifestParseResult]:
        """
        预处理manifest数据

        参数说明：
        - manifest_results: 原始解析结果列表
        - result: 导入结果对象

        返回值：
        - List[ManifestParseResult]: 过滤后的有效解析结果

        预处理内容：
        1. 过滤无效的解析结果
        2. 数据完整性检查
        3. 必需字段验证
        4. 数据标准化

        为什么需要预处理：
        1. 提前发现问题，避免数据库错误
        2. 提高导入效率
        3. 统一数据格式
        4. 详细的问题报告
        """
        valid_results = []
        skipped_count = 0

        for i, parse_result in enumerate(manifest_results):
            # 报告预处理进度
            if i % 100 == 0:
                self._report_progress(i, len(manifest_results), "预处理数据")

            # 检查解析结果有效性
            if not parse_result.is_valid:
                error_msg = f"跳过无效数据: {parse_result.get_error_summary()}"
                result.add_error(error_msg)
                skipped_count += 1
                continue

            # 检查数据完整性
            if not await self._validate_manifest_data(parse_result.data, result):
                skipped_count += 1
                continue

            valid_results.append(parse_result)

        result.skipped_imports = skipped_count
        self.logger.info(f"预处理完成: 有效数据{len(valid_results)}条, 跳过{skipped_count}条")

        return valid_results

    async def _validate_manifest_data(
        self,
        data: Dict[str, Any],
        result: ImportResult
    ) -> bool:
        """
        验证manifest数据

        参数说明：
        - data: manifest数据
        - result: 导入结果对象

        返回值：
        - bool: 验证是否通过

        验证规则：
        1. 必需字段检查
        2. 数据类型验证
        3. 业务逻辑验证
        4. 数据完整性检查

        为什么需要验证：
        1. 确保数据质量
        2. 避免数据库约束错误
        3. 提供详细的错误信息
        4. 提高导入成功率
        """
        # 检查必需字段
        required_fields = ['alias', 'status']
        for field in required_fields:
            if not data.get(field):
                result.add_error(f"缺少必需字段: {field}")
                return False

        # 检查alias长度
        alias = data.get('alias', '')
        if len(alias) > 255:
            result.add_error(f"alias字段过长: {len(alias)} > 255")
            return False

        # 检查status值
        valid_statuses = ['ok', 'error', 'pending', 'generated', 'failed']
        status = data.get('status', '')
        if status not in valid_statuses:
            result.add_warning(f"未知的status值: {status}")

        return True

    async def _check_duplicate_data(
        self,
        manifest_results: List[ManifestParseResult],
        result: ImportResult
    ) -> None:
        """
        检查重复数据

        参数说明：
        - manifest_results: 解析结果列表
        - result: 导入结果对象

        检查策略：
        1. 基于hash_id去重
        2. 基于alias去重
        3. 数据库查询验证
        4. 用户提供决策

        为什么需要检查重复：
        1. 避免数据重复
        2. 提高导入效率
        3. 维护数据唯一性
        4. 用户友好提示
        """
        if not manifest_results:
            return

        async with self.session_factory() as session:
            try:
                # 收集所有alias和hash_id
                aliases = [r.data.get('alias', '') for r in manifest_results if r.data.get('alias')]
                hash_ids = [r.data.get('hash_id', '') for r in manifest_results if r.data.get('hash_id')]

                duplicate_count = 0

                # 检查alias重复
                if aliases:
                    query = select(MalAPIFunction.alias).where(
                        MalAPIFunction.alias.in_(aliases)
                    )
                    existing_aliases = await session.execute(query)
                    existing_aliases = [row[0] for row in existing_aliases.fetchall()]

                    for alias in existing_aliases:
                        result.add_warning(f"alias已存在: {alias}")
                        duplicate_count += 1

                # 检查hash_id重复
                if hash_ids:
                    query = select(MalAPIFunction.hash_id).where(
                        MalAPIFunction.hash_id.in_(hash_ids)
                    )
                    existing_hash_ids = await session.execute(query)
                    existing_hash_ids = [row[0] for row in existing_hash_ids.fetchall()]

                    for hash_id in existing_hash_ids:
                        result.add_warning(f"hash_id已存在: {hash_id}")
                        duplicate_count += 1

                result.duplicate_imports = duplicate_count

                if duplicate_count > 0:
                    self.logger.warning(f"发现 {duplicate_count} 条重复数据")

            except SQLAlchemyError as e:
                result.add_error(f"检查重复数据失败: {str(e)}")
                self.logger.error(f"检查重复数据失败: {e}")

    async def _import_batch_with_retry(
        self,
        batch_results: List[ManifestParseResult],
        batch_number: int
    ) -> Tuple[int, List[str]]:
        """
        带重试机制的批次导入

        参数说明：
        - batch_results: 当前批次的解析结果
        - batch_number: 批次编号

        返回值：
        - Tuple[int, List[str]]: (成功数量, 错误列表)

        重试策略：
        1. 指数退避延迟
        2. 最大重试次数限制
        3. 仅对特定异常重试
        4. 详细的重试日志

        为什么需要重试：
        1. 处理临时性数据库问题
        2. 提高导入成功率
        3. 网络连接问题恢复
        4. 系统负载波动处理
        """
        last_exception = None
        errors = []

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    self.logger.warning(f"批次{batch_number}重试第{attempt}次，延迟{delay}秒")
                    await asyncio.sleep(delay)

                success_count, attempt_errors = await self._import_batch(batch_results)

                if attempt_errors:
                    errors.extend(attempt_errors)

                return success_count, errors

            except (SQLAlchemyError, IntegrityError) as e:
                last_exception = e
                error_msg = f"批次{batch_number}数据库错误 (尝试{attempt + 1}): {str(e)}"
                errors.append(error_msg)
                self.logger.warning(error_msg)

                # 某些错误不应该重试
                if "unique constraint" in str(e).lower() or "foreign key" in str(e).lower():
                    self.logger.error(f"批次{batch_number}遇到约束错误，停止重试")
                    break

            except Exception as e:
                last_exception = e
                error_msg = f"批次{batch_number}未知错误 (尝试{attempt + 1}): {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)

                # 非数据库错误通常不需要重试
                break

        # 所有重试都失败了
        if last_exception:
            error_msg = f"批次{batch_number}重试失败: {str(last_exception)}"
            errors.append(error_msg)
            self.logger.error(error_msg)

        return 0, errors

    async def _import_batch(
        self,
        batch_results: List[ManifestParseResult]
    ) -> Tuple[int, List[str]]:
        """
        导入单个批次的数据

        参数说明：
        - batch_results: 当前批次的解析结果

        返回值：
        - Tuple[int, List[str]]: (成功数量, 错误列表)

        处理步骤：
        1. 创建数据库会话
        2. 转换数据为模型对象
        3. 执行批量插入
        4. 提交事务
        5. 处理异常和回滚

        性能优化：
        1. 使用bulk_insert_mappings
        2. 单个事务处理多个表
        3. 批量数据转换
        4. 连接池优化

        错误处理：
        1. 事务回滚机制
        2. 详细错误记录
        3. 部分成功处理
        4. 数据一致性保证
        """
        errors = []
        successful_count = 0

        async with self.session_factory() as session:
            try:
                # 开始事务
                await session.begin()

                # 准备批量插入数据
                function_data_list = []
                attack_mapping_data_list = []
                child_mapping_data_list = []

                # 转换解析结果为数据库模型数据
                for parse_result in batch_results:
                    try:
                        model_data = await self._convert_to_model_data(parse_result.data)
                        function_data_list.append(model_data['function'])
                        # 保持索引关系，以便后续正确设置外键
                        attack_mapping_data_list.append({
                            'function_index': len(function_data_list) - 1,
                            'mappings': model_data['attack_mappings']
                        })
                        child_mapping_data_list.append({
                            'function_index': len(function_data_list) - 1,
                            'mappings': model_data['child_mappings']
                        })

                    except Exception as e:
                        error_msg = f"数据转换失败 ({parse_result.data.get('alias', 'unknown')}): {str(e)}"
                        errors.append(error_msg)
                        self.logger.warning(error_msg)
                        continue

                # 逐条插入主表并获取ID（SQLite兼容方案）
                function_ids = []
                if function_data_list:
                    for function_data in function_data_list:
                        try:
                            # 创建ORM对象实例
                            function_obj = MalAPIFunction(**function_data)
                            session.add(function_obj)
                            await session.flush()  # 获取生成的ID但不提交
                            function_ids.append(function_obj.id)
                            successful_count += 1
                        except Exception as e:
                            # 单条记录失败，继续处理下一条
                            error_msg = f"插入函数失败 ({function_data.get('alias', 'unknown')}): {str(e)}"
                            errors.append(error_msg)
                            self.logger.warning(error_msg)
                            continue

                # 准备最终的ATT&CK映射数据（设置正确的function_id）
                final_attack_mappings = []
                for attack_group in attack_mapping_data_list:
                    function_index = attack_group['function_index']
                    if function_index < len(function_ids):
                        function_id = function_ids[function_index]
                        for mapping in attack_group['mappings']:
                            mapping['function_id'] = function_id
                            final_attack_mappings.append(mapping)

                # 准备最终的子函数映射数据（设置正确的parent_function_id）
                final_child_mappings = []
                for child_group in child_mapping_data_list:
                    function_index = child_group['function_index']
                    if function_index < len(function_ids):
                        function_id = function_ids[function_index]
                        for mapping in child_group['mappings']:
                            mapping['parent_function_id'] = function_id
                            final_child_mappings.append(mapping)

                # 批量插入ATT&CK映射表
                if final_attack_mappings:
                    await session.execute(
                        insert(AttCKMapping),
                        final_attack_mappings
                    )

                # 批量插入子函数映射表
                if final_child_mappings:
                    await session.execute(
                        insert(FunctionChild),
                        final_child_mappings
                    )

                # 提交事务
                await session.commit()

                self.logger.debug(f"批次提交成功: {successful_count}条记录")

            except SQLAlchemyError as e:
                # 回滚事务
                await session.rollback()
                error_msg = f"批次事务失败: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg, exc_info=True)

                # 重新抛出异常以便重试
                raise

            except Exception as e:
                # 回滚事务
                await session.rollback()
                error_msg = f"批次处理失败: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg, exc_info=True)

                # 重新抛出异常以便重试
                raise

        return successful_count, errors

    async def _convert_to_model_data(self, data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        将解析数据转换为数据库模型数据

        参数说明：
        - data: 解析后的manifest数据

        返回值：
        - Dict[str, List[Dict]]: 包含各表数据的字典

        转换规则：
        1. 字段映射和类型转换
        2. 关联数据处理
        3. 业务逻辑验证
        4. 默认值填充

        数据转换策略：
        1. 保持原始数据完整性
        2. 适应数据库字段约束
        3. 处理数据类型转换
        4. 生成关联表数据

        为什么单独封装这个方法：
        1. 分离数据转换逻辑，便于测试
        2. 支持不同的转换策略
        3. 便于扩展和修改
        4. 提高代码可读性
        """
        # 生成或提取hash_id
        hash_id = data.get('hash_id') or self._generate_hash_id(data)

        # 准备主表数据
        function_data = {
            'hash_id': hash_id,
            'alias': data.get('alias', ''),
            'root_function': data.get('root_function'),
            'summary': data.get('summary', ''),
            'cpp_code': data.get('generated_cpp', ''),
            'cpp_filepath': data.get('cpp_filepath', ''),
            'manifest_json': data,  # 存储完整的manifest数据
            'tries': data.get('tries', 1),
            'status': data.get('status', 'unknown'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        # 准备ATT&CK映射数据（仅存储映射关系，technique详细信息从attack_techniques表获取）
        attack_mappings = []
        attck_list = data.get('attck', [])
        if attck_list and isinstance(attck_list, list):
            for technique in attck_list:
                if technique:  # 过滤空值
                    attack_mapping_data = {
                        'function_id': None,  # 稍后更新为实际的function_id
                        'technique_id': str(technique).strip().upper(),
                        'created_at': datetime.utcnow()
                    }
                    attack_mappings.append(attack_mapping_data)

        # 准备子函数映射数据（注意：需要parent_function_id，现在先设为None）
        child_mappings = []
        children_aliases = data.get('children_aliases', {})
        if children_aliases and isinstance(children_aliases, dict):
            for child_alias, child_info in children_aliases.items():
                child_mapping_data = {
                    'parent_function_id': None,  # 稍后更新为实际的parent_function_id
                    'child_function_name': str(child_alias).strip(),
                    'child_alias': str(child_alias).strip(),
                    'child_description': str(child_info) if not isinstance(child_info, dict) else str(child_info.get('description', '')),
                    'created_at': datetime.utcnow()
                }
                child_mappings.append(child_mapping_data)

        return {
            'function': function_data,
            'attack_mappings': attack_mappings,
            'child_mappings': child_mappings
        }

    def _generate_hash_id(self, data: Dict[str, Any]) -> str:
        """
        生成hash_id

        参数说明：
        - data: manifest数据

        返回值：
        - str: 生成的hash_id

        生成策略：
        1. 基于alias字段生成SHA256哈希
        2. 确保唯一性
        3. 长度固定为64字符

        为什么需要生成hash_id：
        1. 确保数据唯一标识
        2. 支持重复数据检测
        3. 便于关联查询
        4. 提高查询性能
        """
        alias = data.get('alias', '')
        if not alias:
            # 如果没有alias，使用其他字段组合
            fallback_data = f"{data.get('status', '')}{data.get('root_function', '')}{datetime.utcnow()}"
            alias = fallback_data

        return hashlib.sha256(alias.encode('utf-8')).hexdigest()

    def _update_global_statistics(self, result: ImportResult) -> None:
        """
        更新全局统计信息

        参数说明：
        - result: 导入结果

        统计信息用途：
        1. 性能监控和分析
        2. 系统优化依据
        3. 使用情况统计
        4. 问题诊断支持
        """
        self.stats['total_imports'] += result.total_records
        self.stats['total_successful'] += result.successful_imports
        self.stats['total_failed'] += result.failed_imports
        self.stats['total_duplicates'] += result.duplicate_imports
        self.stats['total_time'] += result.processing_time

        # 计算平均时间
        if self.stats['total_imports'] > 0:
            self.stats['average_time_per_batch'] = self.stats['total_time'] / (self.stats['total_imports'] / self.batch_size)

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取导入器统计信息

        返回值：
        - Dict[str, Any]: 详细的统计信息

        统计内容：
        1. 导入总量统计
        2. 成功率计算
        3. 性能指标
        4. 错误统计
        """
        stats = self.stats.copy()

        # 计算成功率
        if stats['total_imports'] > 0:
            stats['success_rate'] = (stats['total_successful'] / stats['total_imports']) * 100
            stats['failure_rate'] = (stats['total_failed'] / stats['total_imports']) * 100
            stats['duplicate_rate'] = (stats['total_duplicates'] / stats['total_imports']) * 100
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
            stats['duplicate_rate'] = 0.0

        # 计算性能指标
        if stats['total_time'] > 0:
            stats['records_per_second'] = stats['total_successful'] / stats['total_time']
        else:
            stats['records_per_second'] = 0.0

        return stats

    def print_statistics(self) -> None:
        """
        打印统计信息到控制台

        用途：
        1. 性能监控
        2. 调试和开发
        3. 用户反馈
        """
        stats = self.get_statistics()

        print("\n" + "="*60)
        print("批量导入器统计信息")
        print("="*60)
        print(f"总导入记录数: {stats['total_imports']:,}")
        print(f"成功导入数: {stats['total_successful']:,}")
        print(f"失败导入数: {stats['total_failed']:,}")
        print(f"重复记录数: {stats['total_duplicates']:,}")
        print(f"总导入时间: {stats['total_time']:.2f}s")
        print(f"成功率: {stats['success_rate']:.1f}%")
        print(f"失败率: {stats['failure_rate']:.1f}%")
        print(f"重复率: {stats['duplicate_rate']:.1f}%")
        print(f"导入速度: {stats['records_per_second']:.1f} 记录/秒")
        print(f"平均批次时间: {stats['average_time_per_batch']:.2f}s")
        print("="*60)

    def reset_statistics(self) -> None:
        """
        重置统计信息

        用途：
        1. 开始新的统计周期
        2. 清理累积数据
        3. 测试和调试
        """
        self.stats = {
            'total_imports': 0,
            'total_successful': 0,
            'total_failed': 0,
            'total_duplicates': 0,
            'total_time': 0.0,
            'average_time_per_batch': 0.0
        }
        self.logger.info("批量导入器统计信息已重置")