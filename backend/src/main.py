"""
MalAPI系统后端主应用
FastAPI应用程序入口点
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from src.api.routes import functions, analysis, search, admin, attack
from src.database.connection import init_db
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("正在启动MalAPI后端服务...")
    await init_db()
    logger.info("数据库初始化完成")

    yield

    # 关闭时执行
    logger.info("正在关闭MalAPI后端服务...")


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title="MalAPI System",
        description="恶意软件API管理和分析系统",
        version="1.0.0",
        lifespan=lifespan
    )

    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Page", "X-Page-Size", "X-Total-Pages"],
    )

    # 注册路由
    app.include_router(functions.router, prefix="/api/v1/functions", tags=["functions"])
    app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
    app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
    app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
    app.include_router(attack.router, prefix="/api/v1/attack", tags=["ATT&CK"])

    # 根路径
    @app.get("/")
    async def root():
        return {
            "message": "MalAPI System API",
            "version": "1.0.0",
            "docs": "/docs"
        }

    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"全局异常: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"error": "内部服务器错误", "detail": str(exc)}
        )

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )