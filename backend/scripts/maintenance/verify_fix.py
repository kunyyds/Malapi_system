"""
完整的数据库修复和验证流程

1. 修复 ATT&CK 表结构（使用 INTEGER 而不是 BIGINT）
2. 导入 ATT&CK 基础数据
3. 验证数据完整性
4. 验证 API 查询
"""
import sqlite3
import subprocess
from pathlib import Path

DB_PATH = Path("/home/mine/workspace/MalAPI_system/backend/malapi.db")


def check_table_structure():
    """检查表结构"""
    print("\n🔹 检查表结构")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(attack_tactics)")
    tactics_columns = cursor.fetchall()
    print(f"attack_tactics.id 类型: {tactics_columns[0][2]}")

    cursor.execute("PRAGMA table_info(attack_techniques)")
    techniques_columns = cursor.fetchall()
    print(f"attack_techniques.id 类型: {techniques_columns[0][2]}")

    conn.close()


def check_data():
    """检查数据"""
    print("\n🔹 检查数据")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM attack_tactics")
    tactics_count = cursor.fetchone()[0]
    print(f"attack_tactics: {tactics_count} 条")

    cursor.execute("SELECT COUNT(*) FROM attack_techniques")
    techniques_count = cursor.fetchone()[0]
    print(f"attack_techniques: {techniques_count} 条")

    cursor.execute("SELECT COUNT(*) FROM malapi_functions")
    functions_count = cursor.fetchone()[0]
    print(f"malapi_functions: {functions_count} 条")

    cursor.execute("SELECT COUNT(*) FROM attck_mappings")
    mappings_count = cursor.fetchone()[0]
    print(f"attck_mappings: {mappings_count} 条")

    # 测试 JOIN 查询
    print("\n🔹 测试 JOIN 查询")
    cursor.execute("""
        SELECT
            f.alias,
            at.technique_id,
            at.technique_name,
            att.tactic_name_en
        FROM malapi_functions f
        INNER JOIN attck_mappings am ON f.id = am.function_id
        INNER JOIN attack_techniques at ON am.technique_id = at.technique_id
        INNER JOIN attack_tactics att ON at.tactic_id = att.tactic_id
        LIMIT 3
    """)

    results = cursor.fetchall()
    if results:
        print("✓ JOIN 查询成功:")
        for row in results:
            print(f"  - {row[0]}: {row[1]} ({row[2]}) - {row[3]}")
    else:
        print("✗ JOIN 查询失败：没有结果")

    conn.close()


def test_api():
    """测试 API"""
    print("\n🔹 测试 API")
    try:
        import requests

        # 测试 stats API
        response = requests.get("http://localhost:8000/api/v1/admin/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✓ /api/v1/admin/stats: {stats}")
        else:
            print(f"✗ /api/v1/admin/stats 失败: {response.status_code}")

        # 测试 functions API
        response = requests.get("http://localhost:8000/api/v1/admin/functions")
        if response.status_code == 200:
            functions = response.json()
            print(f"✓ /api/v1/admin/functions: 返回 {len(functions)} 个函数")
            if functions:
                first_func = functions[0]
                tech_count = len(first_func.get('techniques', []))
                print(f"  第一个函数 '{first_func['alias']}' 有 {tech_count} 个技术映射")
                if tech_count > 0:
                    print(f"  示例: {first_func['techniques'][0]['technique_id']} - {first_func['techniques'][0]['technique_name']}")
        else:
            print(f"✗ /api/v1/admin/functions 失败: {response.status_code}")

    except ImportError:
        print("⚠ requests 模块未安装，跳过 API 测试")
    except Exception as e:
        print(f"✗ API 测试失败: {str(e)}")


def main():
    print("="*70)
    print("  MalAPI 数据库修复和验证")
    print("="*70)

    # 1. 修复表结构
    print("\n步骤1: 修复表结构")
    result = subprocess.run(
        ["conda", "run", "-n", "malapi-backend", "python", "fix_attack_tables.py"],
        cwd="/home/mine/workspace/MalAPI_system/backend",
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✓ 表结构修复成功")
    else:
        print(f"✗ 表结构修复失败: {result.stderr}")
        return False

    # 2. 导入 ATT&CK 数据
    print("\n步骤2: 导入 ATT&CK 数据")
    result = subprocess.run(
        ["conda", "run", "-n", "malapi-backend", "python", "backend/import_attack.py"],
        cwd="/home/mine/workspace/MalAPI_system",
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✓ ATT&CK 数据导入成功")
    else:
        print(f"✗ ATT&CK 数据导入失败: {result.stderr}")
        return False

    # 3. 检查数据
    check_data()

    # 4. 测试 API
    test_api()

    print("\n" + "="*70)
    print("✅ 修复和验证完成！")
    print("="*70)
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
