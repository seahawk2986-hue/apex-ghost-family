"""THE VOICE-RESTORE CONDUCTOR:
1. kill the OLD ears (they hold the pre-fix ApexEars.ps1 in memory:
   no-auth 401 + -Message/-Text mismatch + reply-discarded) by LITERAL pids.
2. relaunch the ears detached on the FIXED script.
3. prove the send-lane the ears will use: POST /talk/api WITH the
   X-Apex-Key header -> expect 200 + a non-empty reply field.
4. one stream ask -> the honest lane-tag from Logs/system.log.
No inline powershell, no self-kill possible (it kills only powershell
procs whose cmdline has ApexEars)."""
import json
import os
import subprocess as sp
import time

import psutil
import requests as rq

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
os.chdir(ROOT)

# 1. the literal-pid ears cull
victims = []
for p in psutil.process_iter(["pid", "name", "cmdline"]):
    try:
        nm = (p.info["name"] or "").lower()
        cl = " ".join(p.info["cmdline"] or [])
        if "powershell" in nm and "apexears" in cl.lower():
            victims.append(p.info["pid"])
            p.kill()
    except Exception:
        pass
print("[ears culled]:", victims or "(none were running)")

# 2. the fresh ears (the FIXED script: auth + -Text + reply-spoken)
sp.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
          "-WindowStyle", "Hidden", "-File",
          os.path.join(ROOT, "Scripts", "ApexEars.ps1")],
         cwd=ROOT, creationflags=0x00000008)
time.sleep(6)
alive = [p.info["pid"] for p in psutil.process_iter(["pid", "name", "cmdline"])
         if "powershell" in (p.info["name"] or "").lower()
         and "apexears" in " ".join(p.info["cmdline"] or []).lower()]
print("[ears alive on the fixed script]:", alive)

# 3. the send-lane proof (exactly what the ears now does)
KEY = open(os.path.join(ROOT, "Config", "apex_api.key"),
           encoding="utf-8-sig").read().strip()
try:
    r = rq.post("http://127.0.0.1:8080/talk/api",
                json={"message": "say one short sentence so I can hear you"},
                headers={"X-Apex-Key": KEY}, timeout=90)
    rep = (r.json() or {}).get("reply", "")[:90]
    print(f"[blocking-lane] HTTP {r.status_code} reply: {rep}")
except Exception as e:
    print("[blocking-lane]", type(e).__name__, str(e)[:80])

# 4. the stream lane + the serve's honest lane-tag
try:
    t0 = time.time()
    rr = rq.post("http://127.0.0.1:8080/talk/api/stream",
                 json={"message": "ping the stream lane once"},
                 headers={"X-Apex-Key": KEY}, stream=True, timeout=(8, 90))
    first = None
    n = 0
    for line in rr.iter_lines(decode_unicode=True):
        if line and line.startswith("data:"):
            n += 1
            if first is None:
                first = round(time.time() - t0, 2)
            if n >= 3:
                break
    print(f"[stream-lane] HTTP {rr.status_code} ttft~{first}s "
          f"(events={n}, raw-shape now visible in the log row)")
except Exception as e:
    print("[stream-lane]", type(e).__name__, str(e)[:80])
time.sleep(2)
log = os.path.join(ROOT, "Logs", "system.log")
if os.path.exists(log):
    tail = open(log, encoding="utf-8-sig", errors="ignore").readlines()[-4:]
    print("[system.log tail]:")
    for l in tail:
        print("  ", l.strip()[:105])
ram = psutil.virtual_memory()
print(f"[RAM] {ram.available / 2**30:.1f}GB free ({ram.percent}% used)")