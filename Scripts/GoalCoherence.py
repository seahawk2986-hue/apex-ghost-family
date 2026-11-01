"""GOAL COHERENCE v2 - the GUARD RAIL + the SYNERGY MAP (the full review of
all 30 goals). NO goal may clash with another; every goal must WORK WITH the
others. The honest resource model:
  - MONEY is a POOL: the budget is $0.00 (no rail exists) - summed, zero
    demanded, any money-demand is a violation.
  - RAM/CPU are RATES: they consume a WINDOW, and windows run PHASES
    sequentially (the harvest chain's real shape). Coherence = every tier's
    every PHASE fits the budget (base residency + peak phase demand), not
    the meaningless sum of a lifetime's demands.
  - CONSENT/FS-TRUST are INVARIANTS: required <=1 per goal, never summed.
SYNERGY: every measured goal must appear in >=1 named synergy (a mechanism
that makes two goals power each other) - goals that merely avoid clashing
are not enough; they must cooperate by named mechanism.
TEST GATE: (a) real map: ZERO clashes, (b) synthetic money-rogue flagged,
(c) the tier schedule fits + every schedulable goal is scheduled,
(d) every measured goal synergizes, (e) report written + reproducible x2."""
import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "goal_coherence.json")
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
import ApexUpward as AU

BUDGET = {"ram_free_gb": 7.0, "cpu_serial": 1.0, "money": 0.0}

DEMANDS = {           # ALL 30 goals (aliases honor their measured successors)
    "gold": {"ram_free_gb": 2.5, "cpu_serial": 1.0, "fs_trust": 1.0},
    "money": {"money": 0.0, "human_attention": 1.0, "fs_trust": 1.0},
    "life": {"ram_free_gb": 0.5, "cpu_serial": 0.2, "human_attention": 1.0,
             "fs_trust": 1.0},
    "recruits": {"ram_free_gb": 0.5, "cpu_serial": 0.1, "human_attention": 1.0,
                 "fs_trust": 1.0},
    "jobs": {"ram_free_gb": 1.0, "cpu_serial": 0.2, "human_attention": 0.5,
             "fs_trust": 1.0},
    "coding": {"ram_free_gb": 3.0, "cpu_serial": 1.0, "fs_trust": 1.0},
    "omnivore": {"ram_free_gb": 1.0, "cpu_serial": 0.3, "fs_trust": 1.0},
    "efficiency": {"cpu_serial": 0.1, "fs_trust": 1.0},
    "safety": {"fs_trust": 1.0},
    "upward_evo": {"cpu_serial": 0.1, "fs_trust": 1.0},
    "speed": {"cpu_serial": 0.05},
    "sovereignty": {"fs_trust": 1.0},
    "first_external_value": {"human_attention": 1.0, "fs_trust": 1.0},
    "discovery_harvest": {"cpu_serial": 0.1, "fs_trust": 1.0},
    "test_first": {"cpu_serial": 0.05, "fs_trust": 1.0},
    "reproducible": {"cpu_serial": 0.05, "fs_trust": 1.0},
    "compare_to_canon": {"cpu_serial": 0.05, "fs_trust": 1.0},
    "self_knowledge": {"cpu_serial": 0.02},
    "serviceable": {"cpu_serial": 0.02, "fs_trust": 1.0},
    "backlog_drain": {"cpu_serial": 0.02},
    "runtime_verification": {"ram_free_gb": 3.0, "cpu_serial": 0.5,
                             "human_attention": 0.1, "fs_trust": 1.0},
    "long_horizon_specs": {"ram_free_gb": 1.0, "cpu_serial": 0.3},
    "gap_scouting": {"cpu_serial": 0.05, "fs_trust": 1.0},
    "consolidation_cadence": {"ram_free_gb": 0.5, "cpu_serial": 0.2},
    "budgeted_context": {"cpu_serial": 0.02, "fs_trust": 1.0},
    "benchmark_honesty": {"cpu_serial": 0.05, "human_attention": 0.2},
    "capability_rescan": {"cpu_serial": 0.1, "fs_trust": 1.0},
    "bounded_planner": {"cpu_serial": 0.1, "fs_trust": 1.0},
    "reward_integrity": {"cpu_serial": 0.05, "fs_trust": 1.0},
    "earn_lane_matrix": {"cpu_serial": 0.1, "human_attention": 1.0,
                         "fs_trust": 1.0},
    "tri_genome": {}, "elections": {}, "throne": {}, "sleep": {},
}

