"""THE CRON-LANE RECHECK (the never-verified lane): the apex-watch.yml's
REAL runs on THEIR machines (the */5 cadence since registration) + the
latest run's jobs/conclusions."""
import json
import sys
import time
import urllib.request

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PatchStep as PS

tok = PS.token()
H = {"Authorization": "Bearer " + tok, "Accept":
     "application/vnd.github+json", "User-Agent": "apex-recheck/1.0"}
REPO = "seahawk2986-hue/apex-ghost-family"
r = urllib.request.urlopen(urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/actions/workflows/"
    f"apex-watch.yml/runs?per_page=5", headers=H), timeout=30)
d = json.loads(r.read().decode())
runs = d.get("workflow_runs", [])
print(f"[cron-recheck] total runs: {d.get('total_count', 0)}")
for x in runs[:5]:
    print(f"  {x.get('created_at')} {x.get('event')} -> "
          f"{x.get('status')} / {x.get('conclusion')}")