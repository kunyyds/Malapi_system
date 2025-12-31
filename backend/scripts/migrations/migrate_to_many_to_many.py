"""
数据库迁移脚本：从单战术关联改为多对多关系

使用方法:
    cd backend
    conda activate malapi-backend
    python scripts/migrations/migrate_to_many_to_many.py

说明:
    此迁移将：
    1. 创建 attack_technique_tactics 关联表
    2. 将现有 tactic_id 数据迁移到关联表
    3. 删除 attack_techniques.tactic_id 列（完全重构）
    4. 更新所有外键约束
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
    print("  MalAPI - 迁移到多对多战术关联")
    print("="*60)

    if not DB_PATH.exists():
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return False

    # 备份数据库
    backup_path = str(DB_PATH) + ".before_m2m_backup"
    import shutil
    shutil.copy2(str(DB_PATH), backup_path)
    print(f"\n✓ 数据库已备份到: {backup_path}")

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # 开启事务
        cursor.execute("BEGIN TRANSACTION")

        # ===== 步骤1: 创建关联表 =====
        print("\n🔹 步骤1: 创建 attack_technique_tactics 关联表")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attack_technique_tactics (
                technique_id VARCHAR(20) NOT NULL,
                tactic_id VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (technique_id, tactic_id),
                FOREIGN KEY (technique_id) REFERENCES attack_techniques(technique_id) ON DELETE CASCADE,
                FOREIGN KEY (tactic_id) REFERENCES attack_tactics(tactic_id) ON DELETE CASCADE
            )
        """)
        print("  ✓ 创建关联表成功")

        # ===== 步骤2: 迁移现有数据 =====
        print("\n🔹 步骤2: 迁移现有 tactic_id 数据到关联表")

        cursor.execute("""
            INSERT OR IGNORE INTO attack_technique_tactics (technique_id, tactic_id)
            SELECT technique_id, tactic_id FROM attack_techniques
            WHERE tactic_id IS NOT NULL
        """)
        migrated_count = cursor.rowcount
        print(f"  ✓ 迁移了 {migrated_count} 条关联记录")

        # ===== 步骤3: 删除旧的 tactic_id 列 =====
        print("\n🔹 步骤3: 删除 attack_techniques.tactic_id 列")

        # SQLite 不直接支持 DROP COLUMN，需要重建表
        print("  → SQLite 需要重建表...")

        # 获取表结构
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='attack_techniques'")
        table_sql = cursor.fetchone()[0]

        # 创建新表（不含 tactic_id）
        cursor.execute("""
            CREATE TABLE attack_techniques_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                technique_id VARCHAR(20) UNIQUE NOT NULL,
                technique_name VARCHAR(255) NOT NULL,
                is_sub_technique BOOLEAN DEFAULT 0,
                parent_technique_id VARCHAR(20),
                description TEXT,
                stix_id VARCHAR(100) UNIQUE,
                mitre_description TEXT,
                mitre_url VARCHAR(500),
                mitre_detection TEXT,
                mitre_mitigation TEXT,
                mitre_data_sources TEXT,
                mitre_updated_at TIMESTAMP,
                platforms VARCHAR(500),
                revoked BOOLEAN DEFAULT 0,
                deprecated BOOLEAN DEFAULT 0,
                data_source VARCHAR(50) DEFAULT 'stix_enterprise',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 复制数据（跳过 tactic_id）
        cursor.execute("""
            INSERT INTO attack_techniques_new (
                id, technique_id, technique_name, is_sub_technique, parent_technique_id,
                description, stix_id, mitre_description, mitre_url, mitre_detection,
                mitre_mitigation, mitre_data_sources, mitre_updated_at, platforms,
                revoked, deprecated, data_source, created_at, updated_at
            )
            SELECT
                id, technique_id, technique_name, is_sub_technique, parent_technique_id,
                description, stix_id, mitre_description, mitre_url, mitre_detection,
                mitre_mitigation, mitre_data_sources, mitre_updated_at, platforms,
                revoked, deprecated, data_source, created_at, updated_at
            FROM attack_techniques
        """)

        copied_count = cursor.rowcount
        print(f"  ✓ 复制了 {copied_count} 条记录")

        # 删除旧表
        cursor.execute("DROP TABLE attack_techniques")
        print("  ✓ 删除旧表")

        # 重命名新表
        cursor.execute("ALTER TABLE attack_techniques_new RENAME TO attack_techniques")
        print("  ✓ 重命名新表")

        # 重建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_attack_techniques_technique_id ON attack_techniques(technique_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_attack_techniques_is_sub_technique ON attack_techniques(is_sub_technique)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_attack_techniques_parent_technique_id ON attack_techniques(parent_technique_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_attack_techniques_stix_id ON attack_techniques(stix_id)")
        print("  ✓ 重建索引")

        # ===== 步骤4: 验证数据 =====
        print("\n🔹 步骤4: 验证迁移结果")

        # 统计关联表记录数
        cursor.execute("SELECT COUNT(*) FROM attack_technique_tactics")
        assoc_count = cursor.fetchone()[0]
        print(f"  ✓ 关联表记录数: {assoc_count}")

        # 检查技术表记录数
        cursor.execute("SELECT COUNT(*) FROM attack_techniques")
        tech_count = cursor.fetchone()[0]
        print(f"  ✓ 技术表记录数: {tech_count}")

        # 检查是否有孤立的技术（没有战术关联）
        cursor.execute("""
            SELECT COUNT(*) FROM attack_techniques t
            WHERE NOT EXISTS (
                SELECT 1 FROM attack_technique_tactics a
                WHERE a.technique_id = t.technique_id
            )
        """)
        orphan_count = cursor.fetchone()[0]
        if orphan_count > 0:
            print(f"  ⚠ 警告: {orphan_count} 个技术没有战术关联")
        else:
            print(f"  ✓ 所有技术都有战术关联")

        # 提交事务
        conn.commit()

        print("\n" + "="*60)
        print("✅ 迁移成功完成!")
        print("="*60)

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
