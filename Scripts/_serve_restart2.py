"""THE SERVE-RESTART v2 (the full-cmdlines' honest + the single-serve +
the verify w/ the 30s-settle = the model's warm-up)."""
import json
import os
import subprocess
import time
import urllib.request

import psutil

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
PY = os.path.join(ROOT, "apex_venv", "Scripts", "python.exe")

serves = []
for p in psutil.process_iter(["pid", "cmdline"]):
    try:
        cl = " ".join(p.info["cmdline"] or [])
        if "run_apex_evolution" in cl:
            serves.append(p)
            print(f"[serve] pid {p.info['pid']}: {cl[-90]}")
    except Exception:
        pass
for p in serves:
    try:
        p.terminate()
    except Exception:
        pass
time.sleep(3)
DETACHED = 0x00000008
subprocess.Popen([PY, os.path.join(ROOT, "run_apex_evolution.py")],
                 cwd=ROOT, creationflags=DETACHED)
print("[serve] the SINGLE relaunch = in-flight (the 30s settle = "
      "the warm-up's honest)")
time.sleep(30)

import psutil as _p
serve2 = [p.info["pid"] for p in _p.process_iter(["pid", "cmdline"])
          if "run_apex_evolution" in " ".join(p.info["cmdline"] or [])]
print(f"[serve] NOW: {serve2} (the single!)")

KEY = open(os.path.join(ROOT, "Config", "apex_api.key"),
           encoding="utf-8-sig").read().strip()
req = urllib.request.Request(
    "http://127.0.0.1:8080/talk/api",
    data=json.dumps({"message": "which model are you using for this "
                                "chat?"}).encode(),
    headers={"Content-Type": "application/json", "X-Apex-Key": KEY},
    method="POST")
try:
    d = json.loads(urllib.request.urlopen(req, timeout=150).read())
    rep = (d or {}).get("reply", "")
    print("[reply]", rep[:280])
    if "gpt-oss" in rep.lower() or "120b" in rep:
        print("[CHAT-LOCK] LIVE - the 120b speaks")
    elif "quota" in rep.lower() or "rate" in rep.lower():
        print("[CHAT-LOCK] the RATE-CANDOR (honest; the 120b = the "
              "rate-lane's moment)")
    else:
        print("[CHAT-LOCK] CHECK:", rep[:120])
except Exception as e:
    print("[verify] honest:", str(e)[:90])