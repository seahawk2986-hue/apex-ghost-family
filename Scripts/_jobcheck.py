"""THE JOB-CHECK: the latest watch-run's STEPS (the exact failing step)."""
import json
import sys
import urllib.request

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import PatchStep as PS

tok = PS.token()
H = {"Authorization": "Bearer " + tok, "Accept":
     "application/vnd.github+json", "User-Agent": "apex-recheck/1.0"}
REPO = "seahawk2986-hue/apex-ghost-family"
r = urllib.request.urlopen(urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/actions/workflows/"
    f"apex-watch.yml/runs?per_page=1", headers=H), timeout=30)
run = json.loads(r.read().decode()).get("workflow_runs", [{}])[0]
rid = run.get("id")
print(f"[job-check] the run {rid}: {run.get('conclusion')}")
j = urllib.request.urlopen(urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/actions/runs/{rid}/jobs",
    headers=H), timeout=30)
for job in json.loads(j.read().decode()).get("jobs", []):
    print(f"  job: {job.get('name')} -> {job.get('conclusion')}")
    for s in job.get("steps", []):
        print(f"    step: {s.get('name')} -> {s.get('conclusion')}")