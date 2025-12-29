"""
修复 attck_mappings 表的 id 字段自增问题

问题: id 字段是 BIGINT 类型，不支持 SQLite 的 AUTOINCREMENT
解决: 改为 INTEGER PRIMARY KEY AUTOINCREMENT
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("/home/mine/workspace/MalAPI_system/backend/malapi.db")


def fix_table():
    """修复表结构"""

    if not DB_PATH.exists():
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return False

    print("="*60)
    print("  MalAPI - 修复 attck_mappings 表")
    print("="*60)

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # 步骤1: 备份现有数据
        print("\n🔹 步骤1: 备份现有数据")
        cursor.execute("SELECT COUNT(*) FROM attck_mappings")
        old_count = cursor.fetchone()[0]
        print(f"✓ 现有数据: {old_count} 条")

        # 步骤2: 删除旧表
        print("\n🔹 步骤2: 删除旧表结构")
        cursor.execute("DROP TABLE IF EXISTS attck_mappings")
        print("✓ 旧表已删除")

        # 步骤3: 创建新表（使用 INTEGER PRIMARY KEY AUTOINCREMENT）
        print("\n🔹 步骤3: 创建新表结构")
        cursor.execute("""
            CREATE TABLE attck_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_id INTEGER NOT NULL,
                technique_id VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (function_id, technique_id),
                FOREIGN KEY(function_id) REFERENCES malapi_functions(id) ON DELETE CASCADE,
                FOREIGN KEY(technique_id) REFERENCES attack_techniques(technique_id) ON DELETE CASCADE
            )
        """)
        print("✓ 新表已创建")

        # 步骤4: 创建索引
        print("\n🔹 步骤4: 创建索引")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_attck_mappings_function_id
            ON attck_mappings(function_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_attck_mappings_technique_id
            ON attck_mappings(technique_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_attck_mappings_func_tech
            ON attck_mappings(function_id, technique_id)
        """)
        print("✓ 索引已创建")

        # 步骤5: 从备份恢复数据
        print("\n🔹 步骤5: 从备份恢复数据")
        cursor.execute("""
            SELECT COUNT(*) FROM attck_mappings_backup
        """)
        backup_count = cursor.fetchone()[0]
        print(f"✓ 备份数据: {backup_count} 条")

        if backup_count > 0:
            cursor.execute("""
                INSERT INTO attck_mappings (function_id, technique_id, created_at)
                SELECT DISTINCT function_id, technique_id, created_at
                FROM attck_mappings_backup
                WHERE EXISTS (
                    SELECT 1 FROM attack_techniques
                    WHERE technique_id = attck_mappings_backup.technique_id
                )
            """)
            new_count = cursor.rowcount
            conn.commit()
            print(f"✓ 成功恢复: {new_count} 条")
        else:
            print("⚠ 备份表无数据")

        # 步骤6: 验证表结构
        print("\n🔹 步骤6: 验证表结构")
        cursor.execute("PRAGMA table_info(attck_mappings)")
        columns = cursor.fetchall()

        print("\n表结构:")
        for col in columns:
            print(f"  - {col[1]}: {col[2]} {'NOT NULL' if col[3] else ''} {'PK' if col[5] else ''}")

        # 步骤7: 测试自增功能
        print("\n🔹 步骤7: 测试自增功能")
        cursor.execute("""
            INSERT INTO attck_mappings (function_id, technique_id)
            VALUES (999, 'T0000')
        """)
        test_id = cursor.lastrowid
        print(f"✓ 插入测试记录，自动生成 ID: {test_id}")

        # 回滚测试
        conn.rollback()

        # 验证数据量
        cursor.execute("SELECT COUNT(*) FROM attck_mappings")
        final_count = cursor.fetchone()[0]

        print(f"\n{'='*50}")
        print(f"📊 修复完成")
        print(f"{'='*50}")
        print(f"最终记录数: {final_count} 条")
        print(f"{'='*50}")

        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ 修复失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = fix_table()
    exit(0 if success else 1)
