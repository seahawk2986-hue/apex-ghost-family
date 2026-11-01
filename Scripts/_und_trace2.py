import os
import importlib.util
spec = importlib.util.spec_from_file_location(
    "fs", r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\FullSweep.py")
fs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fs)
files = fs.inv()
AD, ROOT = fs.AD, fs.ROOT
for f in files:
    if f["kind"] == "code" and f["size"] > -1:
        base = AD if f.get("base") == "adapter" else ROOT
        p = os.path.join(base, f["path"])
        try:
            t = open(p, encoding="utf-8-sig", errors="replace").read()
        except Exception:
            continue
        if "def access(" in t or "def is_adult(" in t or "def fib(" in t:
            print("THE FLAGGED FILE:", f["path"])