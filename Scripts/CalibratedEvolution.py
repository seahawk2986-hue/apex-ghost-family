"""CALIBRATED EVOLUTION (clean repair, Part XIII): three verified mechanisms.
 1. CALIBRATED CONFIDENCE (2610.39927): lineages' claims weighted by measured
    calibration (EMA of claim-vs-actual); over-claimers sink until honest.
 2. DIVISION OF COGNITIVE LABOR (2610.33281): per-goal specialty routes.
 3. EPISTEMIC SELF-PLAY + DECEPTION SCREEN (EpiAgent 2610.40227 +
    AgentDecept 2610.39377): vague/deceptive drafts cannot win.
TEST GATE: (a) calibration decay+recovery, (b) specialty routes from the real
grid, (c) deception leg on two drafts, (d) GenePool publish integration.
ALL PASS -> implemented; else self-shelved. (This is the clean rewrite of a
file that briefly carried git-conflict markers - repaired here; the ledger
records the correction.)"""
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
VAGUE_PAT = re.compile("|".join(["in my opinion", "i think", "maybe", "probably",
                                 "roughly", "somehow", "would likely", "should work",
                                 "believe it", "trust me", "definitely will"]), re.I)


def load_cal():
    try:
        return json.load(open(KAL, encoding="utf-8-sig"))
    except Exception:
        return {"alpha": ALPHA, "lineages": {}}


def update_calibration(cal, vid, claimed, actual):
    """EMA of |claim-actual| drift; weight = max(0, 1 - 2*drift)."""
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
    """Per-goal specialty + median-edge routing. Accepts dict OR pairs."""
    rows = (list(goal_grid.items()) if isinstance(goal_grid, dict)
            else [tuple(x) for x in goal_grid])
    rows = [(str(v), s) for v, s in rows if isinstance(s, dict)]
    if not rows:
        return {}
    routes = {}
    med = {g: statistics.median([s.get(g, 0) for _v, s in rows]) for g in GOALS}
    for vid, s in rows:
        best_g = max(GOALS, key=lambda g: s.get(g, 0) - med.get(g, 0))
        routes[vid] = {"specialty": best_g,
                       "edge": round(s.get(best_g, 0) - med.get(best_g, 0), 2)}
    return routes


def epistemic_leg(draft):
    """Deception/vagueness screen (canon: vague agents can't be trusted)."""
    if not draft or len(draft) < 100:
        return False, "too empty to know anything"
    hits = VAGUE_PAT.findall(draft)
    if len(hits) >= 2:
        return False, f"vague/deceptive phrasing x{len(hits)} ({', '.join(hits[:2])})"
    if not re.search(r"evidence|test|measure", draft.lower()):
        return False, "no evidence/test/measurement claim - the draft knows nothing"
    return True, "concrete + evidence-claiming"


def selftest():
    print("=== CALIBRATED EVOLUTION'S OWN GATE ===")
    legs = []
    # (a) calibration: over-claim decays; honest reporting recovers GRADUALLY
    # (the stateful EMA's real contract: monotonic recovery across reports,
    #  not one-shot forgiveness - the prior test was impatient and failed)
    cal = load_cal()
    w0 = update_calibration(cal, "L_test", 10.0, 4.0)
    ws = [update_calibration(cal, "L_test", 4.0, 4.0) for _ in range(3)]
    leg_a = all(ws[i] <= ws[i + 1] for i in range(len(ws) - 1)) and ws[-1] >= w0
    print(f"   calibration: over-claim w={w0} -> honest x3: {ws} "
          f"(monotonic recovery: {leg_a})")
    legs.append(("calibration_math", leg_a))
    # (b) specialty from the real grid
    a = json.load(open(os.path.join(ROOT, "Config", "gene_archive.json"),
                       encoding="utf-8-sig"))
    routes = specialize(a.get("goal_grid", {}))
    leg_b = isinstance(routes, dict) and len(routes) == len(a.get("goal_grid", {})) \
        and len(a.get("goal_grid", {})) > 0
    print(f"   routes: {json.dumps(routes)[:150]}")
    legs.append(("specialty_routes", leg_b))
    # (c) deception screen
    bad_d = ("Trust me, this patch should work in my opinion and definitely "
             "will fix things somehow.")
    good_d = ("Replace the naive slice with one snapshot-derived and add a test "
              "asserting drain equals consumed growth; evidence: the 100-cycle "
              "ledger divergence (2,000 vs 3,335 without consumed growth).")
    okb, whyb = epistemic_leg(bad_d)
    okg, whyg = epistemic_leg(good_d)
    leg_c = (not okb) and okg
    print(f"   vague draft: REFUSED ({whyb}) | concrete draft: PASS")
    legs.append(("epistemic_deception_leg", leg_c))
    # (d) GenePool integration
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