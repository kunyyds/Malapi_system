#!/bin/bash
# MalAPI后端环境设置脚本

set -e  # 遇到错误立即退出

echo "🚀 设置MalAPI后端开发环境..."

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查conda是否安装
if ! command -v conda &> /dev/null; then
    echo -e "${RED}❌ Conda未安装，请先安装Miniconda或Anaconda${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Conda已安装${NC}"

# 接受conda terms of service
echo "📋 接受Conda服务条款..."
conda tos accept --override-channels

# 检查环境是否已存在
if conda env list | grep -q "malapi-backend"; then
    echo -e "${YELLOW}⚠️  malapi-backend环境已存在${NC}"
    read -p "是否要删除并重建环境？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  删除现有环境..."
        conda env remove -n malapi-backend -y
    else
        echo "✅ 使用现有环境"
        conda activate malapi-backend
        exit 0
    fi
fi

# 创建conda环境
echo "📦 创建conda环境..."
conda env create -f environment.yml

# 激活环境
echo "🔧 激活环境..."
eval "$(conda shell.bash hook)"
conda activate malapi-backend

# 验证安装
echo "🔍 验证核心依赖安装..."
python -c "
import fastapi, uvicorn, sqlalchemy, psycopg2, redis, pydantic
import pytest, black, isort, flake8, mypy
import asyncpg, httpx, aiohttp, openai
print('✅ 所有核心依赖安装成功')
"

# 创建必要的目录
echo "📁 创建项目目录..."
mkdir -p logs
mkdir -p data
mkdir -p temp

# 设置环境变量文件
if [ ! -f ".env" ]; then
    echo "📝 创建.env文件..."
    cp .env.example .env 2>/dev/null || cat > .env << EOF
# 应用配置
DEBUG=true
APP_NAME=MalAPI System
VERSION=1.0.0

# 数据库配置 - 使用SQLite进行开发
DATABASE_URL=sqlite+aiosqlite:///./malapi.db

# Redis配置
REDIS_URL=redis://localhost:6379

# 文件路径配置
FILES_BASE_PATH=/home/mine/workspace/MalAPI_system/files

# LLM配置 - 请替换为您的实际API密钥
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

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
EOF
fi

echo -e "${GREEN}🎉 环境设置完成！${NC}"
echo -e "${YELLOW}💡 使用方法：${NC}"
echo "  激活环境: conda activate malapi-backend"
echo "  启动服务: ./scripts/start_dev.sh"
echo "  运行测试: pytest"
echo "  代码格式化: black src/"
echo "  代码检查: flake8 src/"