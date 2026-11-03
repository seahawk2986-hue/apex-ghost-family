"""The smoothness gate: the near-cache's trust mechanics + the learner's
dispatch. Offline (no network); pass or fix."""
import io
import sys

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import ApexCache as C

fails = []

# seed: one validated entry
C.store("sim-seed", {"task": "repair divide, test 7/2 = 3.5"}, "local", "sim-test",
        "diff --- a/calc.py +++ b/calc.py --- divide", "validated")

# 1) an EXACT near-duplicate text -> the semantic path at >=0.90
reply, kind = C.cache_lookup_any("repair divide, test 7/2 = 3.5")
ok = reply is not None and kind in ("exact", "semantic")
print("[near-cache exact-ish]:", "PASS" if ok else "FAIL", "|", kind, "|", str(reply)[:40])
if not ok:
    fails.append("exact-replay")
# the reply = None-cached? -> the near path = the gate: <0.90 = refuse
reply2, kind2 = C.cache_lookup_any("totally unrelated quantum flux calibration task")
ok2 = (kind2 in ("none", "near")) and reply2 is None
print("[near-cache refuse-far]:", "PASS" if ok2 else "FAIL", "|", kind2)
if not ok2:
    fails.append("far")

# 2) the learner: record then promote
import CapabilityMap as CM
CM.record("chat", "nim-glm", True)
CM.record("chat", "nim-glm", True)
CM.record("chat", "nim-glm", True)
CM.record("chat", "gpt-oss-120b", False)
CM.record("chat", "gpt-oss-120b", False)
w = CM.best_for("chat", ["gpt-oss-120b", "nim-glm", "groq-qwen"])
ok3 = w == "nim-glm"
print("[learner promote]:", "PASS" if ok3 else "FAIL", "->", w)
if not ok3:
    fails.append("learner")

# 3) the Sharder's order still valid with the learner present
import ApexShard as S
order = S.order_for(code=True)
ok4 = order[0][0] == "local-coder" and len(order) >= len(S.LANES) - 2
print("[shard order with learner]:", "PASS" if ok4 else "FAIL", "| first:", order[0][0])
if not ok4:
    fails.append("order")

print("[verdict]:", "ALL PASS" if not fails else f"FAIL {fails}")
sys.exit(1 if fails else 0)