#!/bin/bash
set -e

echo "检查数据库状态..."

cd "$(dirname "$0")/.."

DB_FILE="malapi.db"
ATTACK_JSON="../matrix-enterprise.json"

if [ ! -f "$DB_FILE" ]; then
    echo "数据库文件不存在，开始初始化..."

    if [ ! -f "$ATTACK_JSON" ]; then
        echo "错误: 找不到 ATT&CK 数据文件"
        exit 1
    fi

    echo "步骤1: 创建 ATT&CK 表结构..."
    python scripts/maintenance/fix_attack_tables.py || exit 1

    echo "步骤2: 导入 ATT&CK 基础数据..."
    cd ..
    python backend/scripts/maintenance/import_attack.py || exit 1
    cd backend

    echo "数据库初始化完成"
else
    echo "数据库文件已存在"

    TABLE_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('attack_tactics', 'attack_techniques');" 2>/dev/null || echo "0")

    if [ "$TABLE_COUNT" -lt 2 ]; then
        echo "ATT&CK 表不存在，开始修复..."
        python scripts/maintenance/fix_attack_tables.py || exit 1
        cd ..
        python backend/scripts/maintenance/import_attack.py || exit 1
        cd backend
        echo "ATT&CK 表修复完成"
    else
        TACTICS_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM attack_tactics;" 2>/dev/null || echo "0")
        TECHNIQUES_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM attack_techniques;" 2>/dev/null || echo "0")

        if [ "$TACTICS_COUNT" -eq 0 ] || [ "$TECHNIQUES_COUNT" -eq 0 ]; then
            echo "ATT&CK 表为空，开始导入数据..."
            cd ..
            python backend/scripts/maintenance/import_attack.py || exit 1
            cd backend
            echo "ATT&CK 数据导入完成"
        else
            echo "数据库状态正常 (Tactics: $TACTICS_COUNT, Techniques: $TECHNIQUES_COUNT)"
        fi
    fi
fi

exit 0
