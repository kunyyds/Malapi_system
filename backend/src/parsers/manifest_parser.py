"""
manifest_parser.py - MalFocus manifest.json解析器

设计思路：
1. 专门处理MalFocus工具生成的manifest.json格式
2. 提供数据验证、修复、标准化功能
3. 支持批量处理和错误恢复
4. 为后续的LLM分析提供结构化数据

为什么需要专门解析器：
- MalFocus的manifest.json有特定的字段结构
- 需要验证ATT&CK技术ID的有效性
- 数据质量问题需要自动修复
- 为数据库导入准备标准化数据

使用示例：
>>> parser = ManifestParser(strict_mode=False)
>>> result = await parser.parse_file("/path/to/manifest.json")
>>> if result.is_valid:
>>>     print(f"成功解析: {result.data['alias']}")
>>> else:
>>>     print(f"解析失败: {result.get_error_summary()}")
"""

import asyncio
import json
import logging
import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

from src.exceptions.data_exceptions import (
    ParseError,
    ValidationError,
    ErrorCodes
)


@dataclass
class ManifestParseResult:
    """
    manifest.json解析结果封装类

    设计思路：
    1. 为什么需要单独的结果类：封装解析状态、数据和错误信息
    2. 避免返回复杂的元组或字典，提高代码可读性
    3. 支持链式操作，便于批量处理
    4. 提供丰富的状态查询方法

    为什么使用dataclass：
    1. 自动生成__init__、__repr__等方法
    2. 类型提示支持
    3. 比手动定义类更简洁
    4. 支持字段默认值
    """
    is_valid: bool = False
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    source_file: Optional[str] = None
    parse_time: float = 0.0

    def add_error(self, error_msg: str) -> 'ManifestParseResult':
        """
        添加错误信息，支持链式调用

        参数说明：
        - error_msg: 错误消息内容

        为什么支持链式调用：
        1. 便于连续添加多个错误
        2. 提高代码可读性
        3. 减少中间变量

        设计示例：
        >>> result = ManifestParseResult()
        >>> result.add_error("字段缺失").add_error("格式错误")
        """
        self.errors.append(error_msg)
        self.is_valid = False
        return self

    def add_warning(self, warning_msg: str) -> 'ManifestParseResult':
        """
        添加警告信息，不影响解析成功状态

        参数说明：
        - warning_msg: 警告消息内容

        错误vs警告的区别：
        - 错误：必须修复的问题，导致解析失败
        - 警告：建议修复的问题，不影响解析成功
        """
        self.warnings.append(warning_msg)
        return self

    def get_error_summary(self) -> str:
        """
        获取错误摘要，用于日志记录

        返回值：
        - str: 错误摘要字符串

        为什么需要摘要：
        1. 日志记录时不宜显示全部错误详情
        2. 提供快速的错误概览
        3. 便于问题分类和统计
        """
        if not self.errors:
            return "无错误"

        # 显示前3个主要错误
        main_errors = self.errors[:3]
        if len(self.errors) > 3:
            return f"解析失败，共{len(self.errors)}个错误: {'; '.join(main_errors)}..."
        else:
            return f"解析失败，共{len(self.errors)}个错误: {'; '.join(main_errors)}"

    def get_status_summary(self) -> str:
        """
        获取解析状态摘要

        返回值：
        - str: 状态摘要信息

        用途：
        1. 进度报告
        2. 统计信息
        3. 调试输出
        """
        status = "✅ 成功" if self.is_valid else "❌ 失败"
        info_parts = [status]

        if self.source_file:
            info_parts.append(f"文件: {Path(self.source_file).name}")

        if self.parse_time > 0:
            info_parts.append(f"耗时: {self.parse_time:.2f}s")

        if self.warnings:
            info_parts.append(f"警告: {len(self.warnings)}个")

        return " | ".join(info_parts)


