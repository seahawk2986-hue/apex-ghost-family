"""THE SERVE-SINGLETON (the robust cure): keep EXACTLY the port-8080
owner; self-exclusion (never kill our own shell); the fresh 120b-stream
verify after."""
import json
import os
import subprocess as _sp
import sys
import time

import psutil
import requests as rq

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
os.chdir(ROOT)
ME = os.getpid()

owner = None
try:
    r = _sp.run(["powershell", "-NoProfile", "-Command",
                 "(Get-NetTCPConnection -LocalPort 8080 -State Listen "
                 "-ErrorAction SilentlyContinue | Select-Object -First 1)"
                 ".OwningProcess"], capture_output=True, text=True, timeout=20)
    owner = int((r.stdout or "0").strip() or 0) or None
except Exception:
    pass
print("[port-8080 owner]:", owner)

kept, killed = [], []
for p in psutil.process_iter(["pid", "cmdline", "name"]):
    try:
        if p.info["pid"] == ME:
            continue
        cl = " ".join(p.info["cmdline"] or [])
        # the REAL serve = the cmdline ENDS with the script (the -c shells
        # = contain the phrase mid-source = the self-kill-trap = excluded)
        if not cl.split(" ")[-1].replace('"', "").endswith("run_apex_evolution.py"):
            continue
        if "python" not in (p.info["name"] or "").lower():
            continue
        if owner and p.info["pid"] == owner:
            kept.append(p.info["pid"])
            continue
        if owner is None and not killed and p.info["pid"] == min(
                x.info["pid"] for x in psutil.process_iter(["pid"]
                ) if x.info.get("pid")):
            pass  # (rare no-owner case: keep the oldest below)
        killed.append(p.info["pid"])
        p.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    except Exception:
        pass
print(f"[killed zombies]: {killed}")
time.sleep(2)
serves = [p.info["pid"] for p in psutil.process_iter(["pid", "cmdline"])
          if "run_apex_evolution.py" in " ".join(p.info["cmdline"] or [])
          and p.info["pid"] != ME]
print("[serve pids]:", serves)
if not serves:
    print("[relaunch] the single serve...")
    _sp.Popen([os.path.join(ROOT, "apex_venv", "Scripts", "python.exe"),
               "run_apex_evolution.py"], cwd=ROOT,
              creationflags=0x00000008)  # DETACHED_PROCESS
    time.sleep(22)
    serves = [p.info["pid"] for p in psutil.process_iter(["pid", "cmdline"])
              if "run_apex_evolution.py" in " ".join(p.info["cmdline"] or [])]
    print("[serve pids post-launch]:", serves)

# the FRESH THE-120b-verify (the lane-name = the truth)
KEY = open(os.path.join(ROOT, "Config", "apex_api.key"),
           encoding="utf-8-sig").read().strip()
r = rq.post("http://127.0.0.1:8080/talk/api/stream",
            json={"message": "In one short line: which model is your chat voice?"},
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
print("[THE 120b-VERIFY] HTTP", r.status_code, "| lanes:", lanes,
      "| first-token:", str(ttft) + "s", "| reply:", "".join(acc)[:110])