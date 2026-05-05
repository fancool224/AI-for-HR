#!/usr/bin/env bash
# ============================================
# 定时合并脚本 - 每周五 12:00 执行
# ============================================
# 功能：
#   1. 运行 weekly-merge.py
#   2. 提交并推送到 GitHub
#
# Windows 定时任务设置：
#   schtasks /create /tn "TOP-HR-Merge" /tr "python.exe C:\Users\22606\WorkBuddy\TOP-HR-Agent-basic\master-agent\weekly-merge.py --auto" /sc weekly /d FRI /st 12:00
#
# Linux/Mac crontab：
#   0 12 * * 5 /path/to/weekly-merge.py --auto
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON="python"

echo "🚀 开始每周合并任务..."
echo "📁 项目目录: $PROJECT_DIR"
echo "⏰ 执行时间: $(date)"

cd "$PROJECT_DIR"

# 1. 运行合并脚本（自动模式）
echo ""
echo "📦 步骤1：执行合并脚本"
$PYTHON master-agent/weekly-merge.py --auto

# 2. 提交变更
echo ""
echo "📝 步骤2：提交变更"
git add .
git commit -m "每周合并更新 $(date +'%Y-%m-%d')" || echo "没有新变更"

# 3. 推送到 GitHub（使用 http.extraHeader 认证）
echo ""
echo "📤 步骤3：推送到 GitHub"
git push origin master:main 2>&1 || echo "推送可能失败，请检查"

echo ""
echo "✅ 定时任务完成！"
