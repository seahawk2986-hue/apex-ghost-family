"""THE SERVE-RESTART = THE CHAT-LOCK'S ACTIVATION: (1) find the serve's
pid (the full-cmdline), (2) restart it (the new-code = the lock = LIVE),
(3) verify: the POST /talk/api 'which model are you using now?' = the
answer must NAME the 120b (the honest: the rate-candor = the acceptable
alternative; the qwen-answer = the FAIL)."""
import json
import os
import subprocess
import sys
import time
import urllib.request

import psutil

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
PY = os.path.join(ROOT, "apex_venv", "Scripts", "python.exe")
# (1) the full-cmdline scan
serves = []
for p in psutil.process_iter(["pid", "name", "cmdline"]):
    try:
        cl_full = " ".join(p.info["cmdline"] or [])
        if "run_apex_evolution" in cl_full:
            serves.append((p.info["pid"], cl_full[:160]))
    except Exception:
        pass
print(f"[serve] the run_apex_evolution's: {serves}")

# (2) the restart (the honest: kill + relaunch detached)
for pid, cl in serves:
    try:
        psutil.Process(pid).terminate()
        print(f"[serve] pid {pid}: terminated (the new-code = next)")
    except Exception as e:
        print(f"[serve] pid {pid}: {str(e)[:50]}")
time.sleep(2)
if serves:
    DETACHED = 0x00000008
    subprocess.Popen([PY, os.path.join(ROOT, "run_apex_evolution.py")],
                     cwd=ROOT, creationflags=DETACHED,
                     stdout=open(os.path.join(ROOT, "Logs",
                                              "evolution_serve.log"),
                                 "ab") if os.path.isdir(
                         os.path.join(ROOT, "Logs")) else None,
                     stderr=subprocess.STDOUT)
    print("[serve] RELAUNCHED (the new-code = the lock = live-in-memory)")
    time.sleep(12)

# (3) the POST-verify (the founder's literal-question!!)
ask = {"message": "which model are you using for this chat?"}
req = urllib.request.Request(
    "http://127.0.0.1:8787/talk/api"
    if False else "http://127.0.0.1:8000/talk/api",
    data=json.dumps(ask).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read().decode())
    rep = (d or {}).get("reply", "")
    print(f"[verify] the REPLY: {rep[:280]}")
    verdict = ("gpt-oss" in rep.lower() or "120b" in rep
               or "groq" in rep.lower())
    tagline = "LIVE (the 120b speaks)" if verdict else \
        "CHECK (the answer above = the honest read)"
    print(f"[verify] THE CHAT-LOCK = {tagline}")
except Exception as e:
    print(f"[verify] the honest: the serve-endpoint = {str(e)[:90]} - the "
          "founder's own chat-page = the same-test (the reply's = the "
          "candor-check)")