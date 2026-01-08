# MalAPI System - 代理开发指南

本文档为参与MalAPI系统开发的AI代理提供关键信息，包括构建命令、代码风格指南和开发规范。

## 项目概述

MalAPI系统是一个恶意软件API分析平台，包含：
- **后端**: FastAPI + SQLAlchemy + PostgreSQL/SQLite
- **前端**: React + TypeScript + Ant Design
- **数据库**: PostgreSQL (生产) / SQLite (开发)
- **缓存**: Redis
- **容器化**: Docker + Docker Compose

## 构建和开发命令

### 环境管理
```bash
# 安装所有依赖
make install

# 设置开发环境
make setup-dev

# 快速启动（设置+安装+Docker）
make quick-start
```

### 开发服务
```bash
# 启动开发环境（前端+后端）
make dev

# 停止所有开发服务
make dev-stop

# 查看服务状态
make status
```

### 测试命令
```bash
# 运行所有测试
make test

# 仅运行后端测试
cd backend && python -m pytest tests/ -v

# 运行单个后端测试文件
cd backend && python -m pytest backend/scripts/tests/test_attack_api.py -v

# 运行前端测试
cd frontend && npm test -- --coverage --watchAll=false
```

### 代码质量检查
```bash
# 运行所有代码检查
make lint

# 后端代码检查
cd backend && flake8 src/ && mypy src/

# 前端代码检查
cd frontend && npm run lint

# 前端代码格式化
cd frontend && npm run format
```

### 构建和部署
```bash
# 构建生产版本
make build

# Docker相关
make docker-build
make docker-up
make docker-down
```

### 数据库操作
```bash
# 初始化数据库
make db-init

# 执行数据库迁移
make db-migrate

# 导入种子数据
make db-seed
```

## 代码风格指南

### Python (后端)

#### 导入顺序
```python
# 标准库导入
import os
import sys
from pathlib import Path
from typing import List, Optional

# 第三方库导入
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, Integer, String
import pytest

# 本地导入
from src.database.connection import get_async_session
from src.database.models import MalAPIFunction
from src.utils.logger import setup_logger
```

#### 命名约定
- **类名**: PascalCase (例: `MalAPIFunction`, `AttackTechnique`)
- **函数/变量名**: snake_case (例: `get_function_list`, `user_id`)
- **常量**: UPPER_SNAKE_CASE (例: `DEFAULT_PAGE_SIZE`, `MAX_REQUESTS`)
- **私有成员**: 前缀下划线 (例: `_internal_method`, `_cache_key`)

#### 文档字符串
```python
class FunctionResponse(BaseModel):
    """API函数响应模型
    
    用于返回函数基本信息和关联的ATT&CK技术映射。
    
    Attributes:
        id: 函数唯一标识符
        alias: 函数别名
        techniques: 关联的ATT&CK技术列表
    """
```

#### 错误处理
```python
# 使用HTTPException进行API错误处理
if not function:
    raise HTTPException(status_code=404, detail="Function not found")

# 使用logger记录错误
logger.error(f"Failed to retrieve function {function_id}: {str(e)}")

# 数据库异常处理
try:
    result = await session.execute(query)
    return result.scalars().all()
except Exception as e:
    logger.error(f"Database error: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

#### 类型注解
```python
from typing import List, Optional, Dict, Any

