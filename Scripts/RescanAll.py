"""RESCAN ALL - the ONE-COMMAND master auditor: the complete line-vs-canon
chain, in order, each step's verdict printed and collected into ONE report
(Config/rescan_master.json):
 1 CapabilityRescan (canon x codebase gap matrix)
 2 CodeProfiler (AST + pyflakes + bandit + tools inventory)
 3 BoundedPlanner (the search instrument)
 4 RewardIntegrity (the theater detector)
 5 GoalCoherence (the clash check)
 6 BacklogIntegrity (the truth in the backlog)
 7 the 16-organ reproducibility suite (RepeatTest, both passes)
 8 the sources audit (the canon + receipts)
 9 the spec recheck (the 14 function-level specs)
The rescan_all gate: every collected rc==0 (or the step honestly FAILs the
master (rc!=0 -> verdict GAPS; nothing hidden)."""
import json
import os
import subprocess
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
S = os.path.join(ROOT, "Scripts")
OUT = os.path.join(ROOT, "Config", "rescan_master.json")
CHAIN = [
    ("capability_rescan", "CapabilityRescan.py"),
    ("paper_tools", "PaperTools.py"),
    ("code_profiler", "CodeProfiler.py"),
    ("bounded_planner", "BoundedPlanner.py"),
    ("reward_integrity", "RewardIntegrity.py"),
    ("goal_coherence", "GoalCoherence.py"),
    ("backlog_integrity", "BacklogIntegrity.py"),
    ("sources_audit", "_sources_audit.py"),
    ("spec_recheck", "_spec_recheck.py"),
    ("the_full_suite_x2", "RepeatTest.py"),
]


def main():
    t0 = time.time()
    steps = []
    for name, script in CHAIN:
        t1 = time.time()
        try:
            r = subprocess.run([sys.executable, os.path.join(S, script)],
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               timeout=1800, cwd=ROOT)
            rc, tail = r.returncode, (r.stdout or "").strip().splitlines()
            verd = next((l.strip() for l in tail
                         if "VERDICT:" in l or "FINAL" in l and "PASS" in l),
                        (tail[-1][:90] if tail else "?"))
        except Exception as e:
            rc, verd = -1, f"crashed: {str(e)[:80]}"
        steps.append({"step": name, "script": script, "rc": rc,
                      "s": round(time.time() - t1, 1), "verdict": verd[:120]})
        print(f"[rescan-all] {name}: rc={rc} ({steps[-1]['s']}s) {verd[:110]}")
    ok = all(s["rc"] == 0 for s in steps)
    rep = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "wall_min": round((time.time() - t0) / 60, 1),
           "steps": steps,
           "verdict": "THE COMPLETE RESCAN: every step green" if ok
           else "GAPS (see steps)"}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    os.replace(tmp, OUT)
    print(f"[rescan-all] {rep['verdict']} in {rep['wall_min']}min")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)