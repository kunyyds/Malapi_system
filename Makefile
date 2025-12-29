.PHONY: help install dev build test clean docker-build docker-up docker-down lint

# 默认目标
help:
	@echo "MalAPI System - 可用命令:"
	@echo ""
	@echo "  install     安装所有依赖"
	@echo "  dev         启动开发环境"
	@echo "  build       构建生产版本"
	@echo "  test        运行测试"
	@echo "  lint        代码检查"
	@echo "  clean       清理临时文件"
	@echo ""
	@echo "Docker命令:"
	@echo "  docker-build 构建Docker镜像"
	@echo "  docker-up   启动Docker服务"
	@echo "  docker-down 停止Docker服务"
	@echo "  docker-logs 查看Docker日志"
	@echo "  docker-shell 进入后端容器"
	@echo ""
	@echo "数据库命令:"
	@echo "  db-init     初始化数据库"
	@echo "  db-migrate  执行数据库迁移"
	@echo "  db-seed     导入种子数据"

# 安装依赖
install:
	@echo "📦 安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "📦 安装前端依赖..."
	cd frontend && npm install
	@echo "✅ 依赖安装完成"

# 开发环境
dev:
	@echo "🚀 启动开发环境..."
# 	docker-compose up -d postgres redis
	@echo "⚡ 启动后端服务..."
	cd backend && bash ./scripts/start_dev.sh &
	@echo "⚡ 启动前端服务..."
	cd frontend && npm start &
	@echo "✅ 开发环境已启动"
	@echo "🌐 前端: http://localhost:3000"
	@echo "🔧 后端: http://localhost:8000"

# 生产构建
build:
	@echo "🏗️ 构建生产版本..."
	@echo "📦 构建前端..."
	cd frontend && npm run build
	@echo "✅ 构建完成"

# 运行测试
test:
	@echo "🧪 运行后端测试..."
	cd backend && python -m pytest tests/ -v
	@echo "🧪 运行前端测试..."
	cd frontend && npm test -- --coverage --watchAll=false

# 代码检查
lint:
	@echo "🔍 检查后端代码..."
	cd backend && flake8 src/ && mypy src/
	@echo "🔍 检查前端代码..."
	cd frontend && npm run lint

# 清理
clean:
	@echo "🧹 清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	cd frontend && rm -rf build/ node_modules/.cache/
	@echo "✅ 清理完成"

# Docker相关命令
docker-build:
	@echo "🐳 构建Docker镜像..."
	docker-compose build

docker-up:
	@echo "🐳 启动Docker服务..."
	docker-compose up -d
	@echo "✅ 服务已启动"
	docker-compose ps

docker-down:
	@echo "🐳 停止Docker服务..."
	docker-compose down

docker-logs:
	@echo "📋 查看Docker日志..."
	docker-compose logs -f

docker-shell:
	@echo "🐚 进入后端容器..."
	docker-compose exec backend bash

# 数据库相关命令
db-init:
	@echo "🗄️ 初始化数据库..."
	docker-compose exec postgres psql -U malapi_user -d malapi -f /docker-entrypoint-initdb.d/01-schema.sql

db-migrate:
	@echo "🔄 执行数据库迁移..."
	cd backend && alembic upgrade head

db-seed:
	@echo "🌱 导入种子数据..."
	cd backend && python -m src.parsers.data_importer

# 开发工具命令
setup-dev:
	@echo "⚙️ 设置开发环境..."
	cp backend/.env.example backend/.env
	cp frontend/.env.example frontend/.env
	@echo "📝 请编辑配置文件:"
	@echo "  - backend/.env"
	@echo "  - frontend/.env"

# 数据导入命令
import-data:
	@echo "📥 导入MalFocus数据..."
	cd backend && python -m src.parsers.malfocus_parser

# API文档生成
docs:
	@echo "📚 生成API文档..."
	cd backend && python -c "from src.main import app; print('API文档地址: http://localhost:8000/docs')"

# 监控命令
status:
	@echo "📊 服务状态:"
	@echo "Docker服务:"
	docker-compose ps
	@echo ""
	@echo "端口占用:"
	@echo "前端 (3000):" && lsof -ti:3000 || echo "未运行"
	@echo "后端 (8000):" && lsof -ti:8000 || echo "未运行"
	@echo "数据库 (5432):" && lsof -ti:5432 || echo "未运行"
	@echo "Redis (6379):" && lsof -ti:6379 || echo "未运行"

# 快速启动命令
quick-start: setup-dev install docker-up
	@echo "🚀 快速启动完成!"
	@echo "🌐 前端: http://localhost:3000"
	@echo "🔧 后端: http://localhost:8000"
	@echo "📚 API文档: http://localhost:8000/docs"

# 重置环境
reset: clean docker-down
	@echo "🔄 重置环境..."
	docker system prune -f
	docker volume prune -f
	@echo "✅ 环境重置完成"

# 终止所有开发环境服务（前端+后端+Docker依赖）
dev-stop:
	@echo "🛑 开始终止所有开发环境服务..."
	@echo "1. 终止前端服务（3000端口）..."
#	# 查找并终止占用3000端口的进程（前端默认端口）
	if lsof -ti:3000 > /dev/null; then \
		lsof -ti:3000 | xargs kill -9; \
		echo "✅ 前端服务已终止"; \
	else \
		echo "ℹ️ 前端服务未运行"; \
	fi

	@echo "2. 终止后端服务(8000端口 + start_dev.sh进程)..."
#	# 方式1：通过后端默认8000端口终止
	if lsof -ti:8000 > /dev/null; then \
		lsof -ti:8000 | xargs kill -9; \
		echo "✅ 后端服务(端口8000)已终止"; \
	else \
		echo "ℹ️ 后端服务(端口8000)未运行"; \
	fi
# 	# 方式2：通过start_dev.sh脚本进程名兜底终止（防止端口占用异常）
# 	if pgrep -f "backend/scripts/start_dev.sh" > /dev/null; then \
# 		pgrep -f "backend/scripts/start_dev.sh" | xargs kill -9; \
# 		echo "✅ 后端start_dev.sh进程已终止"; \
# 	else \
# 		echo "ℹ️ 后端start_dev.sh进程未运行"; \
# 	fi

	@echo "3. 终止Docker依赖服务(postgres/redis)..."
#	# 停止dev目标中可能启动的Docker服务（若注释开启则生效）
	if docker-compose ps | grep -E "postgres|redis" | grep -q "Up"; then \
		docker-compose stop postgres redis; \
		echo "✅ Docker postgres/redis服务已终止"; \
	else \
		echo "ℹ️ Docker postgres/redis服务未运行"; \
	fi

	@echo "4. 清理临时进程残留..."
#	# 清理后台僵尸进程（可选，避免残留）
	wait 2>/dev/null || true
	@echo "✅ 所有开发环境服务已终止完成！"

# （可选）全环境终止命令（含Docker生产服务）
all-stop: dev-stop docker-down
	@echo "🔚 全环境服务(开发+Docker生产)已全部终止!"