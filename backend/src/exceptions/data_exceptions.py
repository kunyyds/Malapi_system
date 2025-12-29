"""
数据处理异常类模块
设计思路：
1. 统一异常处理机制，提高错误处理的一致性
2. 提供详细的错误信息，便于调试和日志记录
3. 支持异常链，保留原始错误信息
4. 遵循Python异常处理最佳实践

为什么需要自定义异常：
- Python内置异常过于通用，无法体现业务逻辑
- 需要区分不同类型的处理错误（解析、验证、导入等）
- 便于上层代码进行精确的异常捕获和处理
- 提供更好的错误报告和用户体验

使用示例：
>>> try:
>>>     # 数据处理代码
>>>     parser = ManifestParser()
>>>     result = await parser.parse_file("manifest.json")
>>> except ParseError as e:
>>>     print(f"解析错误: {e}")
>>> except ValidationError as e:
>>>     print(f"验证错误: {e}")
>>> except DataImportError as e:
>>>     print(f"导入错误: {e}")
"""

from typing import Optional, List, Any, Dict
import json


class DataProcessingError(Exception):
    """
    数据处理基础异常类

    设计思路：
    1. 作为所有数据处理异常的基类
    2. 提供统一的错误信息格式
    3. 支持错误链，保留原始异常
    4. 包含错误代码和详细信息

    继承关系：
        DataProcessingError
        ├── ParseError           # 解析相关错误
        ├── ValidationError       # 验证相关错误
        ├── ImportError          # 导入相关错误
        └── ConfigurationError   # 配置相关错误
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初始化数据处理异常

        参数说明：
        - message: 错误消息，用户友好的描述
        - error_code: 错误代码，便于程序化处理
        - details: 详细错误信息字典，包含上下文数据
        - original_error: 原始异常，保留异常链

        为什么这样设计：
        1. message: 面向用户的简洁描述
        2. error_code: 面向程序的标识符
        3. details: 调试所需的详细信息
        4. original_error: 保持异常链完整性
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.original_error = original_error

    def to_dict(self) -> Dict[str, Any]:
        """
        将异常转换为字典格式

        返回值：
        - Dict[str, Any]: 包含所有异常信息的字典

        设计目的：
        1. 便于日志记录和序列化
        2. 支持API响应中的错误格式
        3. 提供结构化的错误信息
        """
        result = {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }

        # 如果有原始异常，添加异常链信息
        if self.original_error:
            result["original_error"] = str(self.original_error)
            result["original_error_type"] = type(self.original_error).__name__

        return result

    def __str__(self) -> str:
        """字符串表示，用于日志记录"""
        error_info = f"[{self.error_code}] {self.message}"
        if self.details:
            key = next(iter(self.details.keys()))
            value = self.details[key]
            error_info += f" - {key}: {value}"
        return error_info


class ParseError(DataProcessingError):
    """
    解析错误异常类

    设计思路：
    1. 专门处理文件解析过程中的错误
    2. 支持文件路径、行号等上下文信息
    3. 区分不同类型的解析错误（JSON、XML等）
    4. 提供修复建议

    使用场景：
    - JSON格式错误
    - 文件编码问题
    - 语法解析失败
    - 必需字段缺失
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
        suggestion: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初始化解析错误

        参数说明：
        - message: 错误描述
        - file_path: 文件路径，帮助定位错误位置
        - line_number: 行号，精确定位错误
        - column_number: 列号，精确定位错误
        - suggestion: 修复建议，帮助用户解决问题
        - original_error: 原始异常

        为什么需要这些参数：
        1. 文件路径：快速定位问题文件
        2. 行列号：精确定位错误位置
        3. 修复建议：提供解决方案
        """
        details = {}
        if file_path:
            details["file_path"] = file_path
        if line_number is not None:
            details["line_number"] = line_number
        if column_number is not None:
            details["column_number"] = column_number
        if suggestion:
            details["suggestion"] = suggestion

        super().__init__(
            message=message,
            error_code="PARSE_ERROR",
            details=details,
            original_error=original_error
        )

        # 保存便于访问的属性
        self.file_path = file_path
        self.line_number = line_number
        self.column_number = column_number
        self.suggestion = suggestion


class ValidationError(DataProcessingError):
    """
    数据验证错误异常类

    设计思路：
    1. 专门处理数据验证过程中的错误
    2. 支持字段级别的验证错误
    3. 提供详细的验证规则说明
    4. 支持批量验证错误的聚合

    使用场景：
    - 数据类型验证失败
    - 业务规则验证失败
    - 格式验证失败
    - 引用完整性验证失败
    """

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        validation_rule: Optional[str] = None,
        allowed_values: Optional[List[Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初始化验证错误

        参数说明：
        - message: 错误描述
        - field_name: 字段名称，标识验证失败的字段
        - field_value: 字段值，显示导致验证失败的值
        - validation_rule: 验证规则，说明具体的验证要求
        - allowed_values: 允许的值列表，提供正确的示例
        - original_error: 原始异常

        为什么需要这些参数：
        1. 字段名：精确定位验证失败的字段
        2. 字段值：显示导致问题的具体值
        3. 验证规则：说明验证要求
        4. 允许值：提供正确示例
        """
        details = {}
        if field_name:
            details["field_name"] = field_name
        if field_value is not None:
            # 序列化复杂对象，避免显示敏感信息
            if isinstance(field_value, (dict, list)):
                try:
                    details["field_value"] = json.dumps(field_value, ensure_ascii=False)
                except (TypeError, ValueError):
                    details["field_value"] = f"[{type(field_value).__name__}]"
            else:
                details["field_value"] = str(field_value)
        if validation_rule:
            details["validation_rule"] = validation_rule
        if allowed_values:
            details["allowed_values"] = allowed_values

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            original_error=original_error
        )

        # 保存便于访问的属性
        self.field_name = field_name
        self.field_value = field_value
        self.validation_rule = validation_rule
        self.allowed_values = allowed_values


