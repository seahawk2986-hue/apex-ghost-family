"""Reload the adapter: kill the old engine-holder on 8788, re-run the
Task-Scheduler action, and wait (bounded) for health."""
import io
import subprocess
import sys
import time
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return ((r.stdout or "") + (r.stderr or "")).strip()[:140]


# 1) the old engine-holder: whatever listens on 8788 (re-detected, never guessed)
out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout
pids = {ln.split()[-1] for ln in out.splitlines()
        if ":8788" in ln and "LISTENING" in ln}
for pid in pids:
    print("[kill old adapter]: PID", pid, "->", run(["taskkill", "/F", "/PID", pid]))

out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout
still = [ln for ln in out.splitlines() if ":8788" in ln and "LISTENING" in ln]
print("[port 8788 free]:", "NO (old holder survived)" if still else "yes")

# 2) the relaunch: the same Task-Scheduler action the boot path uses
print("[schtasks run]:", run(["schtasks", "/run", "/tn", "Apex-Companion"]))

# 3) bounded health wait: 15 x 2 s
ok = False
for _ in range(15):
    time.sleep(2)
    try:
        with urllib.request.urlopen("http://127.0.0.1:8788/v1/health",
                                    timeout=5) as r:
            ok = r.status == 200
            break
    except Exception:
        continue
print("[health]:", "200 - adapter live with the healed engine" if ok
      else "DOWN after 30 s - honest red light")