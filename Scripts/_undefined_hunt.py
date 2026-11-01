import ast
import json
import os
import re
import subprocess
import sys

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
S = os.path.join(ROOT, "Scripts")
rep = json.load(open(os.path.join(ROOT, "Config", "full_sweep.json"),
                     encoding="utf-8-sig"))
excluded = (".git", "apex_venv", "training_venv", "__pycache__", ".lmstudio",
            "node_modules", "site-packages", "Scratch", "Backup_Archive",
            "versions", "Attic", "manual_fix_20261030", "skill_stage",
            "egg-info", ".ruff_cache", "_handoff")
py_paths = []
for dp, dns, fns in os.walk(ROOT):
    if any(x in dp for x in excluded):
        dns[:] = []
        continue
    dns[:] = [d for d in dns if d not in (".git", "__pycache__")]
    for fn in fns:
        if fn.endswith(".py"):
            py_paths.append(os.path.join(dp, fn))
und = {}
for i in range(0, len(py_paths), 40):
    r = subprocess.run([sys.executable, "-m", "pyflakes"] + py_paths[i:i + 40],
                       capture_output=True, text=True, encoding="utf-8",
                       timeout=240)
    for w in (r.stdout or "").splitlines():
        m = re.search(r"undefined name '(\w+)'", w)
        if m:
            und.setdefault(m.group(1), []).append(w.split(":")[0]
                                                 .replace(
                r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", ""))
print(f"live-code files: {len(py_paths)} | distinct undefined: "
      f"{len(und)} / occurrences {sum(len(v) for v in und.values())}")
for k, v in sorted(und.items(), key=lambda kv: -len(kv[1]))[:12]:
    print(f"  {k:22s} x{len(v):3d}  e.g. ...{v[0][-64:]}")