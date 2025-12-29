# 数据库初始化和迁移指南

## 问题背景

当删除 `malapi.db` 数据库文件后，重启后端服务需要正确创建所有表，包括 ATT&CK 相关的表（`attack_tactics` 和 `attack_techniques`）。

## 解决方案

系统提供了**三层保护机制**来确保数据库正确初始化：

### 1. 启动脚本自动检查（推荐）

`scripts/start_dev.sh` 会在启动服务前自动调用 `scripts/init_database.sh` 进行数据库检查和初始化。

**使用方法**：
```bash
cd /home/mine/workspace/MalAPI_system/backend
./scripts/start_dev.sh
```

### 2. 应用启动时自动创建表

应用启动时，`src/main.py` 会调用 `src/database/connection.py` 中的 `init_db()` 函数：

- 使用 SQLAlchemy 创建基础表
- 调用 `init_attack_tables()` 函数检查并创建 ATT&CK 表
- 如果 ATT&CK 表为空，会在日志中提示运行导入脚本

**日志示例**：
```
INFO:     创建 attack_tactics 表...
INFO:     创建 attack_techniques 表...
WARNING:  ATT&CK 表已创建但数据为空。请运行导入脚本
INFO:     ATT&CK 表状态: tactics=0, techniques=0
```

### 3. 手动初始化脚本

如果需要手动重新初始化数据库：

```bash
cd /home/mine/workspace/MalAPI_system/backend
bash scripts/init_database.sh
```

## 完整的初始化流程

### 第一次初始化（数据库不存在）

1. **删除旧数据库（如果存在）**
   ```bash
   rm /home/mine/workspace/MalAPI_system/backend/malapi.db
   ```

2. **启动服务（会自动初始化）**
   ```bash
   cd /home/mine/workspace/MalAPI_system/backend
   ./scripts/start_dev.sh
   ```

   脚本会自动：
   - ✅ 检测数据库不存在
   - ✅ 创建 ATT&CK 表结构
   - ✅ 导入 ATT&CK 基础数据（14 条 tactics + 691 条 techniques）
   - ✅ 启动 FastAPI 服务

### 数据库损坏时恢复

如果 `attack_tactics` 或 `attack_techniques` 表损坏：

1. **运行初始化脚本**
   ```bash
   cd /home/mine/workspace/MalAPI_system/backend
   bash scripts/init_database.sh
   ```

   脚本会：
   - ✅ 检测表不存在或已损坏
   - ✅ 删除并重建表结构
   - ✅ 重新导入 ATT&CK 数据

### ATT&CK 数据为空时

如果表存在但数据为空（可能是导入失败）：

```bash
cd /home/mine/workspace/MalAPI_system/backend
python scripts/maintenance/import_attack.py
```

## 验证数据库状态

### 检查表结构

```bash
sqlite3 backend/malapi.db ".schema attack_tactics"
sqlite3 backend/malapi.db ".schema attack_techniques"
```

### 检查数据量

```bash
sqlite3 backend/malapi.db "
SELECT 'attack_tactics' as table_name, COUNT(*) as count FROM attack_tactics
UNION ALL
SELECT 'attack_techniques', COUNT(*) FROM attack_techniques
UNION ALL
SELECT 'malapi_functions', COUNT(*) FROM malapi_functions
UNION ALL
SELECT 'attck_mappings', COUNT(*) FROM attck_mappings;
"
```

### 测试 JOIN 查询

```bash
sqlite3 backend/malapi.db "
SELECT
    f.alias,
    at.technique_id,
    at.technique_name,
    att.tactic_name_en
FROM malapi_functions f
INNER JOIN attck_mappings am ON f.id = am.function_id
INNER JOIN attack_techniques at ON am.technique_id = at.technique_id
INNER JOIN attack_tactics att ON at.tactic_id = att.tactic_id
LIMIT 5;
"
```

## 常见问题

### Q1: 为什么 ATT&CK 表的 id 字段必须是 INTEGER 而不是 BIGINT？

**A**: SQLite 的 `AUTOINCREMENT` 关键字只对 `INTEGER` 类型有效。如果使用 `BIGINT`，插入数据时会报错 `NOT NULL constraint failed: id`。

### Q2: 为什么不直接在 SQLAlchemy 模型中定义正确的类型？

**A**: 模型已经使用 `Integer` 类型了。但在应用启动时，我们使用原始 SQL 创建 ATT&CK 表，确保始终使用正确的 `INTEGER PRIMARY KEY AUTOINCREMENT` 结构。

### Q3: 如何重新导入所有数据？

**A**:
```bash
# 1. 删除数据库
rm backend/malapi.db

# 2. 运行启动脚本（会自动初始化）
cd backend
./scripts/start_dev.sh

# 3. 通过 Web 界面导入函数数据
# 访问 http://localhost:8000/api/v1/admin/db
```

### Q4: ATT&CK 数据更新了怎么办？

**A**: 重新运行导入脚本：
```bash
cd /home/mine/workspace/MalAPI_system/backend
python scripts/maintenance/import_attack.py
```

导入脚本使用 `INSERT OR IGNORE`，不会影响现有数据。

## 相关文件

| 文件 | 用途 |
|------|------|
| `scripts/init_database.sh` | 数据库初始化脚本（由 start_dev.sh 调用）|
| `scripts/start_dev.sh` | 开发服务启动脚本 |
| `scripts/maintenance/fix_attack_tables.py` | 修复 ATT&CK 表结构 |
| `scripts/maintenance/import_attack.py` | 导入 ATT&CK 基础数据 |
| `src/database/connection.py` | 数据库连接和初始化逻辑 |
| `src/database/models.py` | SQLAlchemy 模型定义 |
