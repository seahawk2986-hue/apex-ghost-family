"""Registry report: every job, state, and the slot-holder(s)."""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"C:\Users\seaha\Apex-Adapter\jobs_registry.json"
data = json.load(open(P, encoding="utf-8"))
jobs = data.get("jobs", {})
print("[jobs total]:", len(jobs))
for rid, rec in jobs.items():
    print("   ", rid[:8], "|", rec.get("state"),
          "| pending:", str(rec.get("pending_terminal_state") or "-")[:16],
          "| cancelled:", rec.get("cancelled"))
slot = data.get("_slot")
print("[_slot]:", str(slot)[:40])
print("[stuck jobs]:",
      [r[:8] for r, rec in jobs.items()
       if rec.get("state") not in ("succeeded", "failed", "cancelled")])