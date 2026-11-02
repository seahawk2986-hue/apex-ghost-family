"""THE ARM-CHECK: the RAM-window + the hub-lane's latest runs (the
runner-side = the = the = = = = = = = = = = = = = = = = = = = = = = =)"""
import json
import os
import sys
import urllib.request

import psutil

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
os.chdir(ROOT)
sys.path.insert(0, "Scripts")
free = psutil.virtual_memory().available / 2 ** 30
print(f"[RAM]: {free:.2f}GB free (the whisper-small-int8 lane needs ~1GB + the headroom)")
print("[RAM-verdict]:", "GO" if free >= 3.0 else "HOLD (wait for the window)")

try:
    import PatchStep as PS
    H = {"Authorization": "Bearer " + PS.token(),
         "Accept": "application/vnd.github+json"}
    r = urllib.request.urlopen(urllib.request.Request(
        "https://api.github.com/repos/seahawk2986-hue/apex-ghost-family"
        "/actions/runs?per_page=5", headers=H), timeout=25)
    runs = json.loads(r.read().decode()).get("workflow_runs", [])
    for x in runs:
        print(f"[run] {x.get('name','?')[:22]} {str(x.get('created_at'))[:16]} "
              f"{x.get('status')}/{x.get('conclusion')}")
except Exception as e:
    print("[runs-read honest]:", str(e)[:80])