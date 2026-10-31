"""test_reward.py - Offline unit test of Apex's multi-dimensional reward matrix."""
import json
import os
import sys

R = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, R)
LED = os.path.join(R, "Config", "RewardLedger.json")

with open(LED, "w", encoding="utf-8") as f:
    json.dump({}, f)

import run_apex_evolution as m  # noqa: E402

ok = []

def check(name, cond, detail=""):
    ok.append(bool(cond))
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}", flush=True)

# 1. Fresh success with proven output = exactly 100
r1 = m.score_code("t1.py", "print('hello')", {"status": "SUCCESS", "output": "hello"}, None)
check("fresh success scores 100.0", r1[0] == 100.0, f"got {r1[0]}")

# 2. Identical rewrite (same base) is flagged NO-OP -> can never pass gate
m._bump_ledger("t1.py", {"syntax": 30, "safety": 25, "runtime": 20, "output": 15}, 100.0, True)
r2 = m.score_code("t1.py", "print('hello')", {"status": "SUCCESS", "output": "hello"}, None)
check("identical rewrite flagged noop", bool(r2[1].get("noop")), f"score {r2[0]}")

# 3. Candidate below ledger best_base is flagged noop (regression gate)
m._bump_ledger("t2.py", {"syntax": 30, "safety": 25, "runtime": 20, "output": 15}, 900.0, True)
r3 = m.score_code("t2.py", "print('hi')", {"status": "SUCCESS", "output": "hi"}, None)
check("regression/noop below ledger best", bool(r3[1].get("noop")), f"score {r3[0]}")

# 4. Predecessor produced output, candidate silent -> BEHAVIOR LOSS
r4 = m.score_code("t3.py", "print('x')", {"status": "SUCCESS", "output": ""},
                  {"status": "SUCCESS", "output": "previous output existed"})
check("behavior loss flagged", bool(r4[1].get("behavior_loss")), f"score {r4[0]}")

# 5. Silent-predecessor parity is ACCEPTED (modules legitimately print nothing)
r5 = m.score_code("t4.py", "print('x')", {"status": "SUCCESS", "output": ""},
                  {"status": "SUCCESS", "output": ""})
check("silent parity accepted", r5[1].get("output") == 15, f"score {r5[0]}")

# 6. Full veto on mass-deletion / shell-out
r6 = m.score_code("t5.py", "import shutil\nshutil.rmtree('important_dir')",
                  {"status": "SUCCESS", "output": ""}, None)
check("shutil.rmtree full veto fires", r6[0] == 0.0, f"score {r6[0]} safety {r6[1].get('safety')}")

# 7. Casual os.remove is penalized below the write gate (not annihilated)
r7 = m.score_code("t6.py", "import os\nos.remove('x')", {"status": "SUCCESS", "output": "x"}, None)
check("os.remove penalized below gate", r7[0] < 100.0 and r7[1].get("safety", 25) < 25,
      f"score {r7[0]} safety {r7[1].get('safety')}")

# 7. Ledger persists per-file stats
lg = m._load_ledger()
check("ledger tracks t1 best/streak", lg.get("t1.py", {}).get("best", 0) >= 100.0,
      f"best {lg.get('t1.py', {}).get('best')}")

with open(LED, "w", encoding="utf-8") as f:
    json.dump({}, f)

score = f"{sum(ok)}/{len(ok)}"
with open(r"C:\Users\seaha\Apex-Adapter\reward_test.txt", "w", encoding="utf-8") as f:
    f.write(score + "\n")
print(f"REWARD MATRIX: {score}", flush=True)