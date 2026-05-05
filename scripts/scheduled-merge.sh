#!/bin/bash
# ============================================================================
# 每周合并脚本 — Master Agent 自动执行
# 触发方式：cron 定时 / GitHub Actions / 手动运行
# ============================================================================

set -euo pipefail

# 脚本所在目录（即项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION_FILE="$PROJECT_ROOT/shared-context/version-control/VERSION"
MERGE_LOG_DIR="$PROJECT_ROOT/master-agent/merge-log"
MERGE_LOG_FILE="$MERGE_LOG_DIR/$(date '+%Y-%m-%d').md"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Master Agent 每周合并 — $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# 1. 确保目录存在
mkdir -p "$MERGE_LOG_DIR"

# 2. 读取当前版本号
if [[ -f "$VERSION_FILE" ]]; then
  CURRENT_VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')
else
  CURRENT_VERSION="0.0.0"
fi

echo "当前版本: $CURRENT_VERSION"

# 3. 拉取 GitHub 最新配置
echo ""
echo "[1/4] 拉取 GitHub 最新配置..."
if git remote get-url origin &>/dev/null; then
  git pull origin main --ff-only 2>/dev/null || echo "⚠️ GitHub 拉取无更新或失败，继续本地合并"
else
  echo "⚠️ 未配置 remote，跳过 GitHub 拉取"
fi

# 4. 检查腾讯文档协作存档
echo ""
echo "[2/4] 检查腾讯文档协作存档..."
# 注：实际腾讯文档读取由 Skill（wecom-doc/wecom-doc-fetcher）完成
# 此处仅记录检查状态
if [[ -d "shared-context/" ]]; then
  CONTEXT_FILES=$(find shared-context/ -name "*.md" | wc -l)
  echo "共享上下文文件数量: $CONTEXT_FILES"
else
  echo "无共享上下文文件，跳过"
fi

# 5. 检查各 Agent 工作目录
echo ""
echo "[3/4] 检查 Agent 工作目录..."
if [[ -d "agents/" ]]; then
  for agent_dir in agents/*/; do
    agent_name=$(basename "$agent_dir")
    echo "  - $agent_name: 已注册"
  done
else
  echo "  无 Agent 工作目录"
fi

# 6. 版本号 +1 并记录日志
NEW_VERSION=$(echo "$CURRENT_VERSION" | awk -F. '{print $1"."$2"."$3+1}')
echo "$NEW_VERSION" > "$VERSION_FILE"

cat > "$MERGE_LOG_FILE" << EOF
# 合并日志 — $(date '+%Y-%m-%d')

| 项目 | 内容 |
|------|------|
| 合并前版本 | $CURRENT_VERSION |
| 合并后版本 | $NEW_VERSION |
| 合并时间 | $(date '+%Y-%m-%d %H:%M:%S') |
| 合并来源 | GitHub main + 本地状态 |

## 本次合并摘要

EOF

echo ""
echo "[4/4] 合并完成"
echo "新版本: $NEW_VERSION"
echo "日志: $MERGE_LOG_FILE"
echo "=========================================="
