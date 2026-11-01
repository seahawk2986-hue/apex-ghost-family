import glob
import os
import subprocess
import sys

paths = (glob.glob(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\*.py")
         + glob.glob(r"C:\Users\seaha\Apex-Adapter\*.py"))
n_und = 0
for i in range(0, len(paths), 30):
    r = subprocess.run([sys.executable, "-m", "pyflakes"] + paths[i:i + 30],
                       capture_output=True, text=True, encoding="utf-8",
                       timeout=180)
    for w in (r.stdout or "").splitlines():
        if "undefined name" in w:
            n_und += 1
            print(w.replace(
                r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "")
              .replace(r"C:\Users\seaha\Apex-Adapter", "ADAPTER/"))
print(f"scan complete: {len(paths)} root/adapter files, {n_und} undefined")