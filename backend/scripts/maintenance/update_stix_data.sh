#!/bin/bash
# STIX 数据更新脚本
#
# 使用方法:
#   cd backend
#   bash scripts/maintenance/update_stix_data.sh

set -e  # 遇到错误立即退出

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STIX_SUBMODULE="$PROJECT_ROOT/attack-stix-data"

echo "========================================"
echo "  更新 ATT&CK STIX 数据"
echo "========================================"

# 1. 更新 Git 子模块
echo ""
echo "步骤1: 更新 Git 子模块..."
cd "$STIX_SUBMODULE"
echo "  → 拉取最新代码"
git fetch origin
git pull origin main

# 2. 检查最新版本
echo ""
echo "步骤2: 检查最新版本..."
LATEST_JSON="enterprise-attack/enterprise-attack.json"
if [ ! -f "$LATEST_JSON" ]; then
    echo "❌ 错误: 找不到最新版本文件"
    exit 1
fi
echo "  ✓ 找到 STIX 文件: $LATEST_JSON"

# 3. 重新导入数据
echo ""
echo "步骤3: 重新导入数据..."
cd "$PROJECT_ROOT/backend"
echo "  → 运行导入脚本"
conda run -n malapi-backend python scripts/maintenance/import_attack_from_stix.py --clear

echo ""
echo "========================================"
echo "✅ 更新完成!"
echo "========================================"
