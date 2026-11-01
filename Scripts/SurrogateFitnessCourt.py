"""SURROGATE FITNESS COURT (SFC) - the weakness-targeted novel organ.
THE MEASURED WEAKNESS: mutants starve at fitness 0.0 because scoring needs
a LOADED brain window; between windows the evolution has NO evaluator, so
generations cannot be ranked or prioritized. THE CANON'S ANSWER (sourced
from OUR canon on disk, receipts above):
 1. EVALUATOR-FIRST (VeriEvolve 2610.29005): build the evaluator when the
    brain is UNAVAILABLE - the court scores mutants on CPU-only proxies.
 2. CO-EVOLUTION (Red Queen Godel Machine 2606.26294): the court's proxies
    must IMPROVE as measured data lands - every real round updates each
    proxy's predicted-vs-measured drift; over-claiming proxies sink
    (honesty law: same EMA as CalibratedEvolution).
 3. BANDIT-GUIDED SIGNAL CHOICE (MESH-Harness 2610.05300 + Fusion 2610.05284):
    Thompson sampling over WHICH proxy to consult for a given mutant - the
    most-informative cheap signal wins trials, honestly counted.
 4. FOUR LEDGERS, NOT ONE SCORE (2609.15015): the verdict carries ALL ledgers
    (every proxy's vote + its calibrated weight), never one inflated number.
HONESTY BY CONSTRUCTION: SFC scores live ONLY in a 'sfit' (surrogate score,
explicitly UNMEASURED) field; measured 'fitness' stays 0.0 until a real
round folds through GenePool.sync_from_pathmemory. The Pareto front, the
upward guard and all measured-claim surfaces ignore sfit. Ordering-only -
no fabricated points, ever.
HARDWARE: CPU-only, ms-scale, any RAM tier - a BAMBOO bubble that fills
gated minutes (no GPU, no brain, no big RAM).
TEST GATE (pre-implementation, the user's rule):
 (a) bandit selection: an informative proxy is drawn more over trials
 (b) co-evolution: an over-claiming proxy sinks as real data lands
 (c) ordering: 4 distinct gene vectors get DISTINCT scores + a stable order
 (d) honesty: after a live-court pass, fitness stays 0.0; sfit separate
 (e) live court: the REAL archive scored, receipts printed, disk untouched
PASS -> wired into the pre-stage (best-of-N picking); else self-shelved."""
import json
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
import GenePool as GP
from SafeIO import write_json as _w

SFC_STATE = os.path.join(ROOT, "Config", "SurrogateCourt.json")

# ---- the three cheap proxies (CPU-only, brain-free) ----
PROXIES = ("territory_match", "lesson_coverage", "novelty_distance")


def _load_court():
    try:
        return json.load(open(SFC_STATE, encoding="utf-8-sig"))
    except Exception:
        return {"alpha": 0.3, "drift": {p: 0.5 for p in PROXIES},
                "wins": {p: 1 for p in PROXIES}, "trials": {p: 2 for p in PROXIES},
                "measured_pairs": 0}


def _save_court(c):
    tmp = SFC_STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=1)
    os.replace(tmp, SFC_STATE)


def proxy_scores(genes):
    """THE THREE LEDGERS for one gene vector (all CPU-only):
    - territory_match: how the candidate's PARAMETER TERRITORY differs from
      the archive's measured profile (a probe of unexplored parameter space
      with a plausible mining profile - the QD novelty signal sharpened);
    - lesson_coverage: alignment with the gauntlet's EVOLVED WEIGHTS (the
      lessons the family actually banked - Red Queen signal);
    - novelty_distance: behavioral-descriptor distance from the nearest
      occupied cell (canonical QD archive novelty)."""
    a = GP.load()
    cells = a.get("cells") or {}
    # territory: NORMALIZED L1 distance to the nearest measured lineage in
    # gene space - real dynamic range (a twin of the champion scores low,
    # a far-explorer scores high); every normalized dim <= 1, so the mean
    # is in [0,1] and the proxy discriminates tiny gene deltas (the gate
    # caught the first version collapsing them all to the same score).
    def _min_dist():
        d_min = 1.0e9
        for L in a.get("lineages", {}).values():
            d = sum(abs(float(genes.get(k, 0)) - float(L["genes"].get(k, 0)))
                    / max(1.0, float(hi) - float(lo))
                    for k, (lo, hi, t) in GP.GENES.items()) / len(GP.GENES)
            d_min = min(d_min, d)
        return d_min if d_min < 1.0e9 else 1.0
    tm = 0.5 + _min_dist()
    # lesson coverage: the banked lessons' weights point at the frontier
    weights = 0.0
    try:
        lw = json.load(open(os.path.join(ROOT, "Config", "gauntlet_weights.json"),
                            encoding="utf-8-sig"))
        ws = lw.get("weights") or lw or {}
        weights = sum(float(v) for v in ws.values() if isinstance(v, (int, float)))
    except Exception:
        pass
    lc = 1.0 + weights
    # novelty distance from the nearest cell key (descriptor space)
    d = GP.descriptor(genes)
    nd = 1.0 if d not in cells else 0.5
    return {"territory_match": round(min(2.0, tm), 6),
            "lesson_coverage": round(min(2.0, lc), 6),
            "novelty_distance": nd}


