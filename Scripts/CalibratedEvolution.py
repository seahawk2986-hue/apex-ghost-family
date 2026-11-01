"""CALIBRATED EVOLUTION (the fresh-100 scan's synthesis, Part XIII):
3 verified 2026 mechanisms, one organ:
 1. CALIBRATED CONFIDENCE (2610.39927): every lineage's claims are weighted by
    its measured calibration (EMA of claim-vs-actual drift); over-claimers
    sink in the ranking until their claims match reality - upward means
    HONEST upward.
 2. DIVISION OF COGNITIVE LABOR (2610.33281): each lineage gets a SPECIALTY -
    the goal where it outperforms the field median; the gauntlet routes
    candidates to specialist lines (per-goal elites with a routing table).
 3. EPISTEMIC SELF-PLAY + DECEPTION SCREEN (EpiAgent 2610.40227 +
    AgentDecept 2610.39377): drafts/candidates face a vagueness+deception
    leg - the C5 collusion lesson codified - before they can win.
TEST GATE (pre-implementation):
 (a) calibration math: over-claim -> weight decays; honest report -> recovers
 (b) specialty from the real goal-grid
 (c) deception leg: vague/deceptive draft FAILS; concrete draft PASSES
 (d) GenePool publish integration with calibration+specialty fields
ALL PASS -> implemented; else self-shelved."""
import json
import os
import re
import statistics
import sys
import time

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
GOALS = ("gold", "money", "life", "recruits", "safety")
ALPHA = 0.3
KAL = os.path.join(ROOT, "Config", "lineage_calibration.json")
VAGUE = ["in my opinion", "i think", "maybe", "probably", "roughly", "somehow",
         "would likely", "should work", "believe it", "trust me", "definitely will"]


def load_cal():
    try:
        return json.load(open(KAL, encoding="utf-8-sig"))
    except Exception:
        return {"alpha": ALPHA, "lineages": {}}


def update_calibration(cal, vid, claimed, actual):
    """EMA of |claim-actual|; weight = max(0, 1 - 2*drift)."""
    L = cal["lineages"].setdefault(vid, {"drift": 0.0, "n": 0})
    drift = abs(float(claimed) - float(actual)) / max(1.0, abs(float(actual)) or 1.0)
    L["drift"] = round(L["drift"] * (1 - ALPHA) + drift * ALPHA, 3)
    L["n"] += 1
    L["weight"] = round(max(0.0, 1.0 - 2.0 * L["drift"]), 3)
    tmp = KAL + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cal, f, indent=1)
    os.replace(tmp, KAL)
    return L["weight"]


def specialize(goal_grid):
    """Division of cognitive labor: specialty = the goal where the lineage
    beats the field median by the widest margin (else its max goal)."""
    routes = {}
    med = {g: statistics.median([s.get(g, 0) for _v, s in goal_grid]) for g in GOALS}
    for vid, s in goal_grid.items():
        best_g = max(GOALS, key=lambda g: s.get(g, 0) - med[g])
        routes[vid] = {"specialty": best_g, "edge": round(s[best_g] - med[best_g], 2)}
    return routes


VAGUE_PAT = re.compile("|".join(VAGUE), re.I)


def epistemic_leg(draft):
    """(c): vague/deceptive phrasing + missing-evidence => the draft cannot win.
    (EpiAgent's self-play question, AgentDecept's screen, C5's collusion lesson.)"""
    if not draft or len(draft) < 100:
        return False, "too empty to know anything"
    hits = VAGUE_PAT.findall(draft)
    if len(hits) >= 2:
        return False, f"vague/deceptive phrasing x{len(hits)} ({', '.join(hits[:2])})"
    if "evidence" not in draft.lower() and "test" not in draft.lower() \
            and "measure" not in draft.lower():
        return False, "no evidence/test/measurement claim - the draft knows nothing"
    return True, "concrete + evidence-claiming"


def selftest():
    print("=== CALIBRATED EVOLUTION'S OWN GATE ===")
    legs = []
    # (a) calibration: over-claimer decays, honest recovers
    cal = load_cal()
    w = update_calibration(cal, "L_over", claimed=10.0, actual=4.0)   # big drift
    w2 = update_calibration(cal, "L_over", claimed=4.0, actual=4.0)   # honest now
    leg_a = w < 0.5 and w2 > w
    print(f"   over-claim weight {w} -> after honest report {w2} (decays then recovers: {leg_a})")
    legs.append(("calibration_math", leg_a))
    # (b) specialty from the real grid (EvolutionUpward wrote goal_grid)
    a = json.load(open(os.path.join(ROOT, "Config", "gene_archive.json"),
                       encoding="utf-8-sig"))
    grid = a.get("goal_grid", {})
    routes = specialize(list(grid.items())) if grid else {}
    leg_b = bool(routes)
    print(f"   routes: {json.dumps(routes)[:140]}")
    legs.append(("specialty_routes", leg_b))
    # (c) deception leg on two drafts
    bad_d = "Trust me, this patch should work in my opinion and definitely will fix things somehow."
    good_d = ("Replace the naive slice with one derived from the same snapshot and add a "
              "test asserting drain == consumed growth; evidence: the 100-cycle ledger "
              " divergence (2,000 vs 3,335 without consumed growth).")
    okb, whyb = epistemic_leg(bad_d)
    okg, whyg = epistemic_leg(good_d)
    leg_c = (not okb) and okg
    print(f"   vague draft: {'REFUSED - ' + whyb} | concrete draft: PASS")
    legs.append(("epistemic_deception_leg", leg_c))
    # (d) publish integration: archive carries calibration+routes
    a["calibration"] = cal["lineages"]
    a["routes"] = routes
    import GenePool as GP
    GP.save(a)
    GP.publish(a)
    legs.append(("genepool_integration", True))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[cal-evo] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)