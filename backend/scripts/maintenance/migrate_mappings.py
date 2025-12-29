"""
迁移原有attck_mappings数据并验证完整性

使用方法:
    cd backend
    conda activate malapi-backend
    python migrate_mappings.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("/home/mine/workspace/MalAPI_system/backend/malapi.db")


def migrate_and_validate():
    """迁移映射数据并验证"""

    print("="*60)
    print("  MalAPI - 映射数据迁移与验证")
    print("="*60)

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # 步骤1: 检查备份数据
        print("\n🔹 步骤1: 检查备份数据")
        cursor.execute("SELECT COUNT(*) FROM attck_mappings_backup")
        backup_count = cursor.fetchone()[0]
        print(f"✓ 备份数据: {backup_count} 条")

        # 步骤2: 检查attack_techniques中的数据
        print("\n🔹 步骤2: 检查ATT&CK基础数据")
        cursor.execute("SELECT COUNT(*) FROM attack_tactics")
        tactics_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM attack_techniques")
        techniques_count = cursor.fetchone()[0]

        print(f"✓ Tactics: {tactics_count} 条")
        print(f"✓ Techniques: {techniques_count} 条")

        # 步骤3: 迁移有效的映射数据
        print("\n🔹 步骤3: 迁移有效的映射数据")

        # 获取所有备份中的映射
        cursor.execute("""
            SELECT DISTINCT function_id, technique_id, created_at
            FROM attck_mappings_backup
            ORDER BY function_id, technique_id
        """)
        all_mappings = cursor.fetchall()

        valid_count = 0
        invalid_count = 0
        invalid_list = []

        for function_id, technique_id, created_at in all_mappings:
            # 检查technique_id是否存在于attack_techniques表中
            cursor.execute("""
                SELECT 1 FROM attack_techniques
                WHERE technique_id = ?
            """, (technique_id,))

            if cursor.fetchone():
                # 有效数据,插入
                try:
                    cursor.execute("""
                        INSERT INTO attck_mappings (function_id, technique_id, created_at)
                        VALUES (?, ?, ?)
                    """, (function_id, technique_id, created_at))
                    valid_count += 1
                except sqlite3.IntegrityError:
                    # 可能已经存在,跳过
                    pass
            else:
                # 无效数据
                invalid_count += 1
                invalid_list.append(technique_id)

        conn.commit()

        print(f"✓ 成功迁移: {valid_count} 条")
        print(f"✗ 清理无效: {invalid_count} 条")

        if invalid_count > 0:
            print(f"\n无效的technique_id示例(前10个):")
            for tech_id in list(set(invalid_list))[:10]:
                print(f"  - {tech_id}")

        # 步骤4: 验证数据完整性
        print("\n🔹 步骤4: 数据完整性验证")

        # 验证映射总数
        cursor.execute("SELECT COUNT(*) FROM attck_mappings")
        new_count = cursor.fetchone()[0]

        print(f"\n{'='*50}")
        print(f"📊 数据迁移报告")
        print(f"{'='*50}")
        print(f"原始映射数: {backup_count} 条")
        print(f"新映射数: {new_count} 条")
        print(f"清理的无效映射: {invalid_count} 条")
        print(f"数据保留率: {new_count/backup_count*100:.1f}%")
        print(f"{'='*50}")

        # 步骤5: 抽样验证
        print("\n🔹 步骤5: 抽样验证数据质量")

        # 验证映射关系完整性
        cursor.execute("""
            SELECT f.alias, at.technique_id, at.technique_name, att.tactic_name_en
            FROM malapi_functions f
            INNER JOIN attck_mappings am ON f.id = am.function_id
            INNER JOIN attack_techniques at ON am.technique_id = at.technique_id
            INNER JOIN attack_tactics att ON at.tactic_id = att.tactic_id
            LIMIT 5
        """)

        print("\n映射数据示例:")
        print(f"{'Function Alias':<30} {'Technique ID':<15} {'Technique Name':<30} {'Tactic'}")
        print("-" * 90)
        for row in cursor.fetchall():
            print(f"{row[0]:<30} {row[1]:<15} {row[2]:<30} {row[3]}")

        # 统计每个tactic的映射数量
        cursor.execute("""
            SELECT att.tactic_name_en, COUNT(*) as count
            FROM attack_tactics att
            INNER JOIN attack_techniques at ON att.tactic_id = at.tactic_id
            INNER JOIN attck_mappings am ON at.technique_id = am.technique_id
            GROUP BY att.tactic_id, att.tactic_name_en
            ORDER BY count DESC
            LIMIT 5
        """)

        print("\n按战术统计的映射数(Top 5):")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} 个映射")

        print(f"\n{'='*50}")
        print("✅ 数据迁移和验证完成!")
        print(f"{'='*50}")

        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ 操作失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate_and_validate()
    exit(0 if success else 1)
