"""THE EARS-LAUNCH (final): detached relaunch on the now-CLEAN script,
then the alive-verification at +7s + the boot-log tail."""
import os
import subprocess as sp
import time

import psutil

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
os.chdir(ROOT)

sp.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
          "-WindowStyle", "Hidden", "-File",
          os.path.join(ROOT, "Scripts", "ApexEars.ps1")],
         cwd=ROOT, creationflags=0x00000008)
time.sleep(7)
alive = []
for p in psutil.process_iter(["pid", "name", "cmdline"]):
    try:
        if ("powershell" in (p.info["name"] or "").lower()
                and "apexears" in " ".join(p.info["cmdline"] or []).lower()):
            alive.append(p.info["pid"])
    except Exception:
        pass
print("[ears alive on the fixed script]:", alive)
boot = os.path.join(ROOT, "Logs", "apex_ears_boot.log")
if os.path.exists(boot):
    for l in open(boot, encoding="utf-8-sig", errors="ignore").readlines()[-3:]:
        print("  ", l.strip()[:100])