class DataImportError(DataProcessingError):
    """
    数据导入错误异常类

    设计思路：
    1. 专门处理数据库导入过程中的错误
    2. 支持批量导入错误的上下文
    3. 提供失败记录的详细信息
    4. 支持部分失败和重试机制

    使用场景：
    - 数据库连接失败
    - 主键冲突错误
    - 外键约束错误
    - 批量插入失败
    - 事务回滚错误
    """

    def __init__(
        self,
        message: str,
        record_identifier: Optional[str] = None,
        batch_size: Optional[int] = None,
        failed_count: Optional[int] = None,
        success_count: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初始化数据导入错误

        参数说明：
        - message: 错误描述
        - record_identifier: 记录标识符，帮助定位失败的记录
        - batch_size: 批次大小，提供上下文信息
        - failed_count: 失败记录数，统计信息
        - success_count: 成功记录数，统计信息
        - original_error: 原始异常

        为什么需要这些参数：
        1. 记录标识符：定位具体的失败记录
        2. 批次信息：理解导入规模
        3. 统计信息：了解导入成功率
        """
        details = {}
        if record_identifier:
            details["record_identifier"] = record_identifier
        if batch_size is not None:
            details["batch_size"] = batch_size
        if failed_count is not None:
            details["failed_count"] = failed_count
        if success_count is not None:
            details["success_count"] = success_count

        super().__init__(
            message=message,
            error_code="IMPORT_ERROR",
            details=details,
            original_error=original_error
        )

        # 保存便于访问的属性
        self.record_identifier = record_identifier
        self.batch_size = batch_size
        self.failed_count = failed_count
        self.success_count = success_count


class ConfigurationError(DataProcessingError):
    """
    配置错误异常类

    设计思路：
    1. 专门处理配置相关错误
    2. 支持配置文件路径和参数名称
    3. 提供配置修复建议
    4. 区分配置类型（文件、环境变量等）

    使用场景：
    - 配置文件不存在
    - 配置格式错误
    - 必需配置项缺失
    - 配置值无效
    - 配置类型错误
    """

    def __init__(
        self,
        message: str,
        config_file: Optional[str] = None,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        expected_type: Optional[str] = None,
        suggestion: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初始化配置错误

        参数说明：
        - message: 错误描述
        - config_file: 配置文件路径
        - config_key: 配置项键名
        - config_value: 配置项值
        - expected_type: 期望的类型
        - suggestion: 修复建议
        - original_error: 原始异常

        为什么需要这些参数：
        1. 配置文件：定位配置文件
        2. 配置键名：精确定位配置项
        3. 配置值：显示问题值
        4. 期望类型：说明正确类型
        """
        details = {}
        if config_file:
            details["config_file"] = config_file
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = str(config_value)
        if expected_type:
            details["expected_type"] = expected_type
        if suggestion:
            details["suggestion"] = suggestion

        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            details=details,
            original_error=original_error
        )

        # 保存便于访问的属性
        self.config_file = config_file
        self.config_key = config_key
        self.config_value = config_value
        self.expected_type = expected_type
        self.suggestion = suggestion