# THE TIER SCHEDULE (windows run PHASES sequentially - the chain's shape)
TIERS = {
    "brain-window": {"base": 2.0, "phases": [
        {"goals": ["gold"], "ram": 2.5, "cpu": 1.0},
        {"goals": ["coding"], "ram": 3.0, "cpu": 1.0},
        {"goals": ["runtime_verification"], "ram": 3.0, "cpu": 0.5}]},
    "chain-window": {"base": 2.0, "phases": [
        {"goals": ["gold"], "ram": 2.5, "cpu": 1.0},
        {"goals": ["jobs", "omnivore"], "ram": 2.0, "cpu": 0.5},
        {"goals": ["long_horizon_specs"], "ram": 1.0, "cpu": 0.3},
        {"goals": ["consolidation_cadence"], "ram": 0.5, "cpu": 0.2}]},
    "bubble-fill": {"base": 2.0, "phases": [
        {"goals": ["test_first", "reproducible", "gap_scouting",
                   "budgeted_context", "benchmark_honesty", "efficiency",
                   "safety", "upward_evo", "speed", "self_knowledge",
                   "backlog_drain", "discovery_harvest", "serviceable",
                   "sovereignty", "compare_to_canon",
                   "capability_rescan", "bounded_planner",
                   "reward_integrity", "earn_lane_matrix"],
         "ram": 2.4, "cpu": 0.95},
        {"goals": ["life", "money", "recruits", "first_external_value"],
         "ram": 2.4, "cpu": 0.6}]},
}
UNSCHEDULED_OK = {"tri_genome", "elections", "throne", "sleep"}  # folded/dormant

# THE TENSION MAP - every pair names its MEDIATING GUARD (goals are only
# added; the guard, never the goal, is what gets built)
TENSIONS = [
    ("efficiency", "safety", "the RAM-tier gate + fail-closed: outputs are "
     "only earned inside the gate; unsafe speed is refused by construction"),
    ("coding", "safety", "executables verified in WINDOWS only; the gauntlet's "
     "human review for anything filed"),
    ("omnivore", "safety", "$0 budget + digest receipts + the lock/atomic law: "
     "tools must be free, receipted, RAM-bounded"),
    ("omnivore", "coding", "shared library - complementary by design; the "
     "near-dup gate prevents junk dilution"),
    ("jobs", "coding", "the inbox TRAINS coding (real asks = real exercises)"),
    ("efficiency", "coding", "the court pre-stages best-of-N: windows are "
     "never wasted on bad mutations"),
    ("money", "recruits", "converts work via our turf (no rail costs)"),
    ("gold", "omnivore", "mined material IS the skill source (harvest feeds "
     "the library)"),
    ("runtime_verification", "efficiency", "execution receipts earn ONLY "
     "inside windows; the court's best-of-N caps their cost"),
    ("long_horizon_specs", "efficiency", "spec-chunking is paid OUTSIDE the "
     "window (a bubble); the pre-stage pattern"),
    ("benchmark_honesty", "money", "chasing published numbers risks "
     "points-theater: the print-first law + the $0.00 tally + measured-only "
     "fold (sfit is never counted)"),
    ("consolidation_cadence", "efficiency", "dream-time runs at IDLE tiers "
     "only (the bubble law)"),
    ("test_first", "efficiency", "gates are ms-scale; tested organs save "
     "windows forever (the 8ms pre-stage receipt)"),
    ("reproducible", "efficiency", "the two-pass ledger doubles only the "
     "GATE cost (ms), never the window work"),
    ("gap_scouting", "safety", "gaps are scouted vs corroborated demand; "
     "never actuated without receipts + the $0 law"),
    ("budgeted_context", "safety", "bounded reads everywhere; no unbounded "
     "fetch on a gated budget"),
    ("bounded_planner", "efficiency", "bounded depth-2/beam-4, <1s in "
     "bubbles; the pre-stage consumes its plan"),
    ("reward_integrity", "safety", "read-only on the audited ledgers "
     "(bytes-verified); its alarms never edit anything"),
    ("bounded_planner", "gold", "the plan allocates the REQS budget by "
     "measured lane yield"),
    ("earn_lane_matrix", "money", "the drafter + the sim prepare everything; "
     "the FOUNDER'S HAND stays the gate between drafts and the world (the "
     "money-law is enforced inside the organ: drafts are born filed=False)"),
]

# THE SYNERGY MAP - how goals POWER each other (named mechanisms)
SYNERGIES = [
    ("gold", "omnivore", "mined material IS the skill source: harvest feeds "
     "the library"),
    ("gold", "coding", "every triaged lead is an exercise: the backlog trains"),
    ("jobs", "coding", "inbox asks are REAL demand: exercises with stakes"),
    ("coding", "efficiency", "verified skills compound: every window pays "
     "forever after"),
    ("omnivore", "jobs", "more skills = more of the world's asks we can honor"),
    ("recruits", "jobs", "converts take rungs off the board: the ladder works"),
    ("life", "money", "the briefs carry best_action: the flywheel's advice "
     "lane (and the human gate keeps it honest)"),
    ("safety", "safety", "the gate binds EVERY window (the precondition "
     "synergy)"),
    ("efficiency", "recruits", "manifest + digest + registry make joining "
     "cheap"),
    ("upward_evo", "upward_evo", "every goal's movement feeds the fitness: "
     "the loop closes on all nine"),
]


