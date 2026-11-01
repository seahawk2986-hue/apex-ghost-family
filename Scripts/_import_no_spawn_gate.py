import subprocess, sys
r = subprocess.run([sys.executable, "-c",
    'import sys; sys.path.insert(0, r"C:\\Users\\seaha\\Downloads\\'
    'Apex-With-Triggers-Fixed\\Scripts");'
    'import DeploySwarm; print("IMPORT-CLEAN")'],
    capture_output=True, text=True, encoding="utf-8",
    timeout=60, cwd=r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed")
out = (r.stdout or "").strip()
print("rc =", r.returncode, "| stdout =", out[:120])
ok = out == "IMPORT-CLEAN" and r.returncode == 0 \
    and "fleet plan" not in out and "grain line" not in out
print("IMPORT-NO-SPAWN GATE:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)