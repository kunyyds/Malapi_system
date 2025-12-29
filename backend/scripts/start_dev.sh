#!/usr/bin/bash
# MalAPI后端开发服务启动脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 启动MalAPI后端开发服务...${NC}"

# 激活conda环境
echo "🔧 激活conda环境..."
eval "$(conda shell.bash hook)"
if ! conda activate malapi-backend 2>/dev/null; then
    echo -e "${RED}❌ 无法激活malapi-backend环境${NC}"
    echo "请先运行: ./scripts/setup_env.sh"
    exit 1
fi

echo -e "${GREEN}✅ Conda环境已激活${NC}"

# 检查Python版本
python_version=$(python --version 2>&1 | cut -d' ' -f2)
echo "🐍 Python版本: $python_version"

# 设置环境变量
export DATABASE_URL="sqlite+aiosqlite:///./malapi.db"
export DEBUG=true
export LOG_LEVEL="info"

# 检查必要文件
if [ ! -f "src/main.py" ]; then
    echo -e "${RED}❌ 找不到 src/main.py 文件${NC}"
    echo "请确保在backend目录下运行此脚本"
    exit 1
fi

# 创建日志目录
mkdir -p logs
mkdir -p data

# 初始化数据库
echo -e "${BLUE}🔍 检查并初始化数据库...${NC}"
if [ -f "scripts/init_database.sh" ]; then
    bash scripts/init_database.sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 数据库初始化失败${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  未找到数据库初始化脚本，跳过${NC}"
fi

# 检查端口是否被占用
PORT=8000
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 $PORT 已被占用${NC}"
    read -p "是否要终止占用进程并继续？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 终止占用进程..."
        lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo -e "${RED}❌ 启动取消${NC}"
        exit 1
    fi
fi

# 显示启动信息
echo ""
echo -e "${BLUE}📋 服务信息:${NC}"
echo "  🌐 服务地址: http://localhost:$PORT"
echo "  📚 API文档: http://localhost:$PORT/docs"
echo "  🔄 自动重载: 已启用"
echo "  🗄️  数据库: SQLite (开发环境)"
echo "  📝 日志级别: $LOG_LEVEL"
echo ""

# 启动服务
echo -e "${GREEN}🚀 启动FastAPI服务...${NC}"
echo -e "${YELLOW}💡 按 Ctrl+C 停止服务${NC}"
echo ""

# 设置信号处理
trap 'echo -e "\n${YELLOW}🛑 正在停止服务...${NC}"; exit 0' INT

# 启动uvicorn
uvicorn src.main:app \
    --reload \
    --host 0.0.0.0 \
    --port $PORT \
    --log-level $LOG_LEVEL \
    --access-log \
    --use-colors