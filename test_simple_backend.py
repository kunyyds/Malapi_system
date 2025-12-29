#!/usr/bin/env python3
"""
简化版后端测试 - 不依赖数据库
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="MalAPI System - Test",
    description="测试版本",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "MalAPI System Test API",
        "version": "1.0.0",
        "status": "ok"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/test")
async def test_endpoint():
    return {
        "message": "测试成功",
        "backend": "正常工作",
        "cors": "已启用"
    }

if __name__ == "__main__":
    print("🚀 启动简化版后端服务...")
    print("📋 可用端点:")
    print("  - GET /")
    print("  - GET /health")
    print("  - GET /api/v1/test")
    print("🌐 服务地址: http://localhost:8000")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )