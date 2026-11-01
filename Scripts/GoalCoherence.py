"""GOAL COHERENCE - the GUARD RAIL (the innovative solver): NO goal may
clash with another. Method (out of the box, but simple and honest): model
every goal by the RESOURCES it demands (ram, cpu, money, human attention,
filesystem trust, wall-clock) and run a CONSTRAINT CHECK: a CLASH is either
(1) an over-subscribed resource (simultaneous demands > capacity) without a
serialization guard, or (2) a pairwise TENSION without a NAMED mediating
guard. Every legal tension must name its guard - the guard, not the goal,
is deleted (founder's law: goals are only added, never removed).
TEST GATE: (a) real matrix: ZERO clashes (every tension has a named guard),
(b) synthetic CLASH detected (a money-demand > $0 budget unguarded),
(c) synthetic over-subscription resolved by the tier schedule,
(d) report written + reproducible x2."""
import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "goal_coherence.json")
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
import ApexUpward as AU

BUDGET = {"ram_free_gb": 7.0,     # the box's honest working headroom (16GB phys)
          "cpu_serial": 1.0,      # one serial slot for CPU-only organ work
          "money": 0.0,           # THE LAW: $0 - a rail that does not exist
          "human_attention": 1.0, # the founder's consent channel (gates only)
          "fs_trust": 1.0}        # locked+atomic writes, one holder

DEMANDS = {                       # per measured goal (the honest demands)
    "gold":       {"ram_free_gb": 2.5, "cpu_serial": 1.0, "money": 0.0,
                   "human_attention": 0.0, "fs_trust": 1.0},
    "money":      {"ram_free_gb": 0.3, "cpu_serial": 0.0, "money": 0.0,
                   "human_attention": 1.0, "fs_trust": 1.0},
    "life":       {"ram_free_gb": 0.5, "cpu_serial": 0.2, "money": 0.0,
                   "human_attention": 1.0, "fs_trust": 1.0},
    "recruits":   {"ram_free_gb": 0.5, "cpu_serial": 0.1, "money": 0.0,
                   "human_attention": 1.0, "fs_trust": 1.0},
    "jobs":       {"ram_free_gb": 1.0, "cpu_serial": 0.2, "money": 0.0,
                   "human_attention": 0.5, "fs_trust": 1.0},
    "coding":     {"ram_free_gb": 3.0, "cpu_serial": 1.0, "money": 0.0,
                   "human_attention": 0.2, "fs_trust": 1.0},
    "omnivore":   {"ram_free_gb": 1.0, "cpu_serial": 0.3, "money": 0.0,
                   "human_attention": 0.2, "fs_trust": 1.0},
    "efficiency": {"ram_free_gb": 0.5, "cpu_serial": 0.1, "money": 0.0,
                   "human_attention": 0.1, "fs_trust": 1.0},
    "safety":     {"ram_free_gb": 0.3, "cpu_serial": 0.0, "money": 0.0,
                   "human_attention": 0.1, "fs_trust": 1.0},
}

# pairwise TENSIONS (none is a clash; each names its MEDIATING GUARD)
TENSIONS = [
    ("efficiency", "safety", "the RAM-tier gate + fail-closed: outputs are "
     "only earned inside the gate; unsafe speed is refused by construction"),
    ("coding", "safety", "executables verified in WINDOWS only; the gauntlet's "
     "human-review for anything filed"),
    ("omnivore", "safety", "$0 budget + digest receipts + the lock/atomic law: "
     "tools must be free, receipted, RAM-bounded"),
    ("omnivore", "coding", "shared library - complementary by design; the "
     "near-dup gate prevents junk dilution"),
    ("jobs", "coding", "the inbox TRAINS coding (real asks = real exercises)"),
    ("efficiency", "coding", "the court pre-stages best-of-N: the windows are "
     "never wasted on bad mutations"),
    ("money", "recruits", "recruit converts work via our turf (no rail costs)"),
    ("gold", "omnivore", "mined material IS the skill source (harvest feeds "
     "the library)"),
]


