"""
从 manifest_json 中提取 ATT&CK 映射并填充到 attck_mappings 表

问题:
- malapi_functions 表有 32 条记录
- manifest_json 字段包含 attck 数组,如 ["T1490", "T1480"]
- 但 attck_mappings 表为空

解决方案:
- 解析每个函数的 manifest_json
- 提取 attck 数组
- 验证 technique_id 存在于 attack_techniques 表
- 插入到 attck_mappings 表
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path("/home/mine/workspace/MalAPI_system/backend/malapi.db")


def populate_attck_mappings():
    """从 manifest_json 填充 ATT&CK 映射表"""

    print("=" * 70)
    print("  MalAPI - 从 manifest_json 填充 ATT&CK 映射表")
    print("=" * 70)

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # 步骤1: 检查当前状态
        print("\n🔹 步骤1: 检查当前数据状态")

        cursor.execute("SELECT COUNT(*) FROM malapi_functions")
        total_functions = cursor.fetchone()[0]
        print(f"✓ 总函数数: {total_functions}")

        cursor.execute("SELECT COUNT(*) FROM malapi_functions WHERE manifest_json IS NOT NULL")
        functions_with_manifest = cursor.fetchone()[0]
        print(f"✓ 有 manifest_json 的函数: {functions_with_manifest}")

        cursor.execute("SELECT COUNT(*) FROM attck_mappings")
        existing_mappings = cursor.fetchone()[0]
        print(f"✓ 现有 ATT&CK 映射: {existing_mappings}")

        cursor.execute("SELECT COUNT(*) FROM attack_techniques")
        total_techniques = cursor.fetchone()[0]
        print(f"✓ ATT&CK 技术总数: {total_techniques}")

        # 步骤2: 解析所有 manifest_json
        print("\n🔹 步骤2: 解析 manifest_json 并准备映射数据")

        cursor.execute("""
            SELECT id, alias, manifest_json
            FROM malapi_functions
            WHERE manifest_json IS NOT NULL
            ORDER BY id
        """)

        functions = cursor.fetchall()

        mappings_to_insert = []
        invalid_mappings = []
        parse_errors = []

        for func_id, alias, manifest_json in functions:
            try:
                data = json.loads(manifest_json)
                attck_list = data.get('attck', [])

                if attck_list and isinstance(attck_list, list):
                    for technique_id in attck_list:
                        technique_id = str(technique_id).strip().upper()

                        # 检查 technique_id 是否有效
                        cursor.execute("""
                            SELECT 1 FROM attack_techniques
                            WHERE technique_id = ?
                        """, (technique_id,))

                        if cursor.fetchone():
                            # 检查是否已存在
                            cursor.execute("""
                                SELECT 1 FROM attck_mappings
                                WHERE function_id = ? AND technique_id = ?
                            """, (func_id, technique_id))

                            if not cursor.fetchone():
                                mappings_to_insert.append({
                                    'function_id': func_id,
                                    'technique_id': technique_id,
                                    'alias': alias
                                })
                        else:
                            invalid_mappings.append({
                                'function_id': func_id,
                                'alias': alias,
                                'technique_id': technique_id
                            })

            except json.JSONDecodeError as e:
                parse_errors.append({
                    'function_id': func_id,
                    'alias': alias,
                    'error': str(e)
                })
            except Exception as e:
                parse_errors.append({
                    'function_id': func_id,
                    'alias': alias,
                    'error': str(e)
                })

        print(f"✓ 准备插入映射: {len(mappings_to_insert)} 条")
        print(f"✗ 无效的 technique_id: {len(invalid_mappings)} 条")
        print(f"✗ JSON 解析错误: {len(parse_errors)} 个")

        # 显示无效映射
        if invalid_mappings:
            print(f"\n无效的 technique_id (前10个):")
            for item in invalid_mappings[:10]:
                print(f"  - 函数 {item['function_id']} ({item['alias']}): {item['technique_id']}")

        # 显示解析错误
        if parse_errors:
            print(f"\nJSON 解析错误:")
            for item in parse_errors[:5]:
                print(f"  - 函数 {item['function_id']} ({item['alias']}): {item['error']}")

        # 步骤3: 批量插入映射
        print("\n🔹 步骤3: 批量插入 ATT&CK 映射")

        if mappings_to_insert:
            insert_count = 0
            duplicate_count = 0

            for mapping in mappings_to_insert:
                try:
                    cursor.execute("""
                        INSERT INTO attck_mappings (function_id, technique_id, created_at)
                        VALUES (?, ?, ?)
                    """, (mapping['function_id'], mapping['technique_id'], datetime.now()))
                    insert_count += 1
                except sqlite3.IntegrityError as e:
                    # 可能是重复键
                    duplicate_count += 1

            conn.commit()

            print(f"✓ 成功插入: {insert_count} 条")
            print(f"⚠ 跳过重复: {duplicate_count} 条")
        else:
            print("⚠ 没有需要插入的映射")

        # 步骤4: 验证结果
        print("\n🔹 步骤4: 验证数据完整性")

        cursor.execute("SELECT COUNT(*) FROM attck_mappings")
        final_count = cursor.fetchone()[0]

        # 统计每个函数的映射数
        cursor.execute("""
            SELECT
                f.id,
                f.alias,
                COUNT(am.technique_id) as mapping_count,
                GROUP_CONCAT(am.technique_id, ', ') as technique_ids
            FROM malapi_functions f
            LEFT JOIN attck_mappings am ON f.id = am.function_id
            WHERE f.manifest_json IS NOT NULL
            GROUP BY f.id
            ORDER BY mapping_count DESC
            LIMIT 10
        """)

        print(f"\n函数映射统计 (Top 10):")
        print(f"{'ID':<6} {'别名':<35} {'映射数':<8} {'技术ID'}")
        print("-" * 80)
        for row in cursor.fetchall():
            func_id, alias, count, tech_ids = row
            tech_ids = tech_ids or '(无)'
            print(f"{func_id:<6} {alias:<35} {count:<8} {tech_ids}")

        # 统计每个技术的函数数
        cursor.execute("""
            SELECT
                at.technique_id,
                at.technique_name,
                COUNT(am.function_id) as function_count
            FROM attack_techniques at
            INNER JOIN attck_mappings am ON at.technique_id = am.technique_id
            GROUP BY at.technique_id
            ORDER BY function_count DESC
            LIMIT 10
        """)

        print(f"\n技术映射统计 (Top 10):")
        print(f"{'技术ID':<15} {'技术名称':<40} {'函数数'}")
        print("-" * 70)
        for row in cursor.fetchall():
            tech_id, tech_name, count = row
            print(f"{tech_id:<15} {tech_name:<40} {count}")

        # 检查未映射的函数
        cursor.execute("""
            SELECT COUNT(*)
            FROM malapi_functions
            WHERE manifest_json IS NOT NULL
              AND json_extract(manifest_json, '$.attck') IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM attck_mappings am
                WHERE am.function_id = malapi_functions.id
              )
        """)
        unmapped_count = cursor.fetchone()[0]

        print(f"\n{'='*70}")
        print(f"📊 填充完成")
        print(f"{'='*70}")
        print(f"原始映射数: {existing_mappings} 条")
        print(f"新增映射数: {insert_count} 条")
        print(f"最终映射数: {final_count} 条")
        print(f"未映射函数: {unmapped_count} 个")
        print(f"{'='*70}")

        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ 填充失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = populate_attck_mappings()
    exit(0 if success else 1)
