"""The fleet status: the honest per-lane state from the last LaneGuard pass."""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
st = json.load(open(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
                    r"\scores\lane_state.json", encoding="utf-8"))
for k, v in sorted(st.items()):
    http = str(v.get("last_http"))
    note = str(v.get("note") or "")[:55]
    print("%-16s http=%-4s %s" % (k, http, note))