# 错误代码常量定义
class ErrorCodes:
    """
    错误代码常量定义

    设计思路：
    1. 集中管理所有错误代码
    2. 便于程序化处理和国际化
    3. 避免硬编码错误代码
    4. 保持错误代码的一致性
    """

    # 解析相关错误代码
    PARSE_JSON_ERROR = "PARSE_JSON_ERROR"
    PARSE_INVALID_FORMAT = "PARSE_INVALID_FORMAT"
    PARSE_FILE_NOT_FOUND = "PARSE_FILE_NOT_FOUND"
    PARSE_ENCODING_ERROR = "PARSE_ENCODING_ERROR"

    # 验证相关错误代码
    VALIDATE_REQUIRED_FIELD = "VALIDATE_REQUIRED_FIELD"
    VALIDATE_INVALID_TYPE = "VALIDATE_INVALID_TYPE"
    VALIDATE_INVALID_FORMAT = "VALIDATE_INVALID_FORMAT"
    VALIDATE_OUT_OF_RANGE = "VALIDATE_OUT_OF_RANGE"
    VALIDATE_REFERENCE_NOT_FOUND = "VALIDATE_REFERENCE_NOT_FOUND"

    # 导入相关错误代码
    IMPORT_DATABASE_ERROR = "IMPORT_DATABASE_ERROR"
    IMPORT_CONNECTION_FAILED = "IMPORT_CONNECTION_FAILED"
    IMPORT_TRANSACTION_FAILED = "IMPORT_TRANSACTION_FAILED"
    IMPORT_DUPLICATE_KEY = "IMPORT_DUPLICATE_KEY"
    IMPORT_FOREIGN_KEY = "IMPORT_FOREIGN_KEY"

    # 配置相关错误代码
    CONFIG_FILE_NOT_FOUND = "CONFIG_FILE_NOT_FOUND"
    CONFIG_MISSING_KEY = "CONFIG_MISSING_KEY"
    CONFIG_INVALID_VALUE = "CONFIG_INVALID_VALUE"
    CONFIG_TYPE_MISMATCH = "CONFIG_TYPE_MISMATCH"


# 异常工厂函数，提供便捷的异常创建方法
def create_parse_error(
    message: str,
    file_path: Optional[str] = None,
    line_number: Optional[int] = None,
    suggestion: Optional[str] = None,
    original_error: Optional[Exception] = None
) -> ParseError:
    """
    创建解析错误异常的便捷函数

    设计思路：
    1. 简化常见解析错误的创建过程
    2. 提供一致的错误信息格式
    3. 减少重复代码
    4. 便于单元测试中的异常创建
    """
    return ParseError(
        message=message,
        file_path=file_path,
        line_number=line_number,
        suggestion=suggestion,
        original_error=original_error
    )


def create_validation_error(
    message: str,
    field_name: Optional[str] = None,
    field_value: Optional[Any] = None,
    validation_rule: Optional[str] = None,
    original_error: Optional[Exception] = None
) -> ValidationError:
    """
    创建验证错误异常的便捷函数
    """
    创建验证错误异常的便捷函数,提供标准化的错误信息格式
    """
    return ValidationError(
        message=message,
        field_name=field_name,
        field_value=field_value,
        validation_rule=validation_rule,
        original_error=original_error
    )


def create_import_error(
    message: str,
    record_identifier: Optional[str] = None,
    batch_size: Optional[int] = None,
    original_error: Optional[Exception] = None
) -> DataImportError:
    """
    创建导入错误异常的便捷函数
    """
    创建导入错误异常的便捷函数，提供标准化的错误信息格式
    """
    return DataImportError(
        message=message,
        record_identifier=record_identifier,
        batch_size=batch_size,
        original_error=original_error
    )