"""
临时推送脚本（单次使用）
Token 不写在此文件中，而是通过 git config 配置
"""
import subprocess

token = "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"  # ← 在这里填写

result = subprocess.run(
    ["git", "config", "http.extraHeader", f"AUTHORIZATION: Bearer {token}"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
print(result.stdout, result.stderr)

result = subprocess.run(
    ["git", "push", "-f", "origin", "master:main"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("返回码:", result.returncode)
