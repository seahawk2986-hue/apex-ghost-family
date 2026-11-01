"""THE ACTIVE-JOBS SCANNER (the founder's question): the machine-cadences
+ the local-actives + the runners' latest receipts."""
import json
import os
import subprocess
import psutil

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"

print("== the machine-scheduler (schtasks) ==")
r = subprocess.run(["schtasks", "/Query", "/FO", "CSV", "/NH"],
                   capture_output=True, text=True)
for ln in (r.stdout or "").splitlines():
    if "Apex" in ln:
        parts = [x.strip('"') for x in ln.split('","')]
        if len(parts) >= 3:
            print(f"  {parts[0]} | status={parts[2]} | next={parts[1] if len(parts)>1 else '?'}")

print("== the LOCAL running python-organs ==")
n = 0
for p in psutil.process_iter(["pid", "cmdline", "name"]):
    try:
        cl = " ".join(p.info["cmdline"] or [])
        if "apex_venv" in cl and "python" in (p.info["name"] or "").lower():
            fn = os.path.basename((p.info["cmdline"] or [""])[-1]) if p.info["cmdline"] else "?"
            print(f"  pid {p.info['pid']}: {fn}")
            n += 1
    except Exception:
        pass
print(f"  (total: {n})")

print("== the GitHub-runs' latest (their machines) ==")
try:
    sys_path = os.path.join(ROOT, "Scripts")
    import sys as _s
    _s.path.insert(0, sys_path)
    import PatchStep as PS
    import urllib.request
    H = {"Authorization": "Bearer " + PS.token(), "Accept":
         "application/vnd.github+json", "User-Agent": "apex/1.0"}
    for wf in ("apex-watch.yml", "apex-prlane.yml", "apex-hub.yml"):
        try:
            r = urllib.request.urlopen(urllib.request.Request(
                f"https://api.github.com/repos/seahawk2986-hue/apex-ghost-family"
                f"/actions/workflows/{wf}/runs?per_page=1", headers=H), timeout=30)
            x = json.loads(r.read().decode()).get("workflow_runs", [{}])[0]
            print(f"  {wf}: {x.get('created_at')} {x.get('event')} -> "
                  f"{x.get('status')}/{x.get('conclusion')}")
        except Exception as e:
            print(f"  {wf}: {str(e)[:60]}")
except Exception as e:
    print(f"  the runners-read honest: {str(e)[:60]}")