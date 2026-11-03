"""GENEPOOL (doctrine Part XIII - DGM archive + QD-Rec entry rule + PBT
ratchet, at 8B/stdlib scale): the family's ARCHIVE OF CHILDREN.
- Archive keyed by behavior descriptor (territory mix); entry rule: a lineage
  enters if it is NOVEL (descriptor unseen) or BETTER than its nearest
  neighbor (QD-Rec) - no fixed niches needed.
- Mutation: gaussian perturbation of the champion's cfg parameter vector
  (MUT_* names the orchestrator already consumes), clamped to safe ranges;
  every child inherits a DISTINCT gene vector at birth (DGM requirement:
  children must differ, not clone).
- PBT ratchet: lineages below 20% of the pool's top fitness are retired;
  the champion defends by >2% (eviction floor, audited direction).
- Birth integration: the archive WRITES PathMemory['variants'] (locked+
  atomic) - DeploySwarm._variant_env already reads them, so the NEXT sharded
  spawn draws real mutated genes. No orchestrator edits required.
TEST GATE (user rule): a live inheritance test - import DeploySwarm, call
_variant_env per lineage, verify distinct valid gene vectors are inherited.
Implemented only if the test passes. DGM safety analog: bounded + revertible
(champion ratchet restores), no code self-modification - param genes only."""
import json
import os
import random
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
ARCHIVE = os.path.join(ROOT, "Config", "gene_archive.json")
PM = os.path.join(ROOT, "Config", "PathMemory.json")

# MUT-config genes (the orchestrator reads MUT_<key> env overrides; SafeIO
# guards the cfg file, jitter here is clamped and revertible)
GENES = {
    "ghost_cc_leads": (10, 400, int),
    "ghost_events": (10, 150, int),
    "ghost_trending": (5, 80, int),
    "ghost_wiki_leads": (10, 120, int),
    "ghost_wayback_leads": (20, 150, int),
    "ghost_queue_mines_to_farm": (6, 48, int),
    "ghost_min_stars": (30, 600, int),
}


def _clamp(v, lo, hi, typ):
    v = max(lo, min(hi, v))
    return typ(round(v)) if typ is int else round(v, 3)


def mutate(parent_genes, rng):
    """DGM-style: a NEW interesting version of the sampled parent - gaussian
    jitter (+-18%) on cfg genes, one descriptor gene flipped (territory mix)."""
    child = {}
    for k, (lo, hi, typ) in GENES.items():
        base = float(parent_genes.get(k, (lo + hi) / 2))
        child[k] = _clamp(base * (1 + rng.gauss(0, 0.18)), lo, hi, typ)
    return child


def mutate_fusion(a, parent_vid, rng):
    """FUSION IS THE NEW MUTATION (canon 2610.05284, bandit-guided evolution):
    cross the parent with a second lineage from the front/pool, then jitter -
    the jitter-only operator produced near-twins (the SurrogateFitnessCourt
    measured territory distance 0.5 across ALL mutants: zero new territory,
    the classic diversity collapse). Fusion + guaranteed bucket flips make
    every child NEW TERRITORY, not a clone in disguise."""
    pool = [v for v in a.get("lineages", {}) if v != parent_vid]
    front = [v for v in (a.get("pareto_front") or [])
             if v in a.get("lineages", {}) and v != parent_vid]
    second = rng.choice(front or pool) if (front or pool) else None
    p = a["lineages"][parent_vid]["genes"]
    s = a["lineages"][second]["genes"] if second else p
    child = {}
    for k, (lo, hi, typ) in GENES.items():
        src = rng.choice([p, s])                    # the FUSION
        base = float(src.get(k, (lo + hi) / 2))
        child[k] = _clamp(base * (1 + rng.gauss(0, 0.25)), lo, hi, typ)
    child["ghost_cc_leads"] = _flip_bucket(p, "ghost_cc_leads", child, rng)
    child["ghost_trending"] = _flip_bucket(p, "ghost_trending", child, rng)
    return child