class ManifestParser:
    """
    MalFocus manifest.json解析器

    设计思路：
    1. 专门处理MalFocus工具的输出格式
    2. 提供严格的数据验证和宽松的错误恢复
    3. 支持ATT&CK技术验证和标准化
    4. 为数据库导入准备结构化数据

    核心功能：
    - JSON格式解析和验证
    - 必需字段检查和补全
    - ATT&CK技术ID标准化
    - 数据类型转换和清理

    为什么这样设计：
    1. 专用性：针对MalFocus格式优化
    2. 容错性：处理各种数据质量问题
    3. 可扩展：预留接口支持未来的格式变化
    4. 可测试：每个功能都可以独立测试
    """

    # 必需字段定义 - 为什么定义常量：便于维护和统一修改
    REQUIRED_FIELDS = ['status', 'alias', 'summary', 'attck']

    # 可选字段及其默认值
    OPTIONAL_FIELDS = {
        'root_function': None,
        'summary': '',
        'children_aliases': {},
        'tries': 1,
        'generated_cpp': '',
        'cpp_filepath': '',
        'manifest_json': '',
        'hash_id': ''
    }

    # ATT&CK技术ID格式验证正则表达式
    ATTACK_PATTERN = re.compile(r'^T\d{4}(\.\d{3})?(:.+)?$', re.IGNORECASE)

    def __init__(self, strict_mode: bool = False, validate_attack_ids: bool = True):
        """
        初始化解析器

        参数说明：
        - strict_mode: 严格模式，True时任何错误都导致解析失败
                           False时尝试修复数据并继续处理
        - validate_attack_ids: 是否验证ATT&CK技术ID的有效性

        为什么有strict_mode：
        1. 开发阶段使用strict_mode快速发现数据问题
        2. 生产环境使用非严格模式确保数据处理的连续性
        3. 不同场景对数据质量要求不同

        为什么有validate_attack_ids：
        1. ATT&CK ID格式复杂，需要验证
        2. 有时需要跳过验证以提高处理速度
        3. 支持自定义ATT&CK技术列表
        """
        self.strict_mode = strict_mode
        self.validate_attack_ids = validate_attack_ids
        self.logger = logging.getLogger(__name__)

        # 统计信息
        self.stats = {
            'total_files': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'total_errors': 0,
            'total_warnings': 0
        }

    async def parse_file(self, file_path: Union[str, Path]) -> ManifestParseResult:
        """
        解析manifest.json文件

        参数说明：
        - file_path: manifest.json文件的完整路径

        返回值：
        - ManifestParseResult: 包含解析结果和错误信息

        异常处理：
        - FileNotFoundError: 文件不存在
        - json.JSONDecodeError: JSON格式错误
        - ValidationError: 数据验证错误

        算法步骤：
        1. 文件预检查（存在性、大小、权限）
        2. 读取文件内容
        3. 解析JSON格式
        4. 验证必需字段
        5. 标准化数据格式
        6. 验证ATT&CK技术ID
        7. 最终数据清理
        8. 返回解析结果

        性能考虑：
        1. 异步文件读取，避免阻塞
        2. 文件大小限制，防止内存问题
        3. 错误恢复机制，避免单点失败
        """
        start_time = asyncio.get_event_loop().time()
        self.stats['total_files'] += 1

        # 标准化文件路径
        file_path = Path(file_path)
        result = ManifestParseResult(source_file=str(file_path))

        try:
            self.logger.info(f"开始解析manifest文件: {file_path}")

            # 步骤1: 文件预检查
            await self._pre_validate_file(file_path)

            # 步骤2: 读取文件内容
            raw_data = await self._read_json_file(file_path)

            # 步骤3: 基础结构验证
            if not await self._validate_basic_structure(raw_data, result):
                return result

            # 步骤4: 数据标准化和清理
            cleaned_data = await self._clean_and_normalize_data(raw_data, result, file_path)

            # 步骤5: ATT&CK技术验证
            if self.validate_attack_ids:
                if not await self._validate_attack_techniques(cleaned_data, result):
                    return result

            # 步骤6: 最终验证
            if not await self._final_validation(cleaned_data, result):
                return result

            # 成功解析
            result.is_valid = True
            result.data = cleaned_data
            result.parse_time = asyncio.get_event_loop().time() - start_time

            self.stats['successful_parses'] += 1
            self.logger.info(f"成功解析manifest文件: {file_path} (耗时: {result.parse_time:.2f}s)")

        except Exception as e:
            # 统一异常处理 - 捕获所有异常，确保不会因为单个文件失败而中断整个处理流程
            self._handle_parse_exception(e, file_path, result)
            self.stats['failed_parses'] += 1
            self.stats['total_errors'] += 1

        # 更新统计信息
        self.stats['total_warnings'] += len(result.warnings)

        return result

    async def _pre_validate_file(self, file_path: Path) -> None:
        """
        文件预验证

        验证内容：
        1. 文件是否存在
        2. 文件大小是否合理（避免读取超大文件）
        3. 文件是否可读
        4. 文件扩展名是否正确

        异常：
        - ParseError: 文件预验证失败时抛出

        为什么需要预验证：
        1. 早期发现问题，避免无效的读取操作
        2. 提供更友好的错误信息
        3. 保护系统资源（内存、CPU）
        """
        # 检查文件是否存在
        if not file_path.exists():
            raise ParseError(
                f"manifest文件不存在: {file_path}",
                file_path=str(file_path),
                suggestion="请检查文件路径是否正确"
            )

        # 检查文件大小（避免读取超大文件导致内存问题）
        file_size = file_path.stat().st_size
        max_size = 10 * 1024 * 1024  # 10MB限制

        if file_size > max_size:
            raise ParseError(
                f"manifest文件过大: {file_size:,} bytes (限制: {max_size:,} bytes)",
                file_path=str(file_path),
                suggestion="考虑分片处理大文件或检查文件是否正确"
            )

        if file_size == 0:
            raise ParseError(
                "manifest文件为空",
                file_path=str(file_path),
                suggestion="检查文件是否正确生成或传输"
            )

        # 检查文件扩展名
        if file_path.suffix.lower() != '.json':
            raise ParseError(
                f"文件扩展名不正确: {file_path.suffix}",
                file_path=str(file_path),
                suggestion="manifest文件应该是.json格式"
            )

    async def _read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """
        异步读取JSON文件内容

        设计思路：
        1. 使用异步IO避免阻塞
        2. 统一的文件编码处理
        3. 详细的错误信息
        4. JSON格式验证

        异常处理：
        - UnicodeDecodeError: 文件编码问题
        - json.JSONDecodeError: JSON格式问题

        性能考虑：
        1. 文件大小在预验证中已检查
        2. 使用异步读取，避免阻塞
        3. 统一的编码处理
        """
        try:
            # 异步读取文件内容，使用UTF-8编码
            loop = asyncio.get_event_loop()

            def sync_read_file():
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()

            content = await asyncio.wait_for(
                loop.run_in_executor(None, sync_read_file),
                timeout=30  # 30秒超时
            )

            # 解析JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                # 提供更详细的JSON错误信息
                error_info = {
                    'line': getattr(e, 'lineno', 'unknown'),
                    'column': getattr(e, 'colno', 'unknown'),
                    'position': getattr(e, 'pos', 'unknown')
                }

                raise ParseError(
                    f"JSON格式错误 (行{error_info['line']}, 列{error_info['column']}): {str(e)}",
                    file_path=str(file_path),
                    line_number=error_info['line'] if error_info['line'] != 'unknown' else None,
                    suggestion="检查JSON语法，确保所有引号、括号都正确匹配"
                )

        except asyncio.TimeoutError:
            raise ParseError(
                f"读取文件超时: {file_path}",
                file_path=str(file_path),
                suggestion="检查文件大小或磁盘性能"
            )

    async def _validate_basic_structure(self, data: Dict[str, Any], result: ManifestParseResult) -> bool:
        """
        验证基础数据结构

        验证规则：
        1. 检查必需字段是否存在
        2. 验证字段类型是否正确
        3. 检查关键字段值的有效性

        参数说明：
        - data: 解析后的原始数据
        - result: 解析结果对象，用于收集错误和警告

        返回值：
        - True: 基础验证通过
        - False: 验证失败（错误信息已添加到result）

        验证策略：
        1. 严格验证必需字段
        2. 宽松验证可选字段
        3. 提供详细的错误信息
        """
        # 检查数据是否为字典类型
        if not isinstance(data, dict):
            result.add_error("manifest数据必须是JSON对象（字典）")
            return False

        # 检查必需字段
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                result.add_error(f"缺少必需字段: {field}")
            elif data[field] is None:
                result.add_error(f"必需字段为空: {field}")

        # 验证status字段
        if 'status' in data:
            valid_statuses = ['ok', 'error', 'pending', 'generated', 'failed']
            if data['status'] not in valid_statuses:
                result.add_warning(f"未知的status值: {data['status']}，应为: {valid_statuses}")

        # 验证alias字段（严格模式：必须存在且非空）
        if 'alias' not in data:
            result.add_error("缺少必需字段: alias")
        elif not data['alias']:
            result.add_error("alias字段不能为空")
        else:
            alias = data['alias']
            if not isinstance(alias, str):
                result.add_error("alias字段必须是字符串")
            elif len(alias.strip()) == 0:
                result.add_error("alias字段不能为空字符串")
            elif len(alias) > 255:
                result.add_error("alias字段长度超过255字符")

        # 验证summary字段（严格模式：必须存在且非空）
        if 'summary' not in data:
            result.add_error("缺少必需字段: summary")
        elif not data['summary'] or len(str(data['summary']).strip()) == 0:
            result.add_error("summary字段不能为空，必须提供功能描述")

        # 验证attck字段（严格模式：必须存在且非空）
        if 'attck' not in data:
            result.add_error("缺少必需字段: attck")
        elif not data['attck']:
            result.add_error("attck字段不能为空")
        elif not isinstance(data['attck'], list):
            result.add_error("attck字段必须是数组")
        elif len(data['attck']) == 0:
            result.add_error("attck字段至少需要包含一个ATT&CK技术ID")
        else:
            # 检查每个元素的类型和内容
            import re
            attck_pattern = re.compile(r'^T\d{4}(\.\d+)?')  # Txxxx 或 Txxxx.xxx 格式

            for i, technique in enumerate(data['attck']):
                if not isinstance(technique, str):
                    result.add_error(f"attck数组第{i}个元素必须是字符串，当前类型: {type(technique).__name__}")
                elif len(technique.strip()) == 0:
                    result.add_error(f"attck数组第{i}个元素不能为空字符串")
                else:
                    # 提取ATT&CK编号（支持 Txxxx 或 Txxxx.xxx:[name] 格式）
                    tech_str = str(technique).strip()
                    # 如果包含冒号，只取冒号前的部分
                    if ':' in tech_str:
                        tech_id = tech_str.split(':')[0].strip()
                    else:
                        tech_id = tech_str

                    # 验证编号格式（Txxxx 或 Txxxx.xxx）
                    if not attck_pattern.match(tech_id.upper()):
                        result.add_error(f"attck数组第{i}个元素格式无效: '{technique}'，应为 'Txxxx' 或 'Txxxx.xxx:[名称]' 格式")

        return len(result.errors) == 0

    async def _clean_and_normalize_data(self, raw_data: Dict[str, Any], result: ManifestParseResult, file_path: Path) -> Dict[str, Any]:
        """
        清理和标准化数据

        处理内容：
        1. 补全缺失的可选字段
        2. 标准化字符串格式（去除空白、统一大小写等）
        3. 清理无效数据
        4. 类型转换
        5. 提取文件路径相关信息

        参数说明：
        - raw_data: 原始解析数据
        - result: 解析结果对象，用于收集警告
        - file_path: 文件路径，用于提取相关信息

        返回值：
        - Dict[str, Any]: 清理后的数据

        为什么不修改原始数据：
        1. 保持原始数据完整性，便于调试
        2. 函数式编程思想，避免副作用
        3. 便于测试和验证

        数据标准化规则：
        1. 字符串去除首尾空白
        2. ATT&CK技术ID转为大写
        3. 数字类型统一为int
        4. 布尔值统一为bool
        """
        cleaned = raw_data.copy()

        # 补全可选字段
        for field, default_value in self.OPTIONAL_FIELDS.items():
            if field not in cleaned:
                cleaned[field] = default_value
                self.logger.debug(f"补全字段 {field} = {default_value}")

        # 标准化字符串字段
        string_fields = ['alias', 'summary', 'root_function', 'generated_cpp']
        for field in string_fields:
            if field in cleaned and cleaned[field]:
                # 确保是字符串类型并去除首尾空白
                if isinstance(cleaned[field], str):
                    cleaned[field] = cleaned[field].strip()
                else:
                    # 非字符串类型转为字符串
                    cleaned[field] = str(cleaned[field]).strip()
                    result.add_warning(f"字段{field}类型转换: {type(raw_data[field]).__name__} -> str")

        # 标准化attck数组（支持 Txxxx:[name] 或 Txxxx.xxx:[name] 格式）
        if 'attck' in cleaned and isinstance(cleaned['attck'], list):
            import re
            attck_pattern = re.compile(r'^T\d{4}(\.\d+)?')  # Txxxx 或 Txxxx.xxx 格式

            normalized_attck = []
            for i, technique in enumerate(cleaned['attck']):
                if technique and str(technique).strip():
                    # 转为字符串并去除空白
                    tech_str = str(technique).strip()

                    # 提取ATT&CK编号（支持 Txxxx:[name] 或 Txxxx.xxx:[name] 格式）
                    if ':' in tech_str:
                        # 包含冒号，提取冒号前的编号部分
                        tech_id = tech_str.split(':')[0].strip().upper()
                    else:
                        # 不包含冒号，直接使用
                        tech_id = tech_str.upper()

                    # 验证编号格式
                    if attck_pattern.match(tech_id):
                        normalized_attck.append(tech_id)
                    else:
                        # 格式无效，记录警告但保留原始值（后续在验证阶段会报错）
                        result.add_warning(f"ATT&CK技术ID格式可能无效: {technique} -> {tech_id}")
                        normalized_attck.append(tech_id)

                    # 记录格式变化（仅当实际发生转换时）
                    if tech_id != tech_str and ':' in tech_str:
                        original_name = tech_str.split(':', 1)[1].strip() if ':' in tech_str else ''
                        result.add_warning(f"ATT&CK技术ID已提取: '{technique}' -> '{tech_id}'" +
                                          (f" (忽略描述: {original_name})" if original_name else ''))

            cleaned['attck'] = normalized_attck

        # 标准化tries字段为整数
        if 'tries' in cleaned:
            try:
                cleaned['tries'] = int(cleaned['tries'])
                if cleaned['tries'] < 1:
                    cleaned['tries'] = 1
                    result.add_warning("tries字段值小于1，已调整为1")
            except (ValueError, TypeError):
                cleaned['tries'] = 1
                result.add_warning(f"tries字段类型转换失败，已设为默认值1")

        # 提取文件路径相关信息
        if file_path:
            # 从文件路径提取hash_id和alias
            path_parts = file_path.parts

            # 假设路径结构: files/{hash_id}/{alias}/manifest.json
            if len(path_parts) >= 4:
                extracted_hash = path_parts[-3]  # hash_id
                extracted_alias = path_parts[-2]  # alias目录名

                # 如果数据中没有hash_id，从路径提取
                if not cleaned.get('hash_id'):
                    cleaned['hash_id'] = extracted_hash
                    result.add_warning(f"从路径提取hash_id: {extracted_hash}")

                # 验证alias的一致性
                if cleaned.get('alias') and cleaned['alias'] != extracted_alias:
                    result.add_warning(f"alias不一致: 数据中='{cleaned['alias']}', 路径中='{extracted_alias}'")

                # 设置文件路径信息
                cleaned['manifest_path'] = str(file_path)
                cleaned['cpp_filepath'] = str(file_path.parent / f"{extracted_alias}.cpp")

        return cleaned

    async def _validate_attack_techniques(self, data: Dict[str, Any], result: ManifestParseResult) -> bool:
        """
        验证ATT&CK技术ID

        验证规则：
        1. ID格式：T开头 + 数字（如T1027）
        2. 支持子技术ID（如T1027.001）
        3. 支持自定义名称（如T1027:custom_name）
        4. 提供技术ID修复建议

        参数说明：
        - data: 清理后的数据
        - result: 解析结果对象

        返回值：
        - bool: 验证是否通过

        ATT&CK ID格式说明：
        - Tnnnn: 基础技术ID（如T1027）
        - Tnnnn.nnn: 子技术ID（如T1027.001）
        - Tnnnn:name: 带自定义名称的技术ID（如T1027:obfuscation）

        为什么需要验证：
        1. 确保数据质量
        2. 便于后续处理和分析
        3. 提供用户友好的错误提示
        """
        if 'attck' not in data or not data['attck']:
            return True  # attck字段是可选的

        invalid_techniques = []
        valid_techniques = []

        for technique in data['attck']:
            if self.ATTACK_PATTERN.match(technique):
                valid_techniques.append(technique)
            else:
                invalid_techniques.append(technique)
                # 提供修复建议
                suggestion = self._generate_attack_id_suggestion(technique)
                result.add_error(f"无效的ATT&CK技术ID: {technique} (建议: {suggestion})")

        # 如果有无效ID，在非严格模式下尝试修复
        if invalid_techniques and not self.strict_mode:
            fixed_techniques = []
            for technique in invalid_techniques:
                fixed = self._try_fix_attack_id(technique)
                if fixed:
                    fixed_techniques.append(fixed)
                    result.add_warning(f"ATT&CK技术ID自动修复: {technique} -> {fixed}")

            # 更新数据，使用修复后的ID
            if fixed_techniques:
                data['attck'] = valid_techniques + fixed_techniques
                result.add_warning(f"已修复{len(fixed_techniques)}个ATT&CK技术ID")

        # 如果仍有无效ID且在严格模式下，验证失败
        remaining_invalid = len(invalid_techniques) - len([t for t in invalid_techniques if self._try_fix_attack_id(t)])
        if remaining_invalid > 0 and self.strict_mode:
            result.add_error(f"严格模式下，{remaining_invalid}个ATT&CK技术ID格式无效")
            return False

        return len(result.errors) == 0

    async def _final_validation(self, data: Dict[str, Any], result: ManifestParseResult) -> bool:
        """
        最终验证步骤

        验证内容：
        1. 业务逻辑验证
        2. 数据一致性检查
        3. 特殊字段验证
        4. 完整性检查

        参数说明：
        - data: 完全处理后的数据
        - result: 解析结果对象

        返回值：
        - bool: 最终验证是否通过

        业务规则：
        1. alias和hash_id不能同时为空
        2. CPP文件路径存在时，对应的CPP文件应该存在
        3. status为ok时，应该有有效的数据
        """
        # 检查alias字段
        if not data.get('alias') or len(str(data.get('alias', '')).strip()) == 0:
            if self.strict_mode:
                result.add_error("alias字段不能为空")
            else:
                result.add_warning("alias字段为空，将影响数据识别")

        # 检查tries字段的合理性
        if 'tries' in data:
            tries = data['tries']
            if tries > 1000:
                result.add_warning(f"tries值异常大: {tries}，可能存在问题")
            if tries < 0:
                result.add_error("tries值不能为负数")

        # 验证数据一致性
        if data.get('status') == 'ok':
            # status为ok时，应该有基本的必需信息
            if not data.get('alias'):
                result.add_error("status为ok时，alias字段不能为空")
            if not data.get('attck'):
                result.add_warning("status为ok但attck字段为空")

        # 检查文件路径的一致性
        if 'manifest_path' in data and 'cpp_filepath' in data:
            manifest_path = Path(data['manifest_path'])
            cpp_path = Path(data['cpp_filepath'])

            # 检查CPP文件是否存在
            if not cpp_path.exists():
                result.add_warning(f"CPP文件不存在: {cpp_path}")

        return len(result.errors) == 0

    def _handle_parse_exception(self, exception: Exception, file_path: Path, result: ManifestParseResult) -> None:
        """
        统一的异常处理

        参数说明：
        - exception: 捕获的异常
        - file_path: 正在解析的文件路径
        - result: 解析结果对象

        为什么需要统一异常处理：
        1. 确保不会因为单个文件失败而中断整个处理流程
        2. 提供一致的错误信息格式
        3. 便于错误分类和统计
        4. 支持异常恢复机制
        """
        if isinstance(exception, (ParseError, ValidationError)):
            # 自定义异常，直接使用其信息
            result.add_error(str(exception))
            self.logger.error(f"解析失败 ({file_path.name}): {exception}")

        elif isinstance(exception, FileNotFoundError):
            result.add_error(f"文件不存在: {file_path}")
            self.logger.error(f"文件不存在: {file_path}")

        elif isinstance(exception, json.JSONDecodeError):
            result.add_error(f"JSON格式错误: {str(exception)}")
            self.logger.error(f"JSON格式错误 ({file_path.name}): {exception}")

        elif isinstance(exception, PermissionError):
            result.add_error(f"文件权限不足: {file_path}")
            self.logger.error(f"权限不足，无法读取文件: {file_path}")

        elif isinstance(exception, asyncio.TimeoutError):
            result.add_error(f"读取文件超时: {file_path}")
            self.logger.error(f"读取文件超时: {file_path}")

        else:
            # 其他未知异常
            error_msg = f"未知错误: {type(exception).__name__}: {str(exception)}"
            result.add_error(error_msg)
            self.logger.error(f"解析文件时发生未知异常 ({file_path.name}): {exception}", exc_info=True)

    def _generate_attack_id_suggestion(self, invalid_id: str) -> str:
        """
        生成ATT&CK技术ID修复建议

        参数说明：
        - invalid_id: 无效的ATT&CK技术ID

        返回值：
        - str: 修复建议

        常见修复策略：
        1. 补全T前缀：1027 -> T1027
        2. 修正格式：t1027 -> T1027
        3. 移除多余字符：T1027ABC -> T1027
        """
        invalid_id = str(invalid_id).strip()

        # 策略1: 缺少T前缀
        if invalid_id.isdigit():
            return f"T{invalid_id}"

        # 策略2: 大小写问题
        if invalid_id.lower().startswith('t'):
            return f"T{invalid_id[1:]}"

        # 策略3: 提取开头的数字部分
        import re
        match = re.match(r'([Tt]*)(\d+)', invalid_id)
        if match:
            return f"T{match.group(2)}"

        # 策略4: 提取所有数字
        numbers = re.findall(r'\d+', invalid_id)
        if numbers:
            return f"T{numbers[0]}"

        return "T#### (请填写正确的ATT&CK技术ID)"

    def _try_fix_attack_id(self, invalid_id: str) -> Optional[str]:
        """
        尝试自动修复ATT&CK技术ID

        参数说明：
        - invalid_id: 无效的ATT&CK技术ID

        返回值：
        - Optional[str]: 修复后的ID，如果无法修复返回None

        修复策略：
        1. 简单格式修正
        2. 常见拼写错误修正
        3. 标准化处理

        注意：只在非严格模式下使用
        """
        # 转为字符串并去除空白
        tech_str = str(invalid_id).strip()

        # 策略1: 补全T前缀
        if tech_str.isdigit() and len(tech_str) == 4:
            return f"T{tech_str}"

        # 策略2: 修正大小写
        if tech_str.lower().startswith('t') and len(tech_str) == 5:
            return tech_str.upper()

        # 策略3: 移除多余后缀
        import re
        match = re.match(r'^([Tt]\d{4})', tech_str)
        if match:
            return match.group(1).upper()

        return None

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取解析统计信息

        返回值：
        - Dict[str, Any]: 包含详细统计信息的字典

        统计信息用途：
        1. 性能监控
        2. 质量评估
        3. 问题诊断
        4. 进度跟踪
        """
        total = self.stats['total_files']
        if total == 0:
            return {
                'total_files': 0,
                'success_rate': 0.0,
                'error_rate': 0.0,
                'average_errors_per_file': 0.0,
                'average_warnings_per_file': 0.0
            }

        return {
            'total_files': total,
            'successful_parses': self.stats['successful_parses'],
            'failed_parses': self.stats['failed_parses'],
            'total_errors': self.stats['total_errors'],
            'total_warnings': self.stats['total_warnings'],
            'success_rate': (self.stats['successful_parses'] / total) * 100,
            'error_rate': (self.stats['failed_parses'] / total) * 100,
            'average_errors_per_file': self.stats['total_errors'] / total,
            'average_warnings_per_file': self.stats['total_warnings'] / total
        }

    def reset_statistics(self) -> None:
        """
        重置统计信息

        为什么需要重置：
        1. 开始新的处理周期
        2. 清理统计数据
        3. 避免内存累积
        """
        self.stats = {
            'total_files': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'total_errors': 0,
            'total_warnings': 0
        }
        self.logger.info("解析器统计信息已重置")