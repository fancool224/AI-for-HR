import subprocess

token = "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"
url = f"https://fancool224:{token}@github.com/fancool224/AI-for-HR.git"

print("开始推送...")
result = subprocess.run(
    ["git", "push", "-f", url, "master:main"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace"
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("返回码:", result.returncode)