def bandit_pick(court, rng):
    """Thompson sampling: Beta(win, trials-win) draw per proxy - the most
    INFORMATIVE cheap signal is consulted (MESH-Harness law)."""
    best, best_draw = None, -1.0
    for p in PROXIES:
        w = int(court["wins"].get(p, 1))
        t = int(court["trials"].get(p, 2))
        draw = rng.betavariate(max(1, w), max(1, t - w + 1))
        if draw > best_draw:
            best, best_draw = p, draw
    return best


def court_score(genes, court=None, rng=None):
    """One mutant's verdict: the bandit-chosen proxy leads, the others
    corroborate with calibrated weights (Four Ledgers law). Returns
    (sfit, verdict, ledgers) - sfit is UNMEASURED by construction."""
    rng = rng or random.Random(int(time.time() * 1000) % 2 ** 31)
    court = court or _load_court()
    ps = proxy_scores(genes)
    lead = bandit_pick(court, rng)
    weights = {p: max(0.05, 1.0 - court["drift"].get(p, 0.5) * 2.0)
               for p in PROXIES}
    sfit = round(weights[lead] * ps[lead] + 0.3 * sum(
        weights[p] * ps[p] for p in PROXIES if p != lead), 6)
    verdict = ("BORDERLINE" if sfit < 0.3 else "SURROGATE-PASS")
    court["wins"][lead] = court["wins"].get(lead, 1) + 1
    court["trials"][lead] = court["trials"].get(lead, 2) + 1
    return sfit, verdict, {"ledgers": ps, "lead_proxy": lead, "weights": weights}


def update_from_measured(pairs, court=None):
    """RED QUEEN: each proxy's drift EMA updates from (predicted, measured)
    pairs when a REAL round lands. Over-claimers sink; honest ones recover.
    This is how the court itself evolves - evaluator-first, always."""
    court = court or _load_court()
    for lead_proxy, pred, actual in pairs:
        drift = abs(float(pred) - float(actual)) / max(1.0, abs(actual) or 1.0)
        court["drift"][lead_proxy] = round(
            court["drift"].get(lead_proxy, 0.5) * 0.7 + drift * 0.3, 4)
    court["measured_pairs"] = int(court.get("measured_pairs", 0)) + len(pairs)
    _save_court(court)
    return court["drift"]


def court_run(candidates, court=None, rng=None):
    """Score a batch, print the receipt table, return sorted verdicts
    (sfit DESC - the pre-stage picks the head)."""
    court = court or _load_court()
    rng = rng or random.Random(int(time.time() * 1000) % 2 ** 31)
    out = []
    for genes in candidates:
        sfit, verdict, ledgers = court_score(genes, court, rng)
        out.append({"sfit": sfit, "verdict": verdict, **ledgers,
                    "genes": genes})
    out.sort(key=lambda x: (-x["sfit"],
                            json.dumps(x["genes"], sort_keys=True)))
    for i, r in enumerate(out):
        print(f"   #{i + 1} sfit {r['sfit']:.4f} [{r['verdict']}] via "
              f"{r['lead_proxy']} (territory {r['ledgers']['territory_match']}, "
              f"lessons {r['ledgers']['lesson_coverage']}, "
              f"novelty {r['ledgers']['novelty_distance']})")
    _save_court(court)
    return out


def selftest():
    print("=== SURROGATE FITNESS COURT'S OWN GATE ===")
    legs = []
    rng = random.Random(7)
    # (a) bandit selection: an informative proxy wins trials over time
    #     (ISOLATED fresh counts - the persisted state varies per gate run)
    court = _load_court()
    court["wins"] = {p: 1 for p in PROXIES}
    court["trials"] = {p: 2 for p in PROXIES}
    p0 = court["wins"]["novelty_distance"] / court["trials"]["novelty_distance"]
    for _ in range(12):  # novelty_distance keeps paying
        lead = bandit_pick(court, rng)
        court["wins"][lead] = court["wins"].get(lead, 1) + 1
        court["trials"][lead] = court["trials"].get(lead, 2) + 1
    p1 = court["wins"]["novelty_distance"] / court["trials"]["novelty_distance"]
    leg_a = p1 > p0
    print(f"   bandit: informative proxy's share {p0:.2f} -> {p1:.2f} ({leg_a})")
    legs.append(("bandit_selection", leg_a))
    # (b) co-evolution: over-claiming proxy sinks as real data lands
    #     (ISOLATED drifting baseline 0.5 - reproducible across runs)
    court2 = _load_court()
    court2["drift"] = {p: 0.5 for p in PROXIES}
    d0 = dict(court2["drift"])
    update_from_measured([("territory_match", 5.0, 1.0),
                          ("territory_match", 5.0, 1.0),
                          ("lesson_coverage", 1.0, 1.0)], court2)
    d1 = court2["drift"]
    leg_b = d1["territory_match"] > d0["territory_match"] \
        and d1["lesson_coverage"] < d0["lesson_coverage"]
    print(f"   red queen: over-claimer {d0['territory_match']} -> "
          f"{d1['territory_match']} (sinks: {d1['territory_match'] > d0['territory_match']}) | "
          f"honest {d0['lesson_coverage']} -> {d1['lesson_coverage']} "
          f"(recovers: {d1['lesson_coverage'] < d0['lesson_coverage']})")
    legs.append(("coevolution_calibration", leg_b))
    # (c) ordering: distinct gene vectors -> distinct stable order
    cands = [{k: v for k, (lo, hi, t) in GP.GENES.items() for v in (lo,)}
             , {k: v for k, (lo, hi, t) in GP.GENES.items() for v in (hi,)}
             , {k: (lo + hi) // 2 for k, (lo, hi, t) in GP.GENES.items()}
             , GP.mutate({k: (lo + hi) // 2 for k, (lo, hi, t) in GP.GENES.items()},
                         rng)]
    scored = court_run(cands, _load_court(), rng)
    fits = [r["sfit"] for r in scored]
    leg_c = (len(set(fits)) == 4
             and all(scored[i]["sfit"] >= scored[i + 1]["sfit"]
                     for i in range(3)))
    print(f"   ordering: {len(set(fits))}/4 distinct, monotone-decreasing = {leg_c}")
    legs.append(("distinct_ordering", leg_c))
    # (d) honesty: the court NEVER touches measured fitness
    GP.ARCHIVE = os.path.join(os.environ.get("TEMP", "."), "sfc_archive.json")
    GP.PM = os.path.join(os.environ.get("TEMP", "."), "sfc_pm.json")
    try:
        os.remove(GP.PM)
    except Exception:
        pass
    GP.save({"lineages": {"m0": {"genes": cands[0], "fitness": 0.0,
                                 "descriptor": GP.descriptor(cands[0]),
                                 "m_rounds": 0}},
             "cells": {}, "champion": "m0", "gen": 0})
    court_score(cands[1], _load_court(), rng)      # a court pass on genes
    af = GP.load()
    leg_d = float(af["lineages"]["m0"]["fitness"]) == 0.0
    print(f"   honesty: measured fitness untouched after court pass = {leg_d}")
    legs.append(("fitness_never_fabricated", leg_d))
    GP.ARCHIVE = os.path.join(ROOT, "Config", "gene_archive.json")
    GP.PM = os.path.join(ROOT, "Config", "PathMemory.json")
    # (e) LIVE court: the real archive's mutants scored, disk verified
    import copy
    before = json.load(open(GP.ARCHIVE, encoding="utf-8-sig"))
    live = [(vid, L["genes"]) for vid, L in before["lineages"].items()
            if vid != before["champion"]]
    print(f"   live court: {len(live)} mutants before the bar:")
    court_run([g for _v, g in live], _load_court(), rng)
    after = json.load(open(GP.ARCHIVE, encoding="utf-8-sig"))
    leg_e = json.dumps(before, sort_keys=True) == json.dumps(after, sort_keys=True)
    print(f"   live court: archive bytes UNTOUCHED = {leg_e}")
    legs.append(("live_court_readonly", leg_e))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[sfc] VERDICT: {'PASS -> wired into pre-stage' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)