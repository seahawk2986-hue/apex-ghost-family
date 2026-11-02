"""THE ONE-CLEAN-RESTART: the literal-pid kill + the relaunch + the
fresh stream-verify (the lane = groq expected; the ollama-queue = the
honest fallback). 90s read-cap."""
import json
import os
import subprocess as sp
import sys
import time

import psutil
import requests as rq

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
os.chdir(ROOT)
ME = os.getpid()
PYEXE = os.path.join(ROOT, "apex_venv", "Scripts", "python.exe")

# any run_apex_evolution.py-scriptarg process (self-excluded, -c-shells excluded)
victims = []
for p in psutil.process_iter(["pid", "cmdline", "name"]):
    try:
        if p.info["pid"] == ME:
            continue
        if "python" not in (p.info["name"] or "").lower():
            continue
        cl = p.info["cmdline"] or []
        if len(cl) >= 2 and cl[-1].replace('"', "").endswith(
                "run_apex_evolution.py"):
            victims.append(p.info["pid"])
    except Exception:
        pass
# also the port-owner explicitly
try:
    own = (sp.run(["powershell", "-NoProfile", "-Command",
                   "(Get-NetTCPConnection -LocalPort 8080 -State Listen "
                   "-ErrorAction SilentlyContinue | Select-Object -First 1)"
                   ".OwningProcess"], capture_output=True, text=True,
                  timeout=20).stdout or "0").strip()
    if own.isdigit() and int(own) not in victims + [ME]:
        victims.append(int(own))
except Exception:
    pass
print("[restart victims]:", victims)
for pid in victims:
    try:
        psutil.Process(pid).kill()
    except Exception:
        pass
time.sleep(4)
sp.Popen([PYEXE, "run_apex_evolution.py"], cwd=ROOT, creationflags=0x00000008)
time.sleep(26)
KEY = open("Config/apex_api.key", encoding="utf-8-sig").read().strip()
r = rq.post("http://127.0.0.1:8080/talk/api/stream",
            json={"message": "In one line: what model are you exactly?"},
            headers={"X-Apex-Key": KEY}, stream=True, timeout=90)
lanes, acc, ttft, t0 = set(), [], None, time.time()
for line in r.iter_lines(decode_unicode=True):
    if not line:
        continue
    if line.startswith("data:"):
        try:
            j = json.loads(line[5:].strip())
            if j.get("lane"):
                lanes.add(j["lane"])
            if j.get("t"):
                ttft = ttft or round(time.time() - t0, 2)
                acc.append(j["t"])
        except Exception:
            pass
print("[LANE-VERIFY] HTTP", r.status_code, "| lanes:", lanes,
      "| first-token:", str(ttft) + "s", "| reply:", "".join(acc)[:100])