"""THE DISPATCH-RETRY: wait for the workflow-registration, dispatch once,
verify the real run (+ the actions-lane step popping the off-box work)."""
import json
import sys
import time
import urllib.request

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PatchStep as PS

tok = PS.token()
H = {"Authorization": "Bearer " + tok,
     "Accept": "application/vnd.github+json",
     "User-Agent": "apex-watch/1.0"}
REPO = "seahawk2986-hue/apex-ghost-family"

for attempt in range(2):
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/actions/workflows",
            headers=H), timeout=30)
        ws = json.loads(r.read().decode()).get("workflows", [])
        names = [w.get("path", w.get("name")) for w in ws]
        print("registered workflows:", names)
        if any("apex-watch" in str(n) for n in names):
            req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/actions/workflows/"
                f"apex-watch.yml/dispatches",
                data=json.dumps({"ref": "main"}).encode(), headers=H,
                method="POST")
            urllib.request.urlopen(req, timeout=30)
            print("DISPATCHED (registered now)")
            time.sleep(40)
            r2 = urllib.request.urlopen(urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/actions/workflows/"
                f"apex-watch.yml/runs?per_page=2", headers=H), timeout=30)
            for x in json.loads(r2.read().decode()).get("workflow_runs", []):
                print(f"run {x.get('id')} status={x.get('status')} "
                      f"conclusion={x.get('conclusion')} "
                      f"event={x.get('event')}")
            break
    except Exception as e:
        print(f"attempt {attempt}: {str(e)[:80]}")
        time.sleep(35)