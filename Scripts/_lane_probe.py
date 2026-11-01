"""THE LANE-PROBE: (1) the apex-watch runs (the schedule's fires?),
(2) the workflow's parse-state via the dispatch-detail (the body!), (3)
the run-41336109312's identity (the leak-check: was it ever OURS?)."""
import json
import sys
import time
import urllib.request

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PatchStep as PS

tok = PS.token()
H = {"Authorization": "Bearer " + tok, "Accept":
     "application/vnd.github+json", "User-Agent": "apex-lane/1.0"}
REPO = "seahawk2986-hue/apex-ghost-family"
base = f"https://api.github.com/repos/{REPO}/actions"

# (1) the runs
runs = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{base}/workflows/apex-watch.yml/runs?per_page=6", headers=H),
    timeout=30).read()).get("workflow_runs", [])
print(f"[lane] our workflow's runs total={len(runs)}")
for x in runs:
    print(f"  {x.get('created_at')} ev={x.get('event')} "
          f"-> {x.get('status')}/{x.get('conclusion')} "
          f"id={str(x.get('id'))[:12]}")

# (2) the run-41336109312's identity (was it REALLY named ApexWatchLane?)
det = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{base}/runs/41336109312", headers=H), timeout=30).read())
print(f"[lane] run-4133: name={det.get('name')} path={det.get('path')} "
      f"event={det.get('event')}")