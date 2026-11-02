"""The repair-list steps 2-3: the git rebind (proper) + the full recheck sweep."""
import io
import py_compile
import os
import sys
import subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
g = lambda *c: subprocess.run(["git", *c], cwd=REPO, capture_output=True,
                              text=True, encoding="utf-8")

print("=== the git rebind (the proper sync) ===")
print("  [current]:", g("log", "--oneline", "-1").stdout.strip())
r = g("pull", "--rebase", "--autostash", "origin", "main")
print("  [pull]:", (r.stdout or r.stderr).strip()[-120:])
r = g("push")
print("  [push]:", (r.stdout or r.stderr).strip()[-120:])
print("  [head]:", g("log", "--oneline", "-1").stdout.strip())

print("=== the full recheck: the compile audit (all py) ===")
bad, ok = [], 0
for root in ("Scripts", "Tools"):
    for f in os.listdir(os.path.join(REPO, root)):
        if f.endswith(".py"):
            p = os.path.join(REPO, root, f)
            try:
                py_compile.compile(p, doraise=True)
                ok += 1
            except Exception as e:
                bad.append((f, str(e)[:60]))
print(f"  compile: {ok} OK / {bad and len(bad)} BAD")
for f, e in bad:
    print("    BAD:", f, "|", e)