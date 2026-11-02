"""THE DEPLOY-VERIFY (the fix = in): restart the serve cleanly (the file-
way, self-excluding), then the fresh stream = the lane MUST read 'groq'."""
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
serves = []
for p in psutil.process_iter(["pid", "cmdline"]):
    try:
        if p.info["pid"] == ME:
            continue
        cl = " ".join(p.info["cmdline"] or [])
        if "python" in (p.info["name"] or "").lower() and cl.split(" ")[-1].replace('"', "").endswith("run_apex_evolution.py"):
            serves.append(p.info["pid"])
    except Exception:
        pass
print("[serve pre]:", serves)
for pid in serves:
    try:
        psutil.Process(pid).kill()
    except Exception:
        pass
time.sleep(3)
sp.Popen([os.path.join(ROOT, "apex_venv", "Scripts", "python.exe"),
          "run_apex_evolution.py"], cwd=ROOT, creationflags=0x00000008)
time.sleep(24)
serves = [p.info["pid"] for p in psutil.process_iter(["pid", "cmdline"])
          if "run_apex_evolution.py" in " ".join(p.info["cmdline"] or [])]
print("[serve post]:", serves)

KEY = open(os.path.join(ROOT, "Config", "apex_api.key"),
           encoding="utf-8-sig").read().strip()
r = rq.post("http://127.0.0.1:8080/talk/api/stream",
            json={"message": "In one short line: what model are you exactly?"},
            headers={"X-Apex-Key": KEY}, stream=True, timeout=240)
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
print("[FINAL-LANE-VERIFY] HTTP", r.status_code, "| lanes:", lanes,
      "| first-token:", str(ttft) + "s", "| reply:", "".join(acc)[:110])