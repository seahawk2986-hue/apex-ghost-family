"""Read-only probe: what job holds the busy slot, and does a DELETE route exist?"""
import io
import json
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = "http://127.0.0.1:8788"

try:
    with urllib.request.urlopen(BASE + "/v2/jobs", timeout=10) as r:
        body = json.loads(r.read().decode("utf-8"))
    jobs = body.get("jobs") if isinstance(body, dict) else body
    print("[jobs route]:", (body.get("jobs") if isinstance(body, dict) and "jobs" in body
                            else "raw keys: " + ", ".join(sorted(body)[:8]) if isinstance(body, dict) else "list"))
    if isinstance(jobs, list):
        for j in jobs[-8:]:
            if isinstance(j, dict):
                print("   rid", str(j.get("request_id") or j.get("rid"))[:8],
                      "| state", j.get("state"),
                      "| pending", str(j.get("pending_terminal_state") or "-")[:20],
                      "| cancelled", j.get("cancelled"))
except Exception as e:
    print("[probe error]:", type(e).__name__, str(e)[:120])