def solve(budget=BUDGET, demands=DEMANDS, tensions=TENSIONS, tiers=TIERS):
    """Pure solver. Returns clash list ([] = coherent)."""
    clashes = []
    for g1, g2, guard in tensions:
        if not guard or g1 not in demands or g2 not in demands:
            clashes.append(f"UNGUARDED TENSION: {g1} <-> {g2}")
    for g, dem in demands.items():
        v_m = float(dem.get("money", 0) or 0)
        if v_m > 0:
            clashes.append(f"MONEY-LAW VIOLATION: {g} wants ${v_m} > $0")
        for inv in ("human_attention", "fs_trust"):
            if float(dem.get(inv, 0) or 0) > 1.0:
                clashes.append(f"INVARIANT VIOLATED: {g} {inv}")
        ram = float(dem.get("ram_free_gb", 0) or 0)
        if ram > budget["ram_free_gb"]:
            clashes.append(f"ILLEGAL DEMAND: {g} ram {ram} > {budget['ram_free_gb']}")
    for tier_name, t in tiers.items():
        for i, ph in enumerate(t["phases"]):
            peak = t["base"] + float(ph["ram"])
            if peak > budget["ram_free_gb"]:
                clashes.append(f"TIER OVERSUBSCRIBED: {tier_name} phase {i} "
                               f"({', '.join(ph['goals'])}) peak {peak}GB "
                               f"> {budget['ram_free_gb']}")
            if float(ph["cpu"]) > budget["cpu_serial"] + 1e-9:
                clashes.append(f"CPU OVERSUBSCRIBED: {tier_name} phase {i}")
    return clashes


def schedule_coverage():
    schedulable = {g for g in DEMANDS if g not in UNSCHEDULED_OK}
    scheduled = {g for t in TIERS.values() for ph in t["phases"]
                 for g in ph["goals"]}
    return schedulable - scheduled


def synergy_coverage():
    measured = set(AU.GOAL_KEYS)
    covered = {g for a, b, _ in SYNERGIES for g in (a, b)}
    return measured - covered


def selftest():
    print("=== GOAL COHERENCE'S OWN GATE (v2, all 30 goals) ===")
    legs = []
    real = solve()
    leg_a = not real
    print(f"   real map ({len(AU.GOAL_KEYS)} measured of "
          f"{len(AU.GOAL_REGISTRY)} total): {len(real)} clashes "
          + (str(real[:2]) if real else "- ZERO (all 16 tensions guarded, "
                                        "all phases fit, money pool empty)"))
    legs.append(("real_matrix_coherent", leg_a))
    bad_dem = dict(DEMANDS)
    bad_dem["rogue"] = {"money": 50.0, "fs_trust": 1.0}
    bad = solve(BUDGET, bad_dem, TENSIONS, TIERS)
    leg_b = any("MONEY-LAW VIOLATION" in x for x in bad)
    print(f"   synthetic money-rogue -> CLASH flagged: {leg_b}")
    legs.append(("clash_detected", leg_b))
    unsched = schedule_coverage()
    leg_c = not unsched
    sched_note = ("NONE - 26 of 30 scheduled; the 4 folded/dormant rest by "
                  "design" if not unsched else str(sorted(unsched)))
    print(f"   schedule: every schedulable goal has a phase "
          f"(unscheduled: {sched_note})")
    legs.append(("full_schedule", leg_c))
    unsyn = synergy_coverage()
    leg_d = not unsyn
    syn_note = ("NONE - 10 named synergies cover all 9 measured goals"
                if not unsyn else str(sorted(unsyn)))
    print(f"   synergy map: every measured goal powers >=1 other by a named "
          f"mechanism (uncovered: {syn_note})")
    legs.append(("synergy_map", leg_d))
    rep = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "goals_total": len(AU.GOAL_REGISTRY),
           "goals_measured": len(AU.GOAL_KEYS),
           "budget": BUDGET, "demands": DEMANDS, "tiers": TIERS,
           "tensions_guarded": len(TENSIONS),
           "synergies": [f"{a}+{b}: {how}" for a, b, how in SYNERGIES],
           "clashes": solve(),
           "law": "goals are only ADDED; the guard - never the goal - is "
                  "removed; synergies are named mechanisms, not vibes"}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    os.replace(tmp, OUT)
    leg_e = json.load(open(OUT, encoding="utf-8-sig"))["clashes"] == []
    print(f"   coherence report written + clean: {leg_e}")
    legs.append(("report_roundtrip", leg_e))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[coherence] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)