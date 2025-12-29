#!/usr/bin/env python3
"""
MalAPI系统简化版主应用
仅用于测试基础功能，不依赖数据库
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 MalAPI后端服务启动中...")

    # 启动时执行
    try:
        logger.info("✅ 服务启动完成")
        yield
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        raise
    finally:
        logger.info("🛑 MalAPI后端服务关闭中...")


# 创建FastAPI应用实例
app = FastAPI(
    title="MalAPI System",
    description="恶意软件API管理和分析系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径 - 服务信息"""
    return {
        "message": "MalAPI System API",
        "version": "1.0.0",
        "status": "running",
        "description": "恶意软件API管理和分析系统",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "api": "/api/v1/",
            "test": "/api/v1/test"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": "2024-12-19T00:00:00Z",
        "version": "1.0.0",
        "environment": os.getenv("DEBUG", "false")
    }


@app.get("/api/v1/test")
async def test_endpoint():
    """测试端点 - 验证API基本功能"""
    return {
        "message": "测试成功",
        "backend": "FastAPI正常运行",
        "cors": "CORS已启用",
        "async": "异步端点正常",
        "features": {
            "fastapi": "✅",
            "cors": "✅",
            "async": "✅",
            "logging": "✅"
        }
    }


@app.get("/api/v1/info")
async def system_info():
    """系统信息端点"""
    return {
        "system": {
            "name": "MalAPI System",
            "version": "1.0.0",
            "environment": "development" if os.getenv("DEBUG") == "true" else "production",
            "python_version": "3.11",
            "framework": "FastAPI",
            "database": "SQLite (开发环境)"
        },
        "features": [
            "恶意软件API管理",
            "ATT&CK矩阵分析",
            "LLM智能分析",
            "实时搜索",
            "可视化展示"
        ],
        "api_endpoints": [
            "/api/v1/functions",
            "/api/v1/attack-matrix",
            "/api/v1/search",
            "/api/v1/analyze",
            "/api/v1/statistics"
        ]
    }


@app.get("/api/v1/status")
async def detailed_status():
    """详细状态检查"""
    components = {
        "api": {"status": "healthy", "details": "FastAPI运行正常"},
        "cors": {"status": "configured", "details": "CORS已配置"},
        "logging": {"status": "active", "details": "日志系统正常"},
        "async": {"status": "operational", "details": "异步处理正常"},
        "middleware": {"status": "loaded", "details": "中间件已加载"}
    }

    overall_status = "healthy" if all(c["status"] == "healthy" or c["status"] == "configured" or c["status"] == "active" or c["status"] == "operational" or c["status"] == "loaded" for c in components.values()) else "unhealthy"

    return {
        "overall_status": overall_status,
        "timestamp": "2024-12-19T00:00:00Z",
        "components": components,
        "uptime": "刚刚启动"
    }


# 异常处理器
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404错误处理"""
    return {
        "error": "Not Found",
        "message": f"路径 {request.url.path} 不存在",
        "available_endpoints": [
            "/",
            "/health",
            "/api/v1/test",
            "/api/v1/info",
            "/api/v1/status",
            "/docs"
        ]
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """500错误处理"""
    logger.error(f"内部服务器错误: {exc}")
    return {
        "error": "Internal Server Error",
        "message": "服务器内部错误，请稍后重试",
        "timestamp": "2024-12-19T00:00:00Z"
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 MalAPI后端服务启动")
    print("📋 可用端点:")
    print("  - GET /")
    print("  - GET /health")
    print("  - GET /api/v1/test")
    print("  - GET /api/v1/info")
    print("  - GET /api/v1/status")
    print("  - GET /docs (API文档)")
    print("🌐 服务地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")

    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )