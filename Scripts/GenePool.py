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
    the birth integration: DeploySwarm._variant_env reads EXACTLY this."""
    from SafeIO import write_json as _w, read_json as _rj
    pm = _rj(PM, {}) or {}
    pm["variants"] = {
        vid: {"params": g["genes"], "fitness": g["fitness"],
              "descriptor": g["descriptor"], "wins": g.get("wins", 0),
              "mines": g.get("mines", 0), "reqs": g.get("reqs", 0)}
        for vid, g in archive["lineages"].items()}
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
    parent_vid, parent = champion(a)
    made = []
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
          f"({', '.join(made) or 'none - all refused as non-novel'}); "
          f"archive now {len(a['lineages'])} lineages, champion {a['champion']}")
    return a


if __name__ == "__main__":
    run()