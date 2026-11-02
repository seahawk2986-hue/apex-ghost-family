"""THE VOICE-CHAIN DIAG: the ears (running? hearing?), the speak (wired?),
the chat (up?) — then the honest break-list."""
import os
import subprocess as sp
import time

import psutil
import requests as rq

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"

print("== the ears ==")
ears = [p.info["pid"] for p in psutil.process_iter(["pid", "cmdline"])
        if "ApexEars" in " ".join(p.info["cmdline"] or [])]
print("[ears procs]:", ears or "NOT RUNNING")
elp = os.path.join(ROOT, "Logs", "apex_ears.log")
if os.path.exists(elp):
    lines = open(elp, encoding="utf-8-sig", errors="ignore").readlines()
    print(f"[ears log] {len(lines)} rows; the tail:")
    for l in lines[-5:]:
        print("  ", l.strip()[:110])
else:
    print("[ears log]: none")

print("== the speak ==")
print("[ApexSpeak.ps1 exists]:", os.path.exists(os.path.join(ROOT, "Scripts", "ApexSpeak.ps1")))
spl = os.path.join(ROOT, "Logs", "apex_speak.log")
print("[speak log]:", (open(spl, encoding="utf-8-sig", errors="ignore"
                            ).read()[-200:] if os.path.exists(spl) else "never spoken"))

print("== the chat ==")
try:
    KEY = open(os.path.join(ROOT, "Config", "apex_api.key"),
               encoding="utf-8-sig").read().strip()
    r = rq.get("http://127.0.0.1:8080/talk/status", timeout=8)
    print(f"[chat]: HTTP {r.status_code}")
except Exception as e:
    print("[chat]", str(e)[:60])

print("== the ears' chat-POST lane (the config) ==")
ec = os.path.join(ROOT, "Config", "ApexEars.json")
print(open(ec, encoding="utf-8-sig").read()[:500] if os.path.exists(ec)
      else "[ApexEars.json]: none")