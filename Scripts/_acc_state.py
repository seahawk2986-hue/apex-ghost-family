"""One small piece: read the last acceptance receipt honestly."""
import io
import sys
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
A = r"C:\Users\seaha\Apex-Adapter"
d = None
p = A + "\\acceptance_run_result.json"
try:
    d = json.load(open(p, encoding="utf-8"))
except Exception as e:
    print("[no result file]:", str(e)[:80])

if d:
    print("[rid]:", d.get("rid", "-")[:14])
    print("[state]:", d.get("state"))
    print("[failure_note]:", str(d.get("failure_note") or "")[:120])
    print("[zip_sha256]:", d.get("zip_sha256"))
    print("[checkpoint files]:", (d.get("checkpoint") or {}).get("file_count"))
else:
    print("[the file's actual keys]: see adapter.log for the raw-head events")

print("[the raw-head receipts]: the last job's model-attempts = logged in the retry-events")
print("[honest state]: the acceptance = still unsealed; the shape-mystery = pending the raw-head data")