"""
从matrix-enterprise.json导入ATT&CK基础数据

使用方法:
    cd backend
    conda activate malapi-backend
    python scripts/maintenance/import_attack.py
"""
import sqlite3
import json
from pathlib import Path

# 数据库和JSON文件路径（相对于脚本位置）
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

DB_PATH = BACKEND_DIR / "malapi.db"
JSON_PATH = PROJECT_ROOT / "matrix-enterprise.json"


def import_attack_data():
    """导入ATT&CK数据到数据库"""

    print("="*60)
    print("  MalAPI - ATT&CK数据导入工具")
    print("="*60)

    # 检查文件是否存在
    if not JSON_PATH.exists():
        print(f"❌ 错误: JSON文件不存在 {JSON_PATH}")
        return False

    if not DB_PATH.exists():
        print(f"❌ 错误: 数据库文件不存在 {DB_PATH}")
        return False

    print(f"\n📖 读取文件: {JSON_PATH}")

    # 读取JSON文件
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        matrix_data = json.load(f)

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # 步骤1: 导入tactics
        print("\n🔹 步骤1: 导入tactics")
        tactic_count = 0
        for tactic_id, tactic_data in matrix_data.items():
            cursor.execute("""
                INSERT OR IGNORE INTO attack_tactics
                (tactic_id, tactic_name_en, tactic_name_cn)
                VALUES (?, ?, ?)
            """, (tactic_id, tactic_data['tactic_name_en'], tactic_data['tactic_name_cn']))
            tactic_count += 1

        conn.commit()
        print(f"✓ 导入tactics: {tactic_count} 条")

        # 步骤2: 导入techniques和sub-techniques
        print("\n🔹 步骤2: 导入techniques")
        technique_count = 0
        sub_technique_count = 0

        for tactic_id, tactic_data in matrix_data.items():
            for technique_group in tactic_data['techniques']:
                # 找到父技术ID和名称
                parent_id = None
                parent_name = None
                for key, value in technique_group.items():
                    if key == 'sub':
                        continue
                    parent_id = key
                    parent_name = value
                    break

                if not parent_id:
                    continue

                # 插入父技术
                cursor.execute("""
                    INSERT OR IGNORE INTO attack_techniques
                    (technique_id, technique_name, tactic_id, is_sub_technique, data_source)
                    VALUES (?, ?, ?, 0, 'matrix_enterprise')
                """, (parent_id, parent_name, tactic_id))
                technique_count += 1

                # 插入子技术
                if 'sub' in technique_group:
                    for sub_technique in technique_group['sub']:
                        for sub_id, sub_name in sub_technique.items():
                            cursor.execute("""
                                INSERT OR IGNORE INTO attack_techniques
                                (technique_id, technique_name, tactic_id, is_sub_technique, parent_technique_id, data_source)
                                VALUES (?, ?, ?, 1, ?, 'matrix_enterprise')
                            """, (sub_id, sub_name, tactic_id, parent_id))
                            sub_technique_count += 1

        conn.commit()
        print(f"✓ 导入父techniques: {technique_count} 条")
        print(f"✓ 导入子techniques: {sub_technique_count} 条")

        # 步骤3: 验证导入结果
        print("\n🔹 步骤3: 验证导入结果")

        cursor.execute("SELECT COUNT(*) FROM attack_tactics")
        total_tactics = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM attack_techniques")
        total_techniques = cursor.fetchone()[0]

        print(f"\n{'='*50}")
        print(f"📊 导入完成统计")
        print(f"{'='*50}")
        print(f"Tactics（战术）: {total_tactics} 条")
        print(f"Techniques（父技术）: {technique_count} 条")
        print(f"Sub-techniques（子技术）: {sub_technique_count} 条")
        print(f"总计Techniques: {total_techniques} 条")
        print(f"{'='*50}")

        # 显示前5条数据示例
        print("\n📋 数据示例:")
        cursor.execute("SELECT tactic_id, tactic_name_en, tactic_name_cn FROM attack_tactics LIMIT 3")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} ({row[2]})")

        cursor.execute("""
            SELECT technique_id, technique_name, is_sub_technique
            FROM attack_techniques
            ORDER BY is_sub_technique, technique_id
            LIMIT 5
        """)
        print("\nTechniques示例:")
        for row in cursor.fetchall():
            sub_mark = "  └─" if row[2] else "●"
            print(f"  {sub_mark} {row[0]}: {row[1]}")

        print(f"\n{'='*50}")
        print("✅ 数据导入成功完成!")
        print(f"{'='*50}")

        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = import_attack_data()
    exit(0 if success else 1)
