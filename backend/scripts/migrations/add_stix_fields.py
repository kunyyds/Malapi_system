"""
数据库迁移脚本：添加 STIX 相关字段

使用方法:
    cd backend
    conda activate malapi-backend
    python scripts/migrations/add_stix_fields.py
"""
import sys
import sqlite3
from pathlib import Path

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent.absolute()  # backend/scripts/migrations
BACKEND_DIR = SCRIPT_DIR.parent.parent  # backend
DB_PATH = BACKEND_DIR / "malapi.db"
sys.path.insert(0, str(BACKEND_DIR))

print(f"脚本目录: {SCRIPT_DIR}")
print(f"后端目录: {BACKEND_DIR}")
print(f"数据库路径: {DB_PATH}")
print(f"数据库存在: {DB_PATH.exists()}")


def migrate():
    """执行数据库迁移"""

    print("="*60)
    print("  MalAPI - 数据库迁移：添加 STIX 字段")
    print("="*60)

    if not DB_PATH.exists():
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return False

    print(f"\n📄 数据库路径: {DB_PATH}")

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # 开启事务
        cursor.execute("BEGIN TRANSACTION")

        # ===== attack_tactics 表 =====
        print("\n🔹 迁移 attack_tactics 表...")

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(attack_tactics)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'stix_id' not in columns:
            print("  → 添加 stix_id 字段")
            cursor.execute("""
                ALTER TABLE attack_tactics
                ADD COLUMN stix_id VARCHAR(100)
            """)
            # 创建唯一索引
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ix_attack_tactics_stix_id
                ON attack_tactics(stix_id)
            """)
        else:
            print("  → stix_id 字段已存在，跳过")

        # ===== attack_techniques 表 =====
        print("\n🔹 迁移 attack_techniques 表...")

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(attack_techniques)")
        columns = [col[1] for col in cursor.fetchall()]

        # STIX 扩展字段
        if 'stix_id' not in columns:
            print("  → 添加 stix_id 字段")
            cursor.execute("""
                ALTER TABLE attack_techniques
                ADD COLUMN stix_id VARCHAR(100)
            """)
            # 创建唯一索引
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS ix_attack_techniques_stix_id
                ON attack_techniques(stix_id)
            """)
        else:
            print("  → stix_id 字段已存在，跳过")

        if 'platforms' not in columns:
            print("  → 添加 platforms 字段")
            cursor.execute("""
                ALTER TABLE attack_techniques
                ADD COLUMN platforms VARCHAR(500)
            """)
        else:
            print("  → platforms 字段已存在，跳过")

        if 'revoked' not in columns:
            print("  → 添加 revoked 字段")
            cursor.execute("""
                ALTER TABLE attack_techniques
                ADD COLUMN revoked BOOLEAN DEFAULT 0
            """)
        else:
            print("  → revoked 字段已存在，跳过")

        if 'deprecated' not in columns:
            print("  → 添加 deprecated 字段")
            cursor.execute("""
                ALTER TABLE attack_techniques
                ADD COLUMN deprecated BOOLEAN DEFAULT 0
            """)
        else:
            print("  → deprecated 字段已存在，跳过")

        # 更新 data_source 默认值
        print("  → 更新 data_source 默认值为 'stix_enterprise'")
        cursor.execute("""
            UPDATE attack_techniques
            SET data_source = 'stix_enterprise'
            WHERE data_source = 'matrix_enterprise'
        """)

        # 提交事务
        conn.commit()

        print("\n" + "="*50)
        print("✅ 数据库迁移成功完成!")
        print("="*50)

        # 验证迁移结果
        print("\n📊 验证迁移结果:")

        cursor.execute("PRAGMA table_info(attack_tactics)")
        tactics_columns = [col[1] for col in cursor.fetchall()]
        print(f"  attack_tactics 字段数: {len(tactics_columns)}")
        print(f"  包含 stix_id: {'stix_id' in tactics_columns}")

        cursor.execute("PRAGMA table_info(attack_techniques)")
        tech_columns = [col[1] for col in cursor.fetchall()]
        print(f"  attack_techniques 字段数: {len(tech_columns)}")
        print(f"  包含 stix_id: {'stix_id' in tech_columns}")
        print(f"  包含 platforms: {'platforms' in tech_columns}")
        print(f"  包含 revoked: {'revoked' in tech_columns}")
        print(f"  包含 deprecated: {'deprecated' in tech_columns}")

        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()

        # 回滚事务
        if conn:
            conn.rollback()
            print("已回滚所有更改")

        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
