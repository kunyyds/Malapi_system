# Backend 目录结构说明

## 目录组织

```
backend/
├── docs/                           # 文档目录
│   ├── DATABASE_INIT.md           # 数据库初始化指南
│   ├── INSTALLATION_REPORT.md    # 安装报告
│   └── README_TESTING.md          # 测试文档
│
├── scripts/                       # 脚本目录
│   ├── maintenance/               # 维护脚本
│   │   ├── fix_attack_tables.py  # 修复 ATT&CK 表结构
│   │   ├── import_attack.py      # 导入 ATT&CK 数据
│   │   └── verify_fix.py         # 验证修复结果
│   ├── tests/                    # 测试脚本
│   │   ├── test_attck_parsing.py
│   │   ├── test_config.py
│   │   └── ...
│   ├── init_database.sh          # 数据库初始化（由 start_dev.sh 调用）
│   ├── setup_env.sh             # 环境设置
│   └── start_dev.sh              # 开发服务启动脚本
│
├── src/                          # 源代码目录
│   ├── api/                      # API 路由
│   ├── config/                   # 配置文件
│   ├── database/                 # 数据库模型和连接
│   ├── exceptions/               # 异常定义
│   ├── importers/                # 批量导入器
│   ├── llm/                      # LLM 服务
│   ├── parsers/                  # JSON 解析器
│   ├── scripts/                  # 代码脚本（已废弃，使用 scripts/ 目录）
│   ├── services/                 # 业务服务
│   ├── utils/                    # 工具函数
│   └── main.py                   # 应用入口
│
├── tests/                        # 单元测试目录
├── data/                         # 数据目录
├── logs/                        # 日志目录
├── malapi.db                    # SQLite 数据库文件
├── requirements.txt             # Python 依赖
└── environment.yml              # Conda 环境配置
```

## 维护脚本说明

### 数据库维护

| 脚本 | 用途 |
|------|------|
| `scripts/maintenance/fix_attack_tables.py` | 修复 ATT&CK 表结构（使用 INTEGER 而不是 BIGINT） |
| `scripts/maintenance/import_attack.py` | 从 matrix-enterprise.json 导入 ATT&CK 基础数据 |
| `scripts/maintenance/verify_fix.py` | 验证数据库修复结果 |

**使用方法**：
```bash
cd /home/mine/workspace/MalAPI_system/backend
python scripts/maintenance/import_attack.py
```

### 测试脚本

| 脚本 | 用途 |
|------|------|
| `scripts/tests/test_attck_parsing.py` | 测试 ATT&CK 字段解析 |
| `scripts/tests/test_config.py` | 测试配置 |
| `scripts/tests/test_data_processing.py` | 测试数据处理 |

**使用方法**：
```bash
cd /home/mine/workspace/MalAPI_system/backend
python scripts/tests/test_attck_parsing.py
```

## 快速开始

### 1. 首次安装

```bash
cd /home/mine/workspace/MalAPI_system/backend
./scripts/setup_env.sh        # 设置 conda 环境
./scripts/start_dev.sh        # 启动开发服务（会自动初始化数据库）
```

### 2. 删除数据库后重新初始化

```bash
rm malapi.db
./scripts/start_dev.sh        # 自动检测并初始化
```

### 3. 手动初始化数据库

```bash
./scripts/init_database.sh
```

### 4. 修复 ATT&CK 表

```bash
python scripts/maintenance/fix_attack_tables.py
python scripts/maintenance/import_attack.py
```

## 文件整理说明

### 移动的文件

**维护脚本** → `scripts/maintenance/`：
- `fix_attack_tables.py`
- `import_attack.py`
- `migrate_mappings.py`
- `verify_fix.py`

**测试文件** → `scripts/tests/`：
- `test_attck_parsing.py`
- `test_config.py`
- `test_data_processing.py`
- `test_data_processing_configured.py`
- `test_simple_scanner.py`

**文档文件** → `docs/`：
- `DATABASE_INIT.md`
- `INSTALLATION_REPORT.md`
- `README_TESTING.md`

### 删除的文件

**废弃的旧脚本** → `src/scripts/` (已删除整个目录):
- `import_attack_data.py` (已被 `scripts/maintenance/import_attack.py` 替代)
- `migrate_attack_refactor.py` (旧版本迁移脚本,不再需要)
- `migrate_database.py` (旧版本迁移脚本,不再需要)
- `migrate_sqlite.py` (旧版本迁移脚本,不再需要)

## 更新日志

- **2025-12-26 18:36**: 删除废弃的 `src/scripts/` 目录及其旧脚本
- **2025-12-26 18:30**: 重新组织目录结构，将脚本、测试和文档分类存放
- **2025-12-26 18:30**: 更新所有脚本和文档中的路径引用
- **2025-12-26 18:30**: 创建 README.md 说明新的目录结构
