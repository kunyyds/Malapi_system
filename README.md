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
- **部署**: Docker

### 前端技术栈
- **框架**: React 18 + TypeScript
- **UI库**: Ant Design
- **可视化**: ECharts
- **构建工具**: Create React App

## 快速开始

### 环境要求

- Docker & Docker Compose
- Node.js 18+ (开发环境)
- Python 3.11+ (开发环境)

### 使用Docker启动（推荐）

1. 克隆项目
```bash
git clone <repository-url>
cd MalAPI_system
```

2. 配置环境变量
```bash
cp backend/.env.example backend/.env
# 编辑 .env 文件，配置数据库和LLM API密钥
```

3. 启动服务
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

4. 访问应用
- 前端界面: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 开发环境启动

#### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

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
│   ├── tests/
│   └── Dockerfile
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/    # React组件
│   │   ├── pages/         # 页面组件
│   │   ├── services/      # API服务
│   │   └── utils/         # 工具函数
│   ├── public/
│   └── Dockerfile
├── database/              # 数据库脚本
│   └── schema.sql
├── files/                 # 数据文件
├── docker-compose.yml
└── README.md
```

## API文档

启动后端服务后，访问 http://localhost:8000/docs 查看交互式API文档。

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

主要配置项在 `backend/.env` 文件中：

```env
# 数据库配置
DATABASE_URL=postgresql://user:pass@localhost:5432/malapi

# Redis配置
REDIS_URL=redis://localhost:6379

# LLM配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4

# 文件路径
FILES_BASE_PATH=/path/to/files
```

### 前端配置

在 `frontend/.env` 文件中配置：

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENV=development
```

## 开发指南

### 添加新的API接口

1. 在 `backend/src/api/routes/` 下创建路由文件
2. 在 `backend/src/database/models.py` 中定义数据模型
3. 更新 `backend/src/main.py` 注册新路由

### 添加新的前端页面

1. 在 `frontend/src/pages/` 下创建页面组件
2. 在 `frontend/src/components/` 下创建可复用组件
3. 更新 `frontend/src/App.tsx` 添加路由

### 数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

## 部署

### 生产环境部署

1. 使用生产配置启动服务
```bash
docker-compose -f docker-compose.prod.yml up -d
```

2. 配置反向代理（Nginx）
3. 启用SSL证书
4. 配置监控和日志

### 扩展部署

- 支持Kubernetes部署
- 支持云平台部署（AWS、Azure、GCP）
- 支持微服务架构

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
- ✅ Docker部署支持

---

⚠️ **免责声明**: 本系统仅用于安全研究和防御目的，请勿用于恶意攻击。使用者需要遵守相关法律法规。