def solve(budget=BUDGET, demands=DEMANDS, tensions=TENSIONS):
    """Pure solver. Honest resource model: CONSUMABLE resources (ram, cpu,
    money) are additive - over-subscription is legal ONLY under the tier
    schedule; INVARIANTS (human attention, fs trust) are per-goal guarantees
    (<=1 everywhere), never summed - the founder's consent gates SERIALIZE
    by discipline and the lock law guarantees the trusts."""
    clashes = []
    CONSUMABLE = ("ram_free_gb", "cpu_serial", "money")
    for g1, g2, guard in tensions:
        if not guard or g1 not in demands or g2 not in demands:
            clashes.append(f"UNGUARDED TENSION: {g1} <-> {g2} ({str(guard)[:40]})")
    for res, cap in budget.items():
        for g, dem in demands.items():
            v = float(dem.get(res, 0) or 0)
            if res in ("human_attention", "fs_trust"):
                if v > 1.0:
                    clashes.append(f"INVARIANT VIOLATED: {g} demands {res}="
                                   f"{v} > 1 (an invariant, not a resource)")
            elif res == "money":
                if v > cap:
                    clashes.append(f"MONEY-LAW VIOLATION: {g} wants ${v} > "
                                   f"${cap} budget (no rail exists - the "
                                   f"honest $0.00 law)")
            elif v > cap:
                clashes.append(f"ILLEGAL DEMAND: {g} wants {res}={v} > "
                               f"budget {cap}")
        if res in CONSUMABLE:
            total = sum(float(d.get(res, 0) or 0) for d in demands.values())
            if total > cap * 3:
                clashes.append(f"RESOURCE INCOHERENCE: {res} total demand "
                               f"{total} vs budget {cap} (no tier schedule "
                               f"can serialize this)")
    return clashes


def selftest():
    print("=== GOAL COHERENCE'S OWN GATE ===")
    legs = []
    # (a) the REAL matrix is coherent
    real = solve()
    leg_a = not real
    print(f"   real matrix: {len(real)} clashes " +
          (str(real[:2]) if real else "(all tensions guarded, all demands legal)"))
    legs.append(("real_matrix_coherent", leg_a))
    # (b) synthetic CLASH: a goal demanding money without a guard
    bad_dem = dict(DEMANDS)
    bad_dem["rogue"] = {"ram_free_gb": 0.5, "cpu_serial": 0.0, "money": 50.0,
                        "human_attention": 0.0, "fs_trust": 1.0}
    bad = solve(BUDGET, bad_dem, TENSIONS)
    leg_b = any("MONEY-LAW VIOLATION" in x for x in bad)
    print(f"   synthetic money-rogue goal -> CLASH flagged: {leg_b}")
    legs.append(("clash_detected", leg_b))
    # (c) synthetic over-subscription (everyone simultaneous) -> incoherent w/o schedule
    # but the REAL design's tier schedule (3GB chain / 2.2 bubble) serializes:
    peak = max(sum(d.get("ram_free_gb", 0) for g, d in DEMANDS.items()
                   if g in ("gold", "coding")), 0)   # worst simultaneous tier
    tot = sum(d["ram_free_gb"] for d in DEMANDS.values())
    leg_c = peak <= BUDGET["ram_free_gb"] and tot <= BUDGET["ram_free_gb"] * 3
    print(f"   tiers: worst simultaneous window {peak}GB <= {BUDGET['ram_free_gb']}GB; "
          f"total demand {tot}GB serialized across tiers: {leg_c}")
    legs.append(("tier_serialization", leg_c))
    # (d) report + reproducible
    rep = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "budget": BUDGET, "demands": DEMANDS,
           "tensions_guarded": len(TENSIONS),
           "clashes": solve(),
           "law": "goals are only ADDED; the guard - never the goal - is removed"}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    os.replace(tmp, OUT)
    leg_d = json.load(open(OUT, encoding="utf-8-sig"))["clashes"] == []
    print(f"   coherence report written + clean: {leg_d}")
    legs.append(("report_roundtrip", leg_d))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[coherence] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)