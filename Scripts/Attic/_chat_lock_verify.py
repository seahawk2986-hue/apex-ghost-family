"""THE CHAT-LOCK'S AUTH-ED VERIFY: the key (the never-printed = the
header-consume) + the ask. The verdict = the honest."""
import json
import os
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
KEY = open(os.path.join(ROOT, "Config", "apex_api.key"),
           encoding="utf-8-sig").read().strip()    # consumed; NEVER printed

# the serve's relaunch-check (the new-code = the restart's = the pid?)
import psutil
serve = [p for p in psutil.process_iter(["pid", "cmdline"])
         if "run_apex_evolution" in " ".join(p.info["cmdline"] or [])]
print(f"[serve] pids: {[p.info['pid'] for p in serve]}")

ask = {"message": "which model are you using for this chat?"}
req = urllib.request.Request(
    "http://127.0.0.1:8080/talk/api", data=json.dumps(ask).encode(),
    headers={"Content-Type": "application/json",
             "X-Apex-Key": KEY}, method="POST")
try:
    d = json.loads(urllib.request.urlopen(req, timeout=150).read())
    rep = (d or {}).get("reply", "")
    print("[verify] the REPLY:", rep[:300])
    live = ("gpt-oss" in rep.lower() or "120b" in rep)
    print("[verify] THE CHAT-LOCK =",
          ("LIVE (the 120b speaks)" if live else
           "CANDOR-or-CHECK: " + ("granted-rate" if "quota" in
                                  rep.lower() or "rate" in rep.lower()
                                  else "the answer's read")))
except Exception as e:
    print("[verify] honest:", str(e)[:90])