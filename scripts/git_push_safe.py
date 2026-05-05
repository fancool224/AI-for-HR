#!/usr/bin/env python3
"""
安全的 Git 推送脚本 - 避免 Token 特殊字符被 Shell 解释
功能：自动推送本地提交到 GitHub 远程仓库
"""

import subprocess
import os
import sys
from pathlib import Path

# ========== 配置区 ==========
GITHUB_TOKEN = "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"
GITHUB_USER = "fancool224"
REPO_NAME = "AI-for-HR"
BRANCH = "main"  # 或 "master"

# 构建认证 URL（Token 作为密码）
REPO_URL = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{REPO_NAME}.git"

# 项目根目录
PROJECT_DIR = Path(__file__).parent.parent.absolute()
# =============================


def run_git_command(args, check=True):
    """运行 Git 命令，自动处理 Token 特殊字符"""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if result.stdout:
            print(f"[STDOUT] {result.stdout.strip()}")
        if result.stderr:
            print(f"[STDERR] {result.stderr.strip()}")

        if check and result.returncode != 0:
            print(f"❌ 命令失败: git {' '.join(args)}")
            sys.exit(1)

        return result

    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)


def main():
    print(f"🚀 开始推送项目: {PROJECT_DIR}")
    print(f"📦 远程仓库: {REPO_NAME}")
    print("-" * 60)

    # 1. 检查是否在 Git 仓库中
    result = run_git_command(["rev-parse", "--git-dir"], check=False)
    if result.returncode != 0:
        print("❌ 错误：当前目录不是 Git 仓库！")
        print("请先运行：git init")
        sys.exit(1)

    # 2. 检查是否有提交
    result = run_git_command(["log", "--oneline", "-1"], check=False)
    if result.returncode != 0:
        print("❌ 错误：没有提交记录！")
        print("请先运行：git add . && git commit -m 'Initial commit'")
        sys.exit(1)

    # 3. 设置远程仓库（如果未设置）
    result = run_git_command(["remote", "get-url", "origin"], check=False)
    if result.returncode != 0:
        print("➕ 添加远程仓库...")
        run_git_command(["remote", "add", "origin", REPO_URL])
    else:
        print("✅ 远程仓库已配置")
        # 更新为正确的 URL（确保 Token 正确）
        run_git_command(["remote", "set-url", "origin", REPO_URL])

    # 4. 推送（使用 Token 认证）
    print(f"\n📤 推送分支 {BRANCH} 到远程...")
    run_git_command(["push", "-u", "origin", BRANCH])

    print("\n" + "=" * 60)
    print("✅ 推送成功！")
    print(f"🔗 查看仓库: https://github.com/{GITHUB_USER}/{REPO_NAME}")
    print("=" * 60)


if __name__ == "__main__":
    main()
