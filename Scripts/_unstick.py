"""Unstick: DELETE the orphaned busy-slot job via the designed cancel route."""
import io
import json
import sys
import time
import urllib.error
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = "http://127.0.0.1:8788"
P = r"C:\Users\seaha\Apex-Adapter\jobs_registry.json"
A = r"C:\Users\seaha\Apex-Adapter"
TOKEN = open(A + "\\adapter_token.txt", encoding="ascii").read().strip()
H = {"Authorization": "Bearer " + TOKEN}

jobs = json.load(open(P, encoding="utf-8")).get("jobs", {})
stuck = [rid for rid, rec in jobs.items()
         if rec.get("state") not in ("succeeded", "failed", "cancelled")]
print("[stuck]:", stuck)

for rid in stuck:
    req = urllib.request.Request(BASE + "/v2/jobs/" + rid, method="DELETE",
                                 headers=H)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print("[DELETE", rid[:8] + "]:", r.status, r.read().decode("utf-8")[:100])
    except urllib.error.HTTPError as e:
        print("[DELETE", rid[:8] + "]: HTTP", e.code, e.read().decode("utf-8")[:100])
    except Exception as e:
        print("[DELETE", rid[:8] + "] error:", type(e).__name__, str(e)[:80])

time.sleep(5)
data = json.load(open(P, encoding="utf-8"))
print("[_slot after]:", str(data.get("_slot"))[:40] or "(released)")
for rid in stuck:
    rec = data.get("jobs", {}).get(rid, {})
    print("[state", rid[:8] + "]:", rec.get("state"),
          "| pending:", str(rec.get("pending_terminal_state") or "-")[:16])