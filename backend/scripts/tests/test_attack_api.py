"""
测试 ATT&CK API 功能

使用方法:
    cd backend
    conda activate malapi-backend
    python scripts/tests/test_attack_api.py
"""
import sys
from pathlib import Path

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent.absolute()  # backend/scripts/tests
BACKEND_DIR = SCRIPT_DIR.parent.parent  # backend
sys.path.insert(0, str(BACKEND_DIR))

import sqlite3
import json

# 数据库路径
DB_PATH = BACKEND_DIR / "malapi.db"


def test_data_integrity():
    """测试数据完整性"""
    print("=" * 60)
    print("测试 1: 数据完整性")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 检查战术
    cursor.execute("SELECT COUNT(*) FROM attack_tactics")
    tactics_count = cursor.fetchone()[0]
    print(f"✓ 战术数量: {tactics_count}")
    assert tactics_count == 14, f"期望 14 个战术，实际 {tactics_count}"

    # 检查技术
    cursor.execute("SELECT COUNT(*) FROM attack_techniques")
    techniques_count = cursor.fetchone()[0]
    print(f"✓ 技术总数: {techniques_count}")
    assert techniques_count == 691, f"期望 691 个技术，实际 {techniques_count}"

    # 检查 STIX 字段
    cursor.execute("SELECT COUNT(*) FROM attack_tactics WHERE stix_id IS NOT NULL")
    tactics_with_stix = cursor.fetchone()[0]
    print(f"✓ 战术包含 STIX ID: {tactics_with_stix}/{tactics_count}")

    cursor.execute("SELECT COUNT(*) FROM attack_techniques WHERE stix_id IS NOT NULL")
    tech_with_stix = cursor.fetchone()[0]
    print(f"✓ 技术包含 STIX ID: {tech_with_stix}/{techniques_count}")

    # 检查平台字段
    cursor.execute("SELECT COUNT(*) FROM attack_techniques WHERE platforms IS NOT NULL")
    tech_with_platforms = cursor.fetchone()[0]
    print(f"✓ 技术包含平台信息: {tech_with_platforms}/{techniques_count}")

    # 检查 MITRE URL
    cursor.execute("SELECT COUNT(*) FROM attack_techniques WHERE mitre_url IS NOT NULL")
    tech_with_url = cursor.fetchone()[0]
    print(f"✓ 技术包含 MITRE URL: {tech_with_url}/{techniques_count}")

    conn.close()
    print("\n✅ 数据完整性测试通过!\n")


def test_sample_data():
    """测试示例数据"""
    print("=" * 60)
    print("测试 2: 示例数据质量")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 测试战术示例
    cursor.execute("""
        SELECT tactic_id, tactic_name_en, stix_id
        FROM attack_tactics
        WHERE tactic_id = 'defense-evasion'
    """)
    result = cursor.fetchone()
    if result:
        print(f"✓ 战术示例: {result[0]} - {result[1]}")
        print(f"  STIX ID: {result[2]}")

    # 测试技术示例
    cursor.execute("""
        SELECT technique_id, technique_name, mitre_url, platforms
        FROM attack_techniques
        WHERE technique_id = 'T1055'
    """)
    result = cursor.fetchone()
    if result:
        print(f"\n✓ 技术示例: {result[0]} - {result[1]}")
        print(f"  MITRE URL: {result[2]}")
        print(f"  平台: {result[3]}")

        # 验证 URL 格式
        assert 'attack.mitre.org' in result[2], "MITRE URL 格式不正确"

    # 测试子技术
    cursor.execute("""
        SELECT COUNT(*) FROM attack_techniques
        WHERE parent_technique_id = 'T1055'
    """)
    sub_count = cursor.fetchone()[0]
    print(f"\n✓ T1055 的子技术数量: {sub_count}")

    conn.close()
    print("\n✅ 示例数据质量测试通过!\n")


def test_api_imports():
    """测试 API 模块导入"""
    print("=" * 60)
    print("测试 3: API 模块导入")
    print("=" * 60)

    try:
        from src.api.routes import attack
        print("✓ attack 路由模块导入成功")

        from src.main import create_app
        print("✓ main 模块导入成功")

        # 创建应用
        app = create_app()
        print("✓ FastAPI 应用创建成功")

        # 检查路由
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and '/api/v1/attack' in route.path:
                routes.append(route.path)

        print(f"\n✓ 注册的 ATT&CK API 端点: {len(routes)} 个")
        for route in sorted(set(routes)):
            print(f"  - {route}")

        expected_routes = [
            '/api/v1/attack/tactics',
            '/api/v1/attack/techniques',
            '/api/v1/attack/matrix',
            '/api/v1/attack/statistics'
        ]

        for expected in expected_routes:
            # 检查是否有路由匹配
            found = any(expected.replace('{', '').replace('}', '') in r for r in routes)
            if found:
                print(f"✓ 找到预期路由: {expected}")

        print("\n✅ API 模块导入测试通过!\n")

    except Exception as e:
        print(f"\n✗ API 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  MalAPI - ATT&CK API 测试")
    print("=" * 60 + "\n")

    try:
        # 测试数据完整性
        test_data_integrity()

        # 测试示例数据
        test_sample_data()

        # 测试 API 导入
        if not test_api_imports():
            return False

        print("=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
