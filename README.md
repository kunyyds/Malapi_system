# MalAPI System

恶意软件API管理和分析系统

## 项目概述

MalAPI系统是一个专业的恶意软件API管理平台，基于ATT&CK框架提供可视化展示、智能分析和安全研究功能。

### 核心功能

- 🎯 **ATT&CK矩阵可视化** - 热力图展示恶意软件技术分布
- 🔍 **智能搜索** - 支持函数名、代码内容、ATT&CK技术的全文搜索
- 🤖 **AI分析** - 基于大语言模型的代码解释和攻击方案生成
- 📊 **数据管理** - MalFocus数据解析、存储和管理
- 🛡️ **安全研究** - 为安全研究提供专业的分析工具

## 技术架构

### 后端技术栈
- **框架**: Python FastAPI
- **数据库**: PostgreSQL + Redis
- **ORM**: SQLAlchemy
- **LLM集成**: OpenAI API / 本地模型

### 前端技术栈
- **框架**: React 18 + TypeScript
- **UI库**: Ant Design
- **可视化**: ECharts
- **构建工具**: Create React App

## 快速开始

### 环境要求

- Node.js 18+ (开发环境)
- Python 3.11+ (开发环境)
- Conda (Miniconda或Anaconda)
- SQLite (开发环境默认)

### 三步快速启动

1. **安装Conda环境**
```bash
cd backend
bash scripts/setup_env.sh
```

2. **启动后端服务**
```bash
bash scripts/start_dev.sh
```

3. **启动前端服务**
```bash
# 新开一个终端
cd frontend
npm install  # 首次运行
npm start
```

访问 http://localhost:3000 开始使用！

### 开发环境启动（推荐）

#### 方法一：使用Make命令（推荐）

```bash
# 安装依赖并启动开发环境
make dev

# 或分步执行
make install        # 安装所有依赖
make dev           # 启动开发环境

# 停止开发环境
make dev-stop      # 停止前后端服务
make all-stop      # 停止所有服务（包括Docker）
```

#### 方法二：手动启动

**后端开发：**

```bash
cd backend

# 1. 设置Conda环境（首次运行）
bash scripts/setup_env.sh

# 2. 激活Conda环境
conda activate malapi-backend

# 3. 启动开发服务器
bash scripts/start_dev.sh
```

启动脚本会自动：
- 检查并激活conda环境
- 初始化SQLite数据库
- 检查端口占用（默认8000）
- 启动FastAPI服务（支持热重载）
- 提供API文档访问地址

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

前端服务将运行在 http://localhost:3000

#### 服务验证

启动成功后，可以访问：
- 前端界面: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs
- 交互式API文档（Swagger）: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc

## 项目结构

```
MalAPI_system/
├── backend/                 # 后端服务
│   ├── src/
│   │   ├── api/            # API路由
│   │   ├── database/       # 数据库模型
│   │   ├── parsers/        # 数据解析器
│   │   ├── llm/           # LLM集成
│   │   ├── services/       # 业务逻辑
│   │   └── utils/         # 工具函数
│   ├── scripts/           # 开发脚本
│   │   ├── setup_env.sh   # 环境设置
│   │   ├── start_dev.sh   # 启动开发服务器
│   │   ├── init_database.sh # 数据库初始化
│   │   └── maintenance/   # 维护脚本
│   ├── tests/
│   ├── environment.yml    # Conda环境配置
│   └── requirements.txt   # Python依赖
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/    # React组件
│   │   ├── pages/         # 页面组件
│   │   ├── services/      # API服务
│   │   └── utils/         # 工具函数
│   ├── public/
│   └── package.json       # Node依赖
├── files/                 # 数据文件
├── Makefile               # 构建命令
└── README.md
```

## 常用Make命令

项目提供了便捷的Make命令来管理开发流程：

```bash
# 环境管理
make help              # 查看所有可用命令
make setup-dev         # 设置开发环境配置文件

# 依赖管理
make install           # 安装所有依赖（前端+后端）

# 开发服务
make dev               # 启动开发环境（前端+后端）
make dev-stop          # 停止开发环境
make all-stop          # 停止所有服务

# 代码质量
make test              # 运行所有测试
make lint              # 代码检查
make clean             # 清理临时文件

# 构建部署
make build             # 构建生产版本

# 数据库管理
make db-init           # 初始化数据库
make db-migrate        # 执行数据库迁移
make db-seed           # 导入种子数据

# 数据导入
make import-data       # 导入MalFocus数据

# API文档
make docs              # 显示API文档地址

# 监控
make status            # 查看服务状态
```

## API文档

启动后端服务后，可以访问以下文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要接口

