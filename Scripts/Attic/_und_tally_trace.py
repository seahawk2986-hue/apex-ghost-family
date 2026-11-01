import ast
import json
import os
import re
import subprocess
import sys

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
import importlib.util
spec = importlib.util.spec_from_file_location(
    "fs", r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\FullSweep.py")
fs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fs)
files = fs.inv()
py_paths = []
for f in files:
    if f["kind"] != "code":
        continue
    base = AD if f.get("base") == "adapter" else ROOT
    py_paths.append(os.path.join(base, f["path"]))
und = {}
for i in range(0, min(len(py_paths), 400), 40):
    r = subprocess.run([sys.executable, "-m", "pyflakes"] + py_paths[i:i + 40],
                       capture_output=True, text=True, encoding="utf-8",
                       timeout=240)
    for w in (r.stdout or "").splitlines():
        m = re.search(r"undefined name '(\w+)'", w)
        if m:
            und.setdefault(m.group(1), []).append(
                w.split(":")[0]
                .replace(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "ROOT/")
                .replace(r"C:\Users\seaha\Apex-Adapter", "AD/"))
print(f"py_paths checked: {min(len(py_paths), 400)}")
for k, v in sorted(und.items(), key=lambda kv: -len(kv[1]))[:10]:
    print(f"  {k:20s} x{len(v):3d}  e.g. {v[0][-72:]}")