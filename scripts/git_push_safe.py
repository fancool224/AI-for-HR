import subprocess
import os
from pathlib import Path

# ========== 配置区 ==========
GITHUB_TOKEN = "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"  # ← 在这里填写 Token（仅本地使用）
GITHUB_USER = "fancool224"
REPO_NAME = "AI-for-HR"
BRANCH = "master"  # 推送分支（映射到远程 main）
# =============================

PROJECT_DIR = Path(__file__).parent.parent.absolute()

def run(cmd, check=True):
    r = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.stdout: print(r.stdout)
    if r.stderr and "warning" not in r.stderr.lower(): print(r.stderr, file=__import__('sys').stderr)
    if check and r.returncode != 0: __import__('sys').exit(1)
    return r

print("=" * 60)
print(f"🚀 推送到 GitHub: {GITHUB_USER}/{REPO_NAME}")
print("=" * 60)

# 1. 配置 Token（存储在本地 .git/config，不进代码）
run(["git", "config", "http.extraHeader", f"AUTHORIZATION: Bearer {GITHUB_TOKEN}"])

# 2. 推送
print("\n📤 正在推送...")
run(["git", "push", "-f", "origin", f"{BRANCH}:main"])

print("\n" + "=" * 60)
print(f"✅ 推送成功！https://github.com/{GITHUB_USER}/{REPO_NAME}")
print("=" * 60)