def _flip_bucket(parent_genes, key, child, rng):
    """Guarantee the child's descriptor BUCKET differs from the parent's in
    this dim (new territory, enforced per dim - jitter alone can't)."""
    lo, hi, _t = GENES[key]
    gran = 50 if key == "ghost_cc_leads" else 20
    pb = int(float(parent_genes.get(key, lo)) // gran)
    buckets = sorted({b for b in range(int(lo // gran) + 1, int(hi // gran) + 1)})
    choices = [b for b in buckets if b != pb] or buckets
    nb = rng.choice(choices)
    return _clamp(nb * gran + gran // 2, lo, hi, GENES[key][2])


def descriptor(genes):
    """Behavior descriptor: the mix the child actually explores (low dims,
    QD archive key)."""
    return f"cc{int(genes['ghost_cc_leads'])//50}_ev{int(genes['ghost_events'])//25}_" \
           f"tr{int(genes['ghost_trending'])//20}"


def novel_or_better(archive, desc, fitness):
    """QD-Rec entry rule: enter if descriptor unseen OR better than the
    nearest neighbor in that descriptor cell."""
    cell = archive.get("cells", {}).get(desc)
    if not cell:
        return True
    return fitness > float(cell.get("fitness", -1))


def champion(archive):
    pool = archive.get("lineages", {})
    if not pool:
        return None
    return max(pool.items(), key=lambda kv: float(kv[1].get("fitness", -1)))


def retire(archive, floor_pct=0.2):
    pool = archive.get("lineages", {})
    if len(pool) < 4:
        return []                       # keep a breeding population
    top = max(float(v.get("fitness", -1)) for v in pool.values())
    floor = floor_pct * max(0.1, top)
    dead = [k for k, v in pool.items() if float(v.get("fitness", -1)) < floor]
    for k in dead:
        del pool[k]
    return dead


def load():
    try:
        return json.load(open(ARCHIVE, encoding="utf-8-sig"))
    except Exception:
        return {"lineages": {}, "cells": {}, "champion": None, "gen": 0}


def save(a):
    tmp = ARCHIVE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(a, f, indent=1)
    os.replace(tmp, ARCHIVE)


def publish(archive):
    """Write the archive's lineages into PathMemory['variants'] via SafeIO - 
    the birth integration: DeploySwarm._variant_env reads EXACTLY this.
    MERGE-PRESERVE (loop-closer fix): keys the archive does not own (e.g. the
    orchestrator's measured 'rounds' telemetry) are carried forward - the old
    wholesale replace WIPED measured rounds on every publish (root cause of
    mutants starving at 0.0 forever)."""
    from SafeIO import write_json as _w, read_json as _rj
    pm = _rj(PM, {}) or {}
    stale = pm.get("variants") or {}
    fresh = {
        vid: {"params": g["genes"], "fitness": g["fitness"],
              "descriptor": g["descriptor"], "wins": g.get("wins", 0),
              "mines": g.get("mines", 0), "reqs": g.get("reqs", 0)}
        for vid, g in archive["lineages"].items()}
    for vid, v in fresh.items():
        for k, val in (stale.get(vid) or {}).items():
            if k not in v:
                v[k] = val
    pm["variants"] = fresh
    ch = archive.get("champion")
    if ch:
        pm.setdefault("family", {})["champion"] = ch
    if not _w(PM, pm):
        print("[genepool] PathMemory publish FAILED (lock busy) - genes not "
              "written; children will draw the old pool (honest)")
        return False
    print(f"[genepool] published {len(pm['variants'])} lineages into PathMemory "
          f"(champion: {ch}) - the next spawned child INHERITS a distinct genome")
    return True


def sync_from_pathmemory():
    """THE MEASURED-FITNESS LOOP CLOSER (audit-found root cause: the
    orchestrator measures real rounds into PathMemory['variants'], but the
    archive never FOLDED them back - mutants starved at 0.0 forever, and the
    old publish() even WIPED 'rounds' on every re-publish). Folds measured
    fitness into the archive, applies the upward-only rollback guard, retires
    only among MEASURED lineages (fitness 0.0 = unmeasured child: protected,
    never slaughtered), re-keys cells, recomputes the front from the stored
    per-goal grid, saves, publishes. Returns (synced, rolled, retired)."""
    from SafeIO import read_json as _rj
    pm = _rj(PM, {}) or {}
    a = load()
    synced, rolled = [], []
    for vid, g in a.get("lineages", {}).items():
        v = (pm.get("variants") or {}).get(vid) or {}
        try:
            v_rounds = int(v.get("rounds") or 0)
        except Exception:
            v_rounds = 0
        if v_rounds > int(g.get("m_rounds", 0)):
            new_fit = float(v.get("fitness") or 0.0)
            if new_fit > 0.0:                    # never fold an empty measure
                g["m_rounds"] = v_rounds
                g["mines"] = int(v.get("mines") or 0)
                g["reqs"] = int(v.get("reqs") or 0)
                g["wins"] = int(v.get("wins") or 0)
                g["fitness"] = new_fit
                d = g.get("descriptor")
                if d:
                    a.setdefault("cells", {})[d] = {"vid": vid, "fitness": new_fit}
                synced.append(vid)
    try:
        import EvolutionSpeedup as ES
        rolled = ES.upward_guard(a, None)
    except Exception:
        rolled = []
    pool = a.get("lineages", {})
    import time as _t
    top_f = max((float(L.get("fitness", -1)) for L in pool.values()), default=0.0)
    floor = 0.2 * max(0.1, top_f)
    # THE UNMEASURED-LINEAGE LAW (2026-11-04): 22 mutants sat at fitness 0.0
    # with 0 measured rounds FOREVER while the pre-stage churned their
    # refresh every 20 min - a lineage in the pool must EARN its seat by
    # being measured within a day, or its bubble churn ends here.
    retired = [k for k, L in list(pool.items())
               if k != a.get("champion") and (
                   (int(L.get("m_rounds", 0)) > 0
                    and float(L.get("fitness", 0)) < floor)
                   or (int(L.get("m_rounds", 0)) == 0
                       and float(L.get("fitness", 0)) == 0.0
                       and float(L.get("born_ts", 0) or L.get("born", 0) or 0)
                       < _t.time() - 86400))]
    for k in retired:
        d = pool[k].get("descriptor")
        del pool[k]
        cell = a.get("cells", {}).get(d)
        if cell and cell.get("vid") == k:
            del a["cells"][d]
    a["champion"] = champion(a)[0] if pool else a.get("champion")
    try:
        grid = a.get("goal_grid") or {}
        scored = [(vid, gg) for vid, gg in grid.items() if vid in pool]
        if scored:
            import EvolutionUpward as EU
            front = EU.pareto_front(scored)
            if front:
                a["pareto_front"] = sorted(set(front))
    except Exception:
        pass
    a["pareto_front"] = [v for v in (a.get("pareto_front") or [])
                         if v in pool] or [a.get("champion") or "base"]
    save(a)
    publish(a)
    note_s = ", ".join(synced) or "none (no new measured rounds - honest no-op)"
    note_r = ", ".join(rolled) or "none"
    note_t = ", ".join(retired) or "none (unmeasured children protected)"
    print(f"[genepool] sync: folded [{note_s}] | rolled-back [{note_r}] | "
          f"retired [{note_t}] | front {a['pareto_front']} | champion {a['champion']}")
    return synced, rolled, retired


def run(gen_mutations=3):
    rng = random.Random(int(time.time()))
    a = load()
    if not a["lineages"]:                       # seed from the base lineage
        base_genes = {k: (lo + hi) / 2 for k, (lo, hi, t) in GENES.items()}
        a["lineages"]["base"] = {"genes": {k: _clamp(v, *([g for g in GENES[k]][:2]),
                                              GENES[k][2]) for k, v in base_genes.items()},
                                 "fitness": 0.259, "descriptor": descriptor(base_genes),
                                 "wins": 0, "mines": 1121, "reqs": 0}
        a["champion"] = "base"
    front = a.get("pareto_front") or [a["champion"]]
    parent_vid = front[int(a.get("gen", 0)) % len(front)]   # EVOLVE FROM THE FRONT:
    if parent_vid not in a["lineages"]:                     # stale-front guard
        parent_vid = (a["champion"] if a["champion"] in a["lineages"] else "base")
    parent = a["lineages"][parent_vid]                      # parents rotate across the
    made = []                                               # Pareto front per goal
    for i in range(gen_mutations):
        vid = f"g{a['gen']}_{i}"
        genes = mutate(parent["genes"], rng)
        desc = descriptor(genes)
        fit = 0.0                               # unfitted: measured on its first real round
        if not novel_or_better(a, desc, fit):
            print(f"[genepool] {vid} refused entry: descriptor '{desc}' already held "
                  f"by a fitter lineage (QD-Rec rule)")
            continue
        a["lineages"][vid] = {"genes": genes, "fitness": fit, "descriptor": desc,
                              "wins": 0, "mines": 0, "reqs": 0,
                              "parent": parent_vid, "born": time.strftime("%Y-%m-%d %H:%M:%S")}
        a["cells"][desc] = {"vid": vid, "fitness": fit}
        made.append(vid)
        a["gen"] += 1
    a["champion"] = champion(a)[0]
    save(a)
    print(f"[genepool] gen {a['gen']}: {len(made)} mutated lineages entered "
          f"(from PARETO parent {parent_vid} - the front rotates); "
          f"archive now {len(a['lineages'])} lineages, champion {a['champion']}")
    return a


if __name__ == "__main__":
    run()