- `GET /api/v1/functions` - 获取函数列表
- `GET /api/v1/functions/{id}` - 获取函数详情
- `GET /api/v1/functions/attack-matrix` - 获取ATT&CK矩阵数据
- `GET /api/v1/search` - 搜索函数
- `POST /api/v1/analysis/code` - 代码分析
- `POST /api/v1/analysis/attack-plan` - 生成攻击方案

## 数据导入

系统支持从MalFocus解析结果导入数据：

```bash
# 在后端目录执行
python -m src.parsers.importer --path /path/to/malfocus/results
```

## 配置说明

### 后端配置

首次运行 `scripts/setup_env.sh` 时会自动创建 `backend/.env` 文件。主要配置项：

```env
# 应用配置
DEBUG=true
APP_NAME=MalAPI System
VERSION=1.0.0

# 数据库配置 - 开发环境使用SQLite
DATABASE_URL=sqlite+aiosqlite:///./malapi.db

# Redis配置（可选）
REDIS_URL=redis://localhost:6379

# LLM配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# 文件路径配置
FILES_BASE_PATH=/home/mine/workspace/MalAPI_system/files

# 缓存配置
CACHE_TTL_SECONDS=3600
LLM_CACHE_TTL_HOURS=24

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=malapi.log

# API配置
API_PREFIX=/api/v1
MAX_REQUEST_SIZE=10485760

# 分页配置
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100

# 成本控制配置
DAILY_LLM_BUDGET=100.0
COST_PER_TOKEN_GPT4=0.00003
COST_PER_TOKEN_GPT35=0.000002
```

### 前端配置

在 `frontend/.env` 文件中配置：

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENV=development
```

### Conda环境管理

后端使用Conda进行环境管理：

```bash
# 创建环境（首次运行）
cd backend
bash scripts/setup_env.sh

# 激活环境
conda activate malapi-backend

# 退出环境
conda deactivate

# 删除并重建环境
conda env remove -n malapi-backend -y
bash scripts/setup_env.sh
```

环境配置文件：`backend/environment.yml`

## 开发指南

### 故障排除

**问题1：端口被占用**
```bash
# 查找占用8000端口的进程
lsof -ti:8000

# 终止进程
lsof -ti:8000 | xargs kill -9

# 或使用make命令
make dev-stop
```

**问题2：Conda环境激活失败**
```bash
# 初始化conda
conda init bash

# 重新加载shell配置
source ~/.bashrc

# 重新创建环境
cd backend
conda env remove -n malapi-backend -y
bash scripts/setup_env.sh
```

**问题3：数据库初始化失败**
```bash
# 删除现有数据库
cd backend
rm -f malapi.db

# 重新初始化
bash scripts/init_database.sh
```

**问题4：前端无法连接后端**
- 检查后端是否正常运行：访问 http://localhost:8000/docs
- 检查前端配置文件 `frontend/.env` 中的 `REACT_APP_API_URL`
- 确保后端CORS配置允许前端地址

### 开发指南

### 添加新的API接口

1. 在 `backend/src/api/routes/` 下创建路由文件
2. 在 `backend/src/database/models.py` 中定义数据模型
3. 更新 `backend/src/main.py` 注册新路由

### 添加新的前端页面

1. 在 `frontend/src/pages/` 下创建页面组件
2. 在 `frontend/src/components/` 下创建可复用组件
3. 更新 `frontend/src/App.tsx` 添加路由

### 数据库管理

项目使用SQLite作为开发数据库，启动脚本会自动初始化数据库。

**手动数据库操作：**

```bash
# 查看数据库状态
sqlite3 backend/malapi.db ".tables"

# 数据库初始化
cd backend
bash scripts/init_database.sh

# 数据库迁移（如果使用Alembic）
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

**数据库文件位置：**
- 开发环境：`backend/malapi.db`
- 数据目录：`backend/data/`

## 部署

### 生产环境部署

1. 配置生产环境变量
2. 构建前端项目
3. 配置反向代理（Nginx）
4. 使用进程管理工具（如systemd、supervisor）管理后端服务
5. 启用SSL证书
6. 配置监控和日志

## 性能优化

- 数据库查询优化和索引设计
- Redis缓存策略
- 前端代码分割和懒加载
- API响应压缩
- CDN静态资源加速

## 安全考虑

- API访问控制
- 数据加密存储
- 输入验证和SQL注入防护
- XSS防护
- CSRF防护
- 安全审计日志

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者: [您的姓名]
- 邮箱: [您的邮箱]
- 项目链接: [项目地址]

## 更新日志

### v1.0.0 (2024-12-19)
- ✅ 初始版本发布
- ✅ ATT&CK矩阵可视化
- ✅ 基础搜索功能
- ✅ 代码分析功能

---

⚠️ **免责声明**: 本系统仅用于安全研究和防御目的，请勿用于恶意攻击。使用者需要遵守相关法律法规。