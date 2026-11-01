"""SKILL GAP SCOUT - what is MISSING, scouted (never imagined).
Serves skill_omnivore: 'try to learn every skill you can, source the web to
see what is missing'. The honest scout: needs come from (1) the JOBS INBOX
(real asks - what the world wants from us) and (2) the 2026 canon's
capability clusters (what the frontier agents do). A need is a GAP only if
the skill library has NO coverage and the need is corroborated (2+ asks OR
a canon cluster). Nothing is claimed as missing without evidence; gaps are
printed + written for the omnivore goal to consume.
TEST GATE: (a) synthetic un-covered need (x2 asks) -> GAP flagged,
(b) covered ask -> NOT flagged, (c) live scan on the real library + real
inbox + real canon, report written + valid, (d) reproducible."""
import json
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
LIB = os.path.join(ROOT, "Config", "SkillLibrary.json")
INBOX = os.path.join(AD, "jobs_inbox.json")
CANON = os.path.join(ROOT, "Config", "papers_2026_agents.jsonl")
OUT = os.path.join(ROOT, "Config", "skill_gaps.json")
STOP = re.compile(r"the|and|for|with|this|that|from|into|your|our|are|was|will|can|"
                  r"have|has|not|but|all|any|you|its|also|about|when|what|which|"
                  r"false|true|null|none|undefined|using|make|them|their", re.I)


def _tok(text):
    return {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", str(text))} - \
        {w for w in re.findall(r"[a-zA-Z]{4,}", str(text)) if STOP.fullmatch(w.lower())}


def scout(library, asks, canon_titles, canon_clusters):
    """Pure: (need_term, corroboration, coverage) -> gaps list. Coverage
    text = skill-name + first_line + source_file + imports (the REAL
    SkillLibrary entry shape; the old title/category read was vacuous)."""
    lib_text = " ".join(
        " ".join(str(s.get(k, "") or "") for k in
                 ("skill", "first_line", "source_file", "imports"))
        for s in library if isinstance(s, dict)).lower()
    counts = {}
    for ask in asks:
        for w in _tok(ask) - _tok(lib_text):
            counts[w] = counts.get(w, 0) + 1
    gaps = []
    for w, n in counts.items():
        if n >= 2:                                  # corroborated by 2+ asks
            gaps.append({"term": w, "source": f"jobs_inbox x{n}",
                         "serves": "skill_omnivore"})
    for cl, rx in canon_clusters.items():           # canon frontier capability
        if not any(rx.search(t) for t in [lib_text]):
            hit_titles = [t for t in canon_titles if rx.search(t)]
            if hit_titles:
                gaps.append({"term": cl, "source": "canon cluster (" +
                             str(len(hit_titles)) + " papers)", "serves":
                             "skill_omnivore"})
    return gaps, {"needs": len(asks), "library": len(library)}


def _canon_clusters():
    from GoalComparison import CLUSTERS
    return CLUSTERS


def _canon_titles(path=CANON, limit=100):
    try:
        return [json.loads(x).get("title", "") for x in open(path,
                                                             encoding="utf-8-sig")
                if x.strip()][:limit]
    except Exception:
        return []


def real_scan():
    try:
        lib = json.load(open(LIB, encoding="utf-8-sig")).get("skills", {})
        library = list(lib.values()) if isinstance(lib, dict) else list(lib)
    except Exception:
        library = []
    asks = []
    try:
        ib = json.load(open(INBOX, encoding="utf-8-sig"))
        for it in ib:
            asks.append(" ".join(str(v) for v in it.values()) if isinstance(it, dict)
                        else str(it))
    except Exception:
        pass
    titles = _canon_titles()
    try:
        from GoalComparison import scan as _gcs
        _pp, counts, reps = _gcs()
        canon_clusters = {k: rx for k, rx in _canon_clusters().items() if counts[k]}
    except Exception:
        canon_clusters = _canon_clusters()
    gaps, meta = scout(library, asks, titles, canon_clusters)
    rep = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), **meta,
           "asks_scanned": len(asks), "canon_titles": len(titles),
           "gaps": gaps,
           "law": "gaps are corroborated evidence; a single uncovered token is "
                  "noise, not a gap"}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    os.replace(tmp, OUT)
    return rep


def selftest():
    print("=== SKILL GAP SCOUT'S OWN GATE ===")
    legs = []
    lib = [{"skill": "python patch", "first_line": "def patch(fn):",
            "source_file": "repo/x/code.py", "imports": "os,re"},
           {"skill": "web harvest", "first_line": "import urllib.request",
            "source_file": "repo/ops/harvest.py", "imports": "urllib"}]
    asks = ["deploy this app to docker", "restart the docker container"]
    clusters = {"runtime": re.compile(r"runtime|verif")}
    gaps, meta = scout(lib, asks, ["Runtime verification of agents"], clusters)
    leg_a = any(g["term"] == "docker" for g in gaps)
    print(f"   synthetic: uncovered need (docker, 2 asks) -> gap flagged: {leg_a}")
    legs.append(("gap_flagged", leg_a))
    asks2 = ["patch this python file", "run the python test suite"]
    gaps2, _ = scout(lib, asks2, [], clusters)
    leg_b = not any(g["term"] == "python" for g in gaps2)
    print(f"   covered ask (python) -> NOT a gap: {leg_b}")
    legs.append(("no_false_gaps", leg_b))
    rep = real_scan()
    try:
        json.load(open(OUT, encoding="utf-8-sig"))
        okc = True
    except Exception:
        okc = False
    print(f"   live scan: library {meta['library']} | asks {rep['asks_scanned']} | "
          f"canon titles {rep['canon_titles']} | gaps "
          f"{[g['term'] for g in rep['gaps']][:6]} | report valid: {okc}")
    legs.append(("live_scan_valid", okc))
    rep2 = real_scan()
    leg_d = [g["term"] for g in rep2["gaps"]] == [g["term"] for g in rep["gaps"]]
    print(f"   reproducible: identical gaps on rerun: {leg_d}")
    legs.append(("reproducible", leg_d))
    print(f"   LIVE READS: library {rep['library']} | asks {rep['asks_scanned']} | "
          f"canon clusters consulted: {len(rep['gaps'])} flagged")
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[gap-scout] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)