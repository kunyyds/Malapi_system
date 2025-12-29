"""
重建 attack_tactics 和 attack_techniques 表，修复 id 字段的自增问题
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("/home/mine/workspace/MalAPI_system/backend/malapi.db")


def fix_tables():
    """重建表结构"""

    print("="*60)
    print("  MalAPI - 修复 ATT&CK 表结构")
    print("="*60)

    # 如果数据库文件不存在，创建一个空的
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # 步骤1: 删除旧表
        print("\n🔹 步骤1: 删除旧表")
        cursor.execute("DROP TABLE IF EXISTS attack_techniques")
        cursor.execute("DROP TABLE IF EXISTS attack_tactics")
        print("✓ 旧表已删除")

        # 步骤2: 创建 attack_tactics 表
        print("\n🔹 步骤2: 创建 attack_tactics 表")
        cursor.execute("""
            CREATE TABLE attack_tactics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tactic_id VARCHAR(20) UNIQUE NOT NULL,
                tactic_name_en VARCHAR(255) NOT NULL,
                tactic_name_cn VARCHAR(255),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ attack_tactics 表已创建")

        # 步骤3: 创建 attack_techniques 表
        print("\n🔹 步骤3: 创建 attack_techniques 表")
        cursor.execute("""
            CREATE TABLE attack_techniques (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                technique_id VARCHAR(20) UNIQUE NOT NULL,
                technique_name VARCHAR(255) NOT NULL,
                tactic_id VARCHAR(20) NOT NULL,
                is_sub_technique BOOLEAN DEFAULT 0,
                parent_technique_id VARCHAR(20),
                description TEXT,
                mitre_description TEXT,
                mitre_url VARCHAR(500),
                mitre_detection TEXT,
                mitre_mitigation TEXT,
                mitre_data_sources TEXT,
                mitre_updated_at TIMESTAMP,
                data_source VARCHAR(50) DEFAULT 'matrix_enterprise',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(tactic_id) REFERENCES attack_tactics(tactic_id) ON DELETE CASCADE
            )
        """)
        print("✓ attack_techniques 表已创建")

        # 步骤4: 创建索引
        print("\n🔹 步骤4: 创建索引")

        # attack_tactics 索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_attack_tactics_tactic_id
            ON attack_tactics(tactic_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_attack_tactics_name_en
            ON attack_tactics(tactic_name_en)
        """)

        # attack_techniques 索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_attack_techniques_technique_id
            ON attack_techniques(technique_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_attack_techniques_tactic_id
            ON attack_techniques(tactic_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_attack_techniques_is_sub
            ON attack_techniques(is_sub_technique)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_attack_techniques_parent_id
            ON attack_techniques(parent_technique_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_attack_techniques_name
            ON attack_techniques(technique_name)
        """)

        print("✓ 索引已创建")

        conn.commit()
        print("\n✅ 表结构修复完成！")

        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ 修复失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = fix_tables()
    print("\n下一步: 运行 python backend/import_attack.py 导入ATT&CK数据")
    exit(0 if success else 1)
