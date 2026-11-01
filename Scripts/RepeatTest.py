"""REPEATED TEST RUNNER: every evolution organ's gate, run TWICE with the
same parameters. A gate that passes once but flakes on the identical repeat
is not a gate - the family only ships organs whose gates are REPRODUCIBLE."""
import subprocess
import sys
import time

PY = sys.executable
SCRIPTS = sys.prefix and r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts"
ORGS = ("SurrogateFitnessCourt.py", "GenePoolTest.py",
        "EvolutionSpeedup.py", "ApexUpward.py", "CalibratedEvolution.py",
        "RuntimeReceipt.py", "LongHorizonSpecs.py", "ConsolidateLessons.py",
        "BenchmarkCard.py", "SkillGapScout.py", "GoalComparison.py",
        "GoalCoherence.py", "BacklogIntegrity.py",
        "CapabilityRescan.py", "BoundedPlanner.py", "RewardIntegrity.py",
        "CodeProfiler.py", "FullSweep.py")
# Run-on-demand ledger organs kept OUT of the automated double-pass:
# ConflictJsonRepair (a repair tool; re-running mutates gen counters) and
# PaperHarvest2/PaperHarvest3 (web fetchers, politeness-costly). Their own
# gates cover them; the suite covers every state-safe organ.
ROUND = 2
verdicts = {}
for rep in (1, 2):
    print(f"########## REPEAT RUN {rep} of {ROUND} (same parameters) ##########")
    for org in ORGS:
        t0 = time.time()
        r = subprocess.run([PY, SCRIPTS + "\\" + org], capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=600, cwd=r"C:\Users\seaha\Downloads"
                                              r"\Apex-With-Triggers-Fixed")
        ms = round((time.time() - t0) * 1000)
        tail = (r.stdout or "").strip().splitlines()
        ver = [x for x in tail if "VERDICT" in x or "GATE VERDICT" in x]
        key = f"r{rep}:{org}"
        verdicts[key] = (r.returncode == 0, ver[0] if ver else "?", f"{ms}ms")
        print(f"[{org}] rc={r.returncode} ({ms}ms) -> "
              f"{ver[0] if ver else ('NO VERDICT LINE: ' + (tail[-1] if tail else 'silent'))}")
print()
print("=== REPRODUCIBILITY LEDGER (both repeats must PASS) ===")
ok_all = True
for k, (ok, ver, ms) in verdicts.items():
    ok_all = ok_all and ok
    print(f"   {'PASS' if ok else 'FAIL'} | {k} {ms} | {ver[:100]}")
n_orgs = len(ORGS)
r1 = all(verdicts[f'r1:{o}'][0] for o in ORGS)
r2 = all(verdicts[f'r2:{o}'][0] for o in ORGS)
print(f"[repeat] FINAL: run1 {'ALL PASS' if r1 else 'FAIL'} | "
      f"run2 {'ALL PASS' if r2 else 'FAIL'} -> "
      f"{'REPRODUCIBLE - SHIP' if r1 and r2 else 'NOT SHIPPABLE'}")
sys.exit(0 if ok_all else 1)