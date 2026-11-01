"""THE ETA: how long does one comb-pass take, how many done, when done."""
import json
import os
import time

LEDGER = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "Config", "comb_passes.jsonl")
rows = []
for l in open(LEDGER, encoding="utf-8"):
    if l.startswith("{"):
        try:
            rows.append(json.loads(l))
        except Exception:
            pass
now = time.time()
recent = [r for r in rows
          if now - time.mktime(time.strptime(
              r["ts"], "%Y-%m-%d %H:%M:%S")) < 2400
          and isinstance(r.get("pass_no"), int)]
print(f"passes completed in the current 10-pass run: {len(recent)}/10")
if len(recent) >= 2:
    ts = [time.mktime(time.strptime(r["ts"], "%Y-%m-%d %H:%M:%S"))
          for r in recent]
    spans = [b - a for a, b in zip(ts, ts[1:])]
    for r, s in zip(recent[1:], spans):
        print(f"  pass {r['pass_no']}: {s:.0f}s | "
              f"findings={r['bug_count']}")
    avg = sum(spans) / len(spans)
    left = 10 - len(recent)
    print(f"avg per-pass: {avg:.0f}s")
    print(f"ETA: {avg * left / 60:.1f} min ({left} passes left)")
    print("findings so far:", {r["bug_count"] for r in recent})
elif recent:
    print("pass 1 = mid-flight; the per-pass rate measures after pass 2")
print(f"ledger size: {os.path.getsize(LEDGER) / 2**20:.2f}MB")