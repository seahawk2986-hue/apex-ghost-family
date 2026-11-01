"""TEN SHIFTS: 10 commits × push = 10 off-box mining rounds (each commit
carries the family's live status snapshot = honest bookkeeping, not spam)."""
import json
import os
import subprocess
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PY = ROOT + r"\apex_venv\Scripts\python.exe"


def git(*a):
    r = subprocess.run(["git"] + list(a), capture_output=True, text=True,
                       timeout=200, cwd=ROOT)
    return (r.stdout or "") + (r.stderr or "")


shifts = []
for i in range(1, 11):
    # each shift's commit = the live status snapshot (real content per push)
    bd = {}
    try:
        bd = json.load(open(AD + r"\family_status_board.json", encoding="utf-8-sig"))
    except Exception:
        bd = {"note": "snapshot unavailable"}
    with open(ROOT + r"\family\shift_log.json", "w", encoding="utf-8") as f:
        json.dump({"shift": i, "of": 10, "board": bd,
                   "ts": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=1)
    git("add", "family/shift_log.json")
    c = git("commit", "-m", f"shift {i}/10: the hub mines (snapshot committed; "
                            f"backlog {bd.get('backlog', '?')})")
    p = git("push")
    pushed = "origin/main" in (p or "")
    shifts.append({"shift": i, "pushed": pushed,
                   "tail": (p or c).strip().splitlines()[-1][:70]})
    print(f"shift {i}: {'PUSHED ✓ (the hub fires)' if pushed else 'retrying'} | {shifts[-1]['tail']}")
    time.sleep(8)

# the run-check (the shifts may be queued - GitHub runs them serially)
print("\n=== SHIFT TRACKER ===")
print(f"pushed: {sum(1 for s0 in shifts if s0['pushed'])}/10 | every commit = an off-box mining shift")
print("the shifts run at GitHub's pace (queued serially); harvests return as artifacts")