#!/usr/bin/env python3
"""
基础设施测试脚本
测试数据库、Redis和基础功能
"""

import subprocess
import time
import sys

def test_docker_services():
    """测试Docker服务状态"""
    print("🐳 测试Docker服务...")

    # 检查PostgreSQL
    try:
        result = subprocess.run(
            ["docker-compose", "exec", "-T", "postgres", "psql", "-U", "malapi_user", "-d", "malapi", "-c", "SELECT 1"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ PostgreSQL 连接正常")
        else:
            print("❌ PostgreSQL 连接失败")
            return False
    except Exception as e:
        print(f"❌ PostgreSQL 测试异常: {e}")
        return False

    # 检查Redis
    try:
        result = subprocess.run(
            ["docker-compose", "exec", "-T", "redis", "redis-cli", "ping"],
            capture_output=True,
            text=True
        )
        if "PONG" in result.stdout:
            print("✅ Redis 连接正常")
        else:
            print("❌ Redis 连接失败")
            return False
    except Exception as e:
        print(f"❌ Redis 测试异常: {e}")
        return False

    return True

def test_database_schema():
    """测试数据库schema"""
    print("🗄️ 测试数据库schema...")

    try:
        result = subprocess.run(
            ["docker-compose", "exec", "-T", "postgres", "psql", "-U", "malapi_user", "-d", "malapi", "-c", "\\dt"],
            capture_output=True,
            text=True
        )

        tables = ["malapi_functions", "attck_mappings", "function_children",
                 "malapi_metadata", "usage_statistics", "attack_plan_history"]

        for table in tables:
            if table in result.stdout:
                print(f"✅ 表 {table} 存在")
            else:
                print(f"❌ 表 {table} 不存在")
                return False

    except Exception as e:
        print(f"❌ Schema测试异常: {e}")
        return False

    return True

def test_file_structure():
    """测试项目文件结构"""
    print("📁 测试项目文件结构...")

    required_files = [
        "backend/src/main.py",
        "backend/requirements.txt",
        "backend/.env",
        "frontend/src/App.tsx",
        "frontend/package.json",
        "docker-compose.yml",
        "database/schema.sql"
    ]

    for file_path in required_files:
        try:
            with open(file_path, 'r') as f:
                pass
            print(f"✅ {file_path}")
        except FileNotFoundError:
            print(f"❌ {file_path} 不存在")
            return False
        except Exception as e:
            print(f"❌ {file_path} 访问异常: {e}")
            return False

    return True

def test_node_dependencies():
    """测试Node.js依赖"""
    print("📦 测试Node.js依赖...")

    try:
        result = subprocess.run(
            ["npm", "list", "--depth=0"],
            capture_output=True,
            text=True,
            cwd="frontend"
        )

        if result.returncode == 0:
            print("✅ 前端依赖安装完成")
            return True
        else:
            print("❌ 前端依赖有问题")
            return False
    except Exception as e:
        print(f"❌ Node依赖测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始基础设施测试\n")

    tests = [
        test_file_structure,
        test_docker_services,
        test_database_schema,
        test_node_dependencies
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()  # 空行分隔
        except Exception as e:
            print(f"❌ 测试执行异常: {e}\n")

    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有基础设施测试通过！")
        print("\n📋 下一步建议:")
        print("1. 启动后端服务: cd backend && uvicorn src.main:app --reload")
        print("2. 启动前端服务: cd frontend && npm start")
        print("3. 访问应用: http://localhost:3000")
        return True
    else:
        print("⚠️ 部分测试失败，请检查上述错误信息")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)