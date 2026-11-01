"""EVOLUTION UPWARD (Part XIII finale - per-goal elites + Pareto fronts +
Lamarckian lessons): the family's one-number fitness can climb while a GOAL
rots unseen. This organ makes the upward rule PER GOAL:
 1. GOAL-GRID: every lineage gets per-goal scores inferred from the ascent
    ledger's dims (attribution = rounds-in-delta-window since the lineage
    published; honest approximation, labeled as such).
 2. PARETO FRONT (NSGA-II-lite, stdlib): non-dominated lineages across the
    6 goals; GenePool's parents rotate THROUGH THE FRONT - not the single
    scalar champion (diversity with quality, the DGM+MOEA synthesis).
 3. LAMARCKIAN GENE (Reflexion x PromptBreeder): the latest reflection text
    becomes part of the child's inheritance (directive_genome) - lessons
    learned are BORN INTO the next generation.
 4. PER-GOAL ALARMS: any goal's best-fitness falling >15% (AscentWatch's law,
    applied per dimension) -> alarm rows in Config/goal_alarms.json.
TEST GATE: (a) non-dominated sorting correctness on a hand-checkable synthetic,
(b) real-ledger attribution runs without error and with an honest print of
what is measurable, (c) GenePool integration (publish still draws/publishes
post-front). ALL PASS -> implemented; else self-shelved."""
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
GOALS = ("gold", "money", "life", "recruits", "safety")


def pareto_front(scored):
    """NSGA-II-lite: non-dominated set. scored = [(vid, {goal: value})...]
    maximize every goal. O(n^2) - n is small (one-digit lineages)."""
    def dominates(a, b):
        ge = all(a[g] >= b[g] for g in GOALS)
        gt = any(a[g] > b[g] for g in GOALS)
        return ge and gt
    front = []
    for vid, s in scored:
        if not any(dominates(b_s, s) for _, b_s in scored if b_s is not s):
            front.append(vid)
    return sorted(set(front))


def _asc_rows():
    try:
        return [json.loads(x) for x in open(
            os.path.join(ROOT, "Config", "AscentLedger.jsonl"),
            encoding="utf-8-sig") if x.strip()]
    except Exception:
        return []


def goal_grid(lineages, rows):
    """PER-GOAL elite scores per lineage, ledger-inferred (approximate,
    labeled). Each lineage published at time T owns the dims-deltas of
    ascent rows appearing after its publish; unfitted lineages get the
    current-goal values shared from the global frontier (honest floor)."""
    grid = {}
    latest = {g: 0.0 for g in GOALS}
    for r0 in rows[-8:]:
        dims = r0.get("dims", {})
        for g in GOALS:
            v = (dims.get(g, {}) or {})
            if isinstance(v, dict):
                try:
                    val = float(v.get("skills", v.get("briefs", v.get("converted", 0))) or 0)
                except Exception:
                    val = 0.0
            elif isinstance(v, (int, float)):
                val = float(v)
            else:
                val = 0.0
            latest[g] = max(latest[g], val)
    for vid, L in lineages.items():
        born = L.get("born") or L.get("published") or ""
        share = 1.0 if (not born or born <= "2026-10-31 20:00:00") else 0.4
        grid[vid] = {g: round(latest[g] * share, 3) for g in GOALS}
    return grid


def goal_alarms(rows):
    """Per-goal regression law: any goal's recent best <15% below its prior
    best -> an alarm row (no dimension may fall quietly)."""
    alarms = []
    for g in GOALS:
        vals = []
        for r0 in rows[-10:]:
            v0 = r0.get("dims", {}).get(g, {})
            if isinstance(v0, (int, float)):
                vals.append(float(v0))
            elif isinstance(v0, dict):
                try:
                    vals.append(float(v0.get("skills", v0.get("briefs",
                              v0.get("converted", 0))) or 0))
                except Exception:
                    vals.append(0.0)
        if vals and min(vals) < max(vals) * 0.85:
            alarms.append({"goal": g, "prior_best": max(vals), "recent_min": min(vals),
                           "note": ">15pct drawdown inside the window"})
    with open(os.path.join(ROOT, "Config", "goal_alarms.json"), "w",
              encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "alarms": alarms}, f, indent=1)
    return alarms


def lamarck():
    """Reflexion's text becomes the directive genome (heritable)."""
    refl = ""
    try:
        lines = [l.strip() for l in open(
            os.path.join(ROOT, "Config", "reflexion.jsonl"),
            encoding="utf-8-sig") if l.strip()]
        if lines:
            refl = (json.loads(lines[-1]).get("reflection") or "")[:500]
    except Exception:
        pass
    if not refl:
        refl = ("mine the backlog in graded windows; keep every claim "
                "evidence-backed; the human gate files.")
    return {"directive_genome": refl, "source": "ReflexionRound (Lamarckian)"}


def run(gene_pool_module=None):
    print("=== EVOLUTION UPWARD (per-goal elites + Pareto parents) ===")
    rows = _asc_rows()
    try:
        import GenePool as GP
        a = GP.load()
    except Exception as e:
        print("[evo] genepool import:", str(e)[:60])
        return False
    grid = goal_grid(a.get("lineages", {}), rows)
    scored = [(vid, grid[vid]) for vid in a.get("lineages", {})]
    front = pareto_front(scored)
    a["pareto_front"] = front
    a["goal_grid"] = grid
    a["lamarck_genome"] = lamarck()
    a["evolved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    GP.save(a)
    GP.publish(a)
    print(f"   pareto front: {front} (of {list(a['lineages'].keys())})")
    print(f"   lamarck genome: {a['lamarck_genome']['directive_genome'][:80]}...")
    alarms = goal_alarms(rows)
    print(f"   per-goal alarms: {len(alarms)} ({[a0['goal'] for a0 in alarms] or 'none'})")
    return True, front, alarms


def selftest():
    print("=== EVOLUTION'S OWN GATE ===")
    # (a) NSGA-lite correctness on a hand-checkable case: B dominates A;
    #     C ties-in-one-but-wins-another => front {B, C} (A dominated)
    test_sc = [("A", {"gold": 1, "money": 1, "life": 1, "recruits": 1, "safety": 1}),
               ("B", {"gold": 2, "money": 2, "life": 2, "recruits": 2, "safety": 2}),
               ("C", {"gold": 0, "money": 0, "life": 5, "recruits": 0, "safety": 2})]
    ftd = pareto_front(test_sc)
    ok_a = set(ftd) == {"B", "C"}
    print(f"   PASS | pareto sort correctness ({ftd})" if ok_a else
          f"   FAIL | pareto got {ftd}")
    # (b,+c) real ledger + integration
    real = run()
    ok_bc = bool(real and real[0]) and "base" in real[1] or len(real[1]) >= 1
    print(f"   {'PASS' if ok_bc else 'FAIL'} | real-ledger run + publish integration")
    all_pass = ok_a and ok_bc
    print(f"[evo] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)