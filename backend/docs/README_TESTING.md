# MalAPI 数据处理层测试指南

## 概述

本目录包含 MalAPI System 数据导入模块的测试工具，支持配置化管理和环境变量控制。

## 环境准备

### 1. 激活 conda 环境
```bash
conda activate malapi-backend
```

### 2. 验证依赖安装
```bash
# 检查关键依赖
python -c "import sqlalchemy; print('SQLAlchemy版本:', sqlalchemy.__version__)"
python -c "import pydantic; print('Pydantic版本:', pydantic.__version__)"
```

## 测试脚本

### 1. 配置管理
```bash
# 查看当前配置
python scripts/tests/test_config.py

# 输出示例：
# 🔧 测试配置
# ==============================================================================
# 📁 scanner_config:
#   max_workers: 4
#   max_depth: 10
# ...
```

### 2. 简化测试（无外部依赖）
```bash
# 基础文件扫描和JSON解析测试
python scripts/tests/test_simple_scanner.py
```

### 3. 完整功能测试
```bash
# 使用默认配置
python scripts/tests/test_data_processing_configured.py

# 使用自定义配置
MALAPI_TEST_PARSER_FILES=20 python scripts/tests/test_data_processing_configured.py
```

### 4. 原始测试脚本（已修复）
```bash
# 使用修复后的原始脚本
python scripts/tests/test_data_processing.py
```

## 环境变量配置

### 测试文件数量控制
```bash
# 设置解析测试的文件数量
export MALAPI_TEST_PARSER_FILES=15

# 设置导入测试的文件数量
export MALAPI_TEST_IMPORT_FILES=8
```

### 性能配置
```bash
# 设置扫描器并发工作线程数
export MALAPI_TEST_MAX_WORKERS=8

# 设置扫描器最大深度
export MALAPI_TEST_MAX_DEPTH=15
```

### 数据库配置
```bash
# 使用自定义数据库
export MALAPI_TEST_DATABASE_URL="sqlite:///./test_malapi.db"

# 使用PostgreSQL
export MALAPI_TEST_DATABASE_URL="postgresql://user:pass@localhost/malapi_test"
```

### 验证配置
```bash
# 启用严格验证模式
export MALAPI_TEST_STRICT=true

# 启用ATT&CK ID验证
export MALAPI_TEST_VALIDATE_ATTACK=true
```

## 测试数据

### 文件结构
测试数据应位于以下位置之一（自动检测）：
- `../files/` (项目上级目录)
- `./files/` (项目根目录)
- `/home/mine/workspace/MalAPI_system/files` (绝对路径)

### 数据格式
每个测试目录应包含 `manifest.json` 文件：
```json
{
  "status": "ok",
  "alias": "MalAPI_Example",
  "summary": "示例函数描述",
  "attck": [
    "T1027: Obfuscated Files or Information",
    "T1055: Process Injection"
  ],
  "children_aliases": {
    "sub_401000": "Example"
  },
  "tries": 1
}
```

## 故障排除

### 常见问题

1. **模块导入失败**
   ```bash
   # 解决方案：激活正确的conda环境
   conda activate malapi-backend

   # 验证环境
   which python
   conda list | grep sqlalchemy
   ```

2. **数据库连接失败**
   ```bash
   # 使用SQLite作为测试数据库
   export MALAPI_TEST_DATABASE_URL="sqlite:///./test.db"

   # 检查文件权限
   ls -la *.db
   ```

3. **找不到测试数据**
   ```bash
   # 检查files目录
   ls -la ../files/ ./files/ /home/mine/workspace/MalAPI_system/files/

   # 创建测试数据链接
   ln -s /home/mine/workspace/MalAPI_system/files ./files
   ```

4. **Python版本兼容性**
   ```bash
   # 检查Python版本
   python --version

   # malapi-backend环境使用Python 3.11
   # 如果使用其他版本，可能遇到包兼容性问题
   ```

### 日志分析

测试日志文件：
- `test_data_processing.log` - 主测试日志
- `test_simple_scanner.log` - 简化测试日志

关键日志模式：
- `✅ 成功` - 操作成功
- `❌ 失败` - 操作失败
- `⚠️ 警告` - 非致命问题
- `🔧 修复` - 自动修复操作

## 性能监控

### 关键指标
- 文件扫描速度（文件/秒）
- JSON解析成功率（%）
- 数据库导入速度（记录/秒）
- 内存使用峰值
- 总测试时间

### 性能优化建议
1. 调整并发工作线程数（`MALAPI_TEST_MAX_WORKERS`）
2. 减少测试文件数量（`MALAPI_TEST_PARSER_FILES`）
3. 使用SQLite而不是PostgreSQL进行测试
4. 确保有足够的磁盘空间用于日志和临时文件

## 集成到CI/CD

### GitHub Actions 示例
```yaml
name: Test Data Processing
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup conda
      uses: conda-incubator/setup-miniconda@v2
      with:
        activate-environment: malapi-backend
    - name: Run tests
      env:
        MALAPI_TEST_PARSER_FILES: 10
        MALAPI_TEST_DATABASE_URL: "sqlite:///./test.db"
      run: |
        python test_data_processing_configured.py
```

## 贡献指南

### 添加新的测试配置
1. 在 `scripts/tests/test_config.py` 中添加新的配置项
2. 更新 `TestConfig` 数据类
3. 在 `_load_from_env` 方法中添加环境变量映射

### 添加新的测试用例
1. 在相应的测试函数中添加新的测试逻辑
2. 使用配置系统控制测试行为
3. 更新日志和统计信息

## 联系和支持

如有问题，请检查：
1. 本文档的故障排除部分
2. 测试日志文件中的详细错误信息
3. 项目的主要文档和代码注释