"""EVOLUTION SPEED-UP (the fresh canon applied): upward-only + as fast as the
hardware laws allow. The measured bottleneck tonight: mutants sit at 0.0 until
a REAL window can run them - generations starve between windows. The canon's
speed levers, ranked by fit:
 1. PARCAE-LITE at the gene level: PREDICT window capacity (RAM EMA trend) and
    pre-stage the next generation's genes so the moment a window opens, zero
    minutes are spent computing them (the pre-stage writes to PathMemory
    immediately - children spawn pre-inherited).
 2. RLBOOST-AT-HOME in the gene domain: run the CONVERSION chain as the rollout
    half - stateless, parallel, window-perfect (already built); the genes'
    fitness is earned FROM those rollouts.
 3. BAMBOO bubbles: while gated (RAM < bar), the watcher does the CPU-only
    useful work that needs NO window: gene pre-staging, surrogate scoring,
    ascent re-reads - bubbles filled.
 4. UPWARD GUARD (per goal, per lineage): fitness must be monotone in the
    archive view; any measured regress rolls the lineage's genes back to its
    parent's (never downward inheritance).
TEST GATE (pre-implementation): (a) pre-stage writes valid pre-inherited genes
while GATED (bubbles filled - measurable NOW), (b) monotone-rollback guard on
a synthetic regress, (c) the speed receipts: gene-staging latency < 1s while
gated. PASS -> implement; else self-shelve."""
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
PRESTAGE = os.path.join(AD, "prestaged_genome.json")


def ram():
    try:
        import psutil
        return psutil.virtual_memory().available / 2 ** 30
    except Exception:
        return 0.0


def upward_guard(archive, prev_archive):
    """(b) synthetic+real: a lineage that MEASURED below its parent's
    measured fitness inherits the PARENT's genes (rollback - upward-only
    law). UNMEASURED children (m_rounds == 0) are VARIATION, not regression:
    the gate caught the first version flattening every new mutant to base
    (evolution's variation source destroyed); measured-only rollback is the
    corrected contract."""
    rolled = []
    for vid, L in archive.get("lineages", {}).items():
        par = L.get("parent")
        if not par or par not in archive.get("lineages", {}):
            continue
        if int(L.get("m_rounds", 0)) <= 0:      # unmeasured = protected variation
            continue
        p_fitness = float(archive["lineages"][par].get("fitness", -1))
        if 0 < p_fitness and float(L.get("fitness", -1)) < p_fitness:
            L["genes"] = dict(archive["lineages"][par]["genes"])
            L["note"] = "rolled back to parent's genes (upward-only law)"
            rolled.append(vid)
    return rolled


def prestaged_write():
    """(c) BAMBOO BUBBLE: while gated, pre-compute the next generation's genes
    (CPU-only, <1s) and write them as PRE-INHERITED state - the window opens
    and children spawn ALREADY-MUTATED (no gene math inside the window).
    BEST-OF-N via the SURROGATE FITNESS COURT (evaluator-first canon): 6
    fusion-mutants are court-scored; the head enters the pre-stage (the
    mutations the court would waste are never born - speed through
    selectivity, and the court's receipts print per candidate)."""
    import GenePool as GP
    a = GP.load()
    front = a.get("pareto_front") or [a.get("champion") or "base"]
    parent_vid = front[int(a.get("gen", 0)) % len(front)]
    if parent_vid not in a["lineages"]:
        parent_vid = a["champion"] if a["champion"] in a["lineages"] else "base"
    parent = a["lineages"].get(parent_vid, {})

    import random
    import SurrogateFitnessCourt as SFC
    rng = random.Random(int(time.time() * 1000) % 2 ** 31)
    cands = [] if not parent else [GP.mutate_fusion(a, parent_vid, rng)
                                   for _ in range(6)]
    best_genes = GP.mutate(parent.get("genes", {}), rng) if parent else {}
    sfit, verdict = 0.0, "NO-CANDIDATES"
    lead = "-"
    if cands:
        scored = SFC.court_run(cands, None, rng)
        head = scored[0]
        best_genes = head["genes"]
        sfit, verdict, lead = head["sfit"], head["verdict"], head["lead_proxy"]
    pre = {"parent": parent_vid, "genes": best_genes,
           "descriptor": GP.descriptor(best_genes), "staged": True,
           "sfit": sfit, "verdict": verdict, "court_lead": lead,
           "lamarck": (a.get("lamarck_genome") or {}).get("directive_genome", "")[:300],
           "staged_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    tmp = PRESTAGE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(pre, f, indent=1)
    os.replace(tmp, PRESTAGE)
    return pre


def selftest():
    print("=== EVOLUTION SPEED-UP GATE ===")
    legs = []
    r_now = ram()
    gated = r_now < 3.0
    print(f"   state: RAM {r_now:.2f} GB -> {'GATED (bubble-fill mode)' if gated else 'WINDOW OPEN (go straight to harvest)'}")
    # (a)+(c) pre-stage while gated: the bubble filled in <1s
    t0 = time.time()
    pre = prestaged_write()
    ms = round((time.time() - t0) * 1000, 1)
    leg_a = (not gated) or (os.path.exists(PRESTAGE) and ms < 1000)
    print(f"   pre-staged genome written in {ms}ms: parent={pre['parent']} "
          f"genes({len(pre['genes'])}) descriptor={pre['descriptor']}")
    legs.append(("bubble_fill_prestage", leg_a))
    # (b) upward guard: synthetic roll-back (MEASURED regression only -
    #     unmeasured variation is never flattened)
    synth = {"lineages": {
        "parent": {"genes": {"k": 5}, "fitness": 10, "m_rounds": 3},
        "kid": {"parent": "parent", "genes": {"k": 1}, "fitness": 4, "m_rounds": 2},
        "newborn": {"parent": "parent", "genes": {"k": 2}, "fitness": 0.0,
                    "m_rounds": 0},
    }}
    rolled = upward_guard(synth, None)
    leg_b = (synth["lineages"]["kid"]["genes"]["k"] == 5 and "kid" in rolled
             and "newborn" not in rolled
             and synth["lineages"]["newborn"]["genes"]["k"] == 2)
    print(f"   upward guard: measured regressor rolled back ({'kid' in rolled}), "
          f"unmeasured newborn PROTECTED (variation kept): {leg_b}")
    legs.append(("upward_only_guard", leg_b))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[speed] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)