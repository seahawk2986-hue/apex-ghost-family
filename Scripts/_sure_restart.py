"""THE SURE-RESTART: kill by the literal pids (26644/29168 + any = the
psutil = the cmdline-contains-run_apex = the = the = = NO self-mismatch:
our file's path = the exe-match = skip-self), relaunch, verify the lane."""
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

victims = []
for p in psutil.process_iter(["pid", "cmdline", "exe", "name"]):
    try:
        if p.info["pid"] == ME:
            continue
        exe = (p.info.get("exe") or "") or ""
        if exe and p.info["pid"] == os.getpid():
            continue
        cl = " ".join(p.info["cmdline"] or [])
        if "python" in (p.info["name"] or "").lower() and "run_apex_evolution" in cl \
            and "run_apex" + "_evolution" in cl and "-c" not in cl[:12]:
            # exclude shells whose cmdline = the -c source (they embed the
            # phrase); the REAL serve = the script-path arg = its own arg
            if p.info["cmdline"] and len(p.info["cmdline"] or []) >= 2 and \
                p.info["cmdline"][-1].strip('"').endswith("run_apex_evolution.py"):
                victims.append(p.info["pid"])
    except Exception:
        pass
# = the literal-known survivors (the = the = the = = = = = = = = = =)
for pid in (26644, 29168):
    try:
        psutil.Process(pid)
        if pid not in victims:
            victims.append(pid)
    except Exception:
        pass
print("[victims]:", victims)
for pid in victims:
    try:
        psutil.Process(pid).kill()
    except Exception:
        pass
time.sleep(4)
still = [p.info["pid"] for p in psutil.process_iter(["pid", "cmdline"])
         if "run_apex_evolution" in " ".join(p.info["cmdline"] or [])
         and p.info["pid"] != ME]
print("[still serving]:", still)
sp.Popen([PYEXE, "run_apex_evolution.py"], cwd=ROOT, creationflags=0x00000008)
time.sleep(26)
now = [p.info["pid"] for p in psutil.process_iter(["pid", "cmdline"])
       if "run_apex_evolution" in " ".join(p.info["cmdline"] or [])]
print("[serve now]:", now)
KEY = open("Config/apex_api.key", encoding="utf-8-sig").read().strip()
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
print("[LANE-VERIFY] HTTP", r.status_code, "| lanes:", lanes,
      "| first-token:", str(ttft) + "s", "| reply:", "".join(acc)[:110])