def get_functions(
    session: AsyncSession,
    technique_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> FunctionListResponse:
    """获取函数列表"""
    pass
```

### TypeScript (前端)

#### 导入顺序
```typescript
// React相关
import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';

// 第三方库
import { Card, Button, Table } from 'antd';
import axios from 'axios';

// 本地组件
import AppHeader from './components/Layout/AppHeader';
import { MalAPIFunction } from './types';

// 工具和样式
import { formatDate } from './utils/dateHelpers';
import './CodeViewer.css';
```

#### 组件定义
```typescript
interface CodeViewerProps {
  code: string;
  language?: string;
  title?: string;
  showLineNumbers?: boolean;
  maxHeight?: number;
}

const CodeViewer: React.FC<CodeViewerProps> = ({
  code,
  language = 'cpp',
  title,
  showLineNumbers = true,
  maxHeight = 600
}) => {
  // 组件实现
};
```

#### 命名约定
- **组件**: PascalCase (例: `CodeViewer`, `AttackMatrix`)
- **接口/类型**: PascalCase (例: `MalAPIFunction`, `ApiResponse`)
- **变量/函数**: camelCase (例: `handleClick`, `functionList`)
- **常量**: UPPER_SNAKE_CASE (例: `API_BASE_URL`, `DEFAULT_PAGE_SIZE`)

#### 状态管理
```typescript
// 使用useState进行状态管理
const [loading, setLoading] = useState(false);
const [functions, setFunctions] = useState<MalAPIFunction[]>([]);

// 异步数据获取
useEffect(() => {
  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await api.getFunctions();
      setFunctions(response.data);
    } catch (error) {
      message.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };
  
  fetchData();
}, []);
```

## 项目结构规范

### 后端目录结构
```
backend/
├── src/
│   ├── api/routes/          # API路由
│   ├── database/            # 数据库模型和连接
│   ├── services/            # 业务逻辑服务
│   ├── parsers/             # 数据解析器
│   ├── importers/           # 数据导入器
│   ├── utils/               # 工具函数
│   └── exceptions/          # 自定义异常
├── scripts/                 # 脚本文件
│   ├── tests/              # 测试文件
│   └── maintenance/        # 维护脚本
└── requirements.txt         # 依赖文件
```

### 前端目录结构
```
frontend/
├── src/
│   ├── components/         # 可复用组件
│   ├── pages/             # 页面组件
│   ├── services/          # API服务
│   ├── types/             # TypeScript类型定义
│   ├── utils/             # 工具函数
│   └── styles/            # 样式文件
├── public/                # 静态资源
└── package.json           # 依赖文件
```

## 数据库规范

### 模型定义
- 使用SQLAlchemy 2.0异步语法
- 所有表必须有`created_at`和`updated_at`字段
- 使用适当的索引优化查询性能
- 外键关系明确定义级联行为

### 查询优化
```python
# 使用selectinload预加载关联数据
query = select(MalAPIFunction).options(
    selectinload(MalAPIFunction.attck_mappings),
    selectinload(MalAPIFunction.children)
)

# 使用适当的索引
result = await session.execute(
    select(MalAPIFunction).where(
        MalAPIFunction.alias.like(f"%{search_term}%")
    ).limit(page_size)
)
```

## API设计规范

### RESTful API
- 使用标准HTTP方法 (GET, POST, PUT, DELETE)
- 统一的响应格式
- 适当的HTTP状态码
- API版本控制 (`/api/v1/`)

### 响应格式
```python
# 成功响应
{
    "success": true,
    "data": {...},
    "message": "操作成功"
}

# 错误响应
{
    "success": false,
    "error": "错误描述",
    "detail": "详细错误信息"
}
```

## 测试规范

### 后端测试
```python
# 使用pytest进行单元测试
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_function_list():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/functions/")
        assert response.status_code == 200
        assert "data" in response.json()
```

### 前端测试
```typescript
// 使用React Testing Library
import { render, screen, fireEvent } from '@testing-library/react';
import CodeViewer from './CodeViewer';

test('renders code viewer with copy functionality', () => {
  render(<CodeViewer code="test code" />);
  expect(screen.getByText('test code')).toBeInTheDocument();
});
```

## 安全注意事项

- 永远不要在代码中硬编码API密钥或密码
- 使用环境变量管理敏感配置
- 实施适当的输入验证和清理
- 遵循最小权限原则
- 定期更新依赖包

## 性能优化

### 后端
- 使用Redis缓存频繁查询的数据
- 实施数据库查询优化
- 使用异步操作处理I/O密集型任务
- 实施API限流和成本控制

### 前端
- 使用React.memo优化组件渲染
- 实施虚拟滚动处理大列表
- 使用懒加载减少初始包大小
- 优化图片和静态资源加载

## 日志和监控

### 日志规范
```python
# 使用结构化日志
logger.info("Function retrieved", extra={
    "function_id": function_id,
    "user_id": user_id,
    "duration_ms": duration
})

logger.error("Database operation failed", extra={
    "operation": "select_functions",
    "error": str(e)
})
```

### 监控指标
- API响应时间
- 数据库查询性能
- 错误率和异常统计
- 资源使用情况

## 部署和容器化

### Docker最佳实践
- 使用多阶段构建优化镜像大小
- 设置适当的健康检查
- 使用非root用户运行容器
- 实施适当的资源限制

### 环境配置
- 开发环境使用SQLite
- 生产环境使用PostgreSQL
- 使用Docker Compose管理服务依赖
- 实施适当的备份和恢复策略

---

**注意**: 本文档应随着项目演进持续更新。在修改代码结构或添加新功能时，请相应更新此指南。