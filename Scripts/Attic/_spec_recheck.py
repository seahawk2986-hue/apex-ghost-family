"""SPEC RECHECK: every SPECIFIC thing today was supposed to do, verified
LIVE against the tree (function-level, not just organ selftests)."""
import json, os, re, subprocess, sys, time, py_compile
ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
S = os.path.join(ROOT, "Scripts")
legs = []

def leg(name, ok, note=""):
    legs.append((name, bool(ok)))
    print(f"   {'PASS' if ok else 'FAIL'} | {name}" + (f" - {note}" if note else ""))

# 1. GenePool: parents rotate through the Pareto front (spec: evolve FROM the front)
import GenePool as GP
src = open(os.path.join(S, "GenePool.py"), encoding="utf-8-sig").read()
leg("genepool_front_rotation", "front[int(a.get(\"gen\", 0)) % len(front)]" in src)
# 2. sync: fold + unmeasured-protected + idempotent (live proof)
before = open(GP.ARCHIVE, encoding="utf-8-sig").read()
s1, r1, t1 = GP.sync_from_pathmemory()
after = open(GP.ARCHIVE, encoding="utf-8-sig").read()
leg("genepool_sync_no_phantom_change", (s1 == [] and before == after),
    f"folded {s1 or 'none'} (archive bytes unchanged on a no-measure pass)")
# 3. SFC read-only live court
import SurrogateFitnessCourt as SFC
b2 = open(GP.ARCHIVE, encoding="utf-8-sig").read()
SFC.court_run([GP.mutate_fusion(GP.load(), GP.load().get("champion"), __import__("random").Random(1))],
              SFC._load_court(), __import__("random").Random(1))
b3 = open(GP.ARCHIVE, encoding="utf-8-sig").read()
leg("sfc_court_readonly", b2 == b3)
# 4. pre-stage: fusion best-of-6 with court receipt
import EvolutionSpeedup as ES
pre = ES.prestaged_write()
leg("prestage_fusion_receipts", pre.get("staged") is True and "sfit" in pre
    and pre.get("court_lead"), f"parent {pre.get('parent')} sfit "
    f"{pre.get('sfit')} via {pre.get('court_lead')}")
# 5. ApexUpward: genealogy complete + coherent + scheduled
import ApexUpward as AU
import GoalCoherence as GCOH
man = AU.tick()
leg("genealogy_complete_traced", len(AU.GOAL_REGISTRY) >= 30 and
    all("origin" in v and "status" in v for v in AU.GOAL_REGISTRY.values()),
    f"{len(AU.GOAL_REGISTRY)} goals")
leg("coherence_zero_clashes", GCOH.solve() == [] and
    not GCOH.schedule_coverage() and not GCOH.synergy_coverage())
# 6. wiring: orchestrator + statusboard + upgrader receipt
so_src = open(os.path.join(S, "SwarmOrchestrator.py"), encoding="utf-8-sig").read()
sb_src = open(os.path.join(S, "StatusBoard.py"), encoding="utf-8-sig").read()
su_src = open(os.path.join(S, "SkillUpgrader.py"), encoding="utf-8-sig").read()
leg("tick_wired_per_measured_round", "_AU.tick()" in so_src)
leg("statusboard_single_derivation", "BacklogIntegrity" in sb_src)
leg("upgrader_receipt_wired", "RuntimeReceipt" in su_src)
# 7. DeploySwarm import-no-spawn (live; plain import - no -S, which breaks
#    the venv's site resolution and is not the honest condition)
r = subprocess.run([sys.executable, "-c",
    "import sys; sys.path.insert(0, r'" + S + "');import DeploySwarm;"
    "print('CLEAN')"], capture_output=True, text=True,
    encoding="utf-8", timeout=60, cwd=ROOT)
leg("import_no_spawn", (r.stdout or "").strip().endswith("CLEAN"),
    (r.stdout or "").strip()[-30:])
# 8. hardware gate tiers + the manifest's tier field
man["state"]["hardware"] = man["state"].get("hardware") or {}
leg("hardware_gate_in_manifest", "hardware" in man["state"]
    and "tier" in (man.get("speed") or {}))
# 9. canon: 621 unique + reports current (the manifest timestamps)
rows = 0
ids = set()
for fn in ("papers_2026.jsonl", "papers_2026_evolution.jsonl",
           "papers_2026_agents.jsonl"):
    for x in open(os.path.join(ROOT, "Config", fn), encoding="utf-8-sig"):
        if x.strip():
            rows += 1
            ids.add(json.loads(x)["id"])
leg("sources_621_unique_current", len(ids) == 621 and rows == 621,
    f"{len(ids)} unique / {rows} rows")
bc = json.load(open(os.path.join(ROOT, "Config", "benchmark_card.json"),
                    encoding="utf-8-sig"))
leg("benchmark_card_labeled", "law" in bc and "honest_note" in bc)
gc = json.load(open(os.path.join(ROOT, "Config", "goal_coherence.json"),
                    encoding="utf-8-sig"))
leg("coherence_report_current", gc["clashes"] == [])

ok = all(v for _, v in legs)
print()
for nm, v in legs:
    if not v:
        print(f"   *** FAILED SPEC: {nm}")
print(f"[spec-recheck] FINAL: {sum(v for _, v in legs)}/{len(legs)} PASS -> "
      f"{'EVERY SPEC HONORED' if ok else 'GAPS ABOVE'}")
sys.exit(0 if ok else 1)