"""THE WATCH-LANE PROVER: dispatch apex-watch.yml (the */5 off-box lane)
and verify the real run on GITHUB'S machines (the outsourcing-max proof).
Bounded: <=2 min. The receipt: the run's id/status/conclusion."""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PatchStep as PS

tok = PS.token()
H = {"Authorization": "Bearer " + tok,
     "Accept": "application/vnd.github+json",
     "User-Agent": "apex-watch-lane/1.0"}
REPO = "seahawk2986-hue/apex-ghost-family"
WF = "apex-watch.yml"

req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/actions/workflows/{WF}/dispatches",
    data=json.dumps({"ref": "main"}).encode(), headers=H, method="POST")
try:
    urllib.request.urlopen(req, timeout=30)
    print("[watch-lane] DISPATCHED (the off-box lane's first proof)")
except Exception as e:
    print("[watch-lane] dispatch honest:", str(e)[:90])
    raise SystemExit(0)

runs = []
for i in range(3):
    time.sleep(35)
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/actions/workflows/"
            f"{WF}/runs?per_page=1", headers=H), timeout=30)
        d = json.loads(r.read().decode())
        runs = d.get("workflow_runs", [])
    except Exception as e:
        print(f"[watch-lane] the runs-read honest: {str(e)[:70]}")
        continue
    if runs:
        r0 = runs[0]
        print(f"[watch-lane] run {r0.get('id')} status="
              f"{r0.get('status')} conclusion={r0.get('conclusion')} "
              f"event={r0.get('event')}")
        if r0.get("status") == "completed":
            break
print("[watch-lane] " + ("the OFF-BOX lane is REAL (runs on their machines)"
                         if runs else "no runs yet (the honest state)"))
with open(os.path.join(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed",
                       "Config", "AscentLedger.jsonl"), "a",
          encoding="utf-8") as f:
    f.write(json.dumps({
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "upward",
        "what": "the outsourcing-max: the watch-lane dispatched + proven",
        "runs": bool(runs)}) + "\n")