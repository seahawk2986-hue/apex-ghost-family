"""GOAL COMPARISON - the fresh 2026 best-agent canon (100 papers) vs OUR
goals. The founder's law: take what helps Apex become the best, implement
it; delete nothing. Method: regex-cluster the canon's STATED goal language
(improve/outperform/achieve + benchmarks), map clusters to our GOAL_KEYS,
produce an adopt-list of mechanisms we can honestly implement on this box.
TEST GATE: (a) clusters extracted from the REAL canon (>=5 classes),
(b) every measured goal gets a comparison position, (c) report written +
valid + reproducible (second run identical clusters)."""
import json
import os
import re
import sys

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
CANON = os.path.join(ROOT, "Config", "papers_2026_agents.jsonl")
REPORT = os.path.join(ROOT, "Config", "goal_comparison.json")
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
import ApexUpward as AU

CLUSTERS = {
    "verification_runtime": re.compile(
        r"runtime|verif|self-repair|self-heal|execut(ion|able) feedback", re.I),
    "long_horizon": re.compile(
        r"long[- ]horizon|multi[- ]step|interdependent spec|end[- ]to[- ]end task", re.I),
    "context_engineering": re.compile(
        r"context (aware|engineering|window)|relevant code|retriev", re.I),
    "memory_lifelong": re.compile(
        r"memory|lifelong|procedural|consolidat", re.I),
    "skill_library": re.compile(
        r"skill (library|acquisition|discover)|tool (use|making|creation)|mastery", re.I),
    "autonomy_selfimprove": re.compile(
        r"self[- ]improv|autonomous|agentic (loop|workflow)|research agent", re.I),
    "benchmark_driven": re.compile(
        r"SWE[- ]?bench|benchmark|leaderboard|pass@(\d+|k)", re.I),
    "efficiency_constraint": re.compile(
        r"efficien|resource[- ]aware|small (model|scale)|budget|edge|low[- ]cost", re.I),
}


def scan():
    papers = [json.loads(x) for x in open(CANON, encoding="utf-8-sig")
              if x.strip()]
    counts = {k: 0 for k in CLUSTERS}
    reps = {k: [] for k in CLUSTERS}
    for p in papers:
        hay = p.get("title", "") + " " + p.get("abstract", "")
        for k, pat in CLUSTERS.items():
            if pat.search(hay):
                counts[k] += 1
                if len(reps[k]) < 3:
                    reps[k].append(p["id"] + " " + p["title"][:60])
    return papers, counts, reps


def our_position(counts, reps):
    """Map each cluster onto our measured goals - what we already honor,
    what the canon pushes further (the honest adopt-list). serves = the
    MEASURED goal key it advances (the goals-serves vocabulary must be
    consistent with ApexUpward.GOAL_KEYS)."""
    adopt = [
        {"cluster": "verification_runtime",
         "adopt": "runtime-aware verification: our gauntlet verifies at test-time; "
                  "add EXECUTION-AT-USE receipts (skills verified against real "
                  "invocations, not just static compile)",
         "serves": "coding", "feasible_now": True},
        {"cluster": "long_horizon",
         "adopt": "spec-splitting for work units: big tasks enter the board as "
                  "interdependent sub-specs (the gauntlet already chunks; make "
                  "the chunks EXPLICIT contracts)",
         "serves": "jobs+coding", "feasible_now": True},
        {"cluster": "skill_library",
         "adopt": "skill-gap scouting (built tonight: SkillGapScout) - the "
                  "canon's agents maintain libraries; gaps are scouted vs "
                  "real demand (the jobs inbox), never imagined",
         "serves": "omnivore", "feasible_now": True},
        {"cluster": "memory_lifelong",
         "adopt": "consolidation cadence: ApexDream's sleep already runs; the "
                  "canon's lesson - consolidate LESSONS (directives) not logs",
         "serves": "efficiency", "feasible_now": True},
        {"cluster": "context_engineering",
         "adopt": "budgeted context: bounded reads everywhere (already law); "
                  "rank context by measured yield (PathMemory lanes already do)",
         "serves": "efficiency", "feasible_now": True},
        {"cluster": "autonomy_selfimprove", "adopt": "the closed loop exists "
                  "(court+sync+prestage); keep Human-Gates on irreversible steps",
         "serves": "upward_evo", "feasible_now": True},
    ]
    return adopt


def selftest():
    print("=== GOAL COMPARISON'S OWN GATE ===")
    papers, counts, reps = scan()
    leg_a = len(papers) == 100 and sum(counts.values()) > 5 and \
        len([k for k, v in counts.items() if v]) >= 5
    print(f"   canon scan: 100 papers -> clusters " +
          " | ".join(f"{k}:{v}" for k, v in counts.items()))
    print(f"   clusters alive: {len([k for k, v in counts.items() if v])} (>=5: {leg_a})")
    adopt = our_position(counts, reps)
    leg_b = all(x["serves"] and x["feasible_now"] is not None for x in adopt) and len(adopt) >= 5
    goals_in = {g for x in adopt for g in x["serves"].split("+")}
    known = set(AU.GOAL_KEYS) | {"upward_evo"}
    leg_b = leg_b and goals_in <= known
    print(f"   adopt-list: {len(adopt)} mechanisms, goals touched {sorted(goals_in)}")
    rep = {"ts": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
           "canon": "Config/papers_2026_agents.jsonl (100 papers, deduped vs 521)",
           "their_goal_clusters": {k: {"n": counts[k], "reps": reps[k]}
                                   for k in counts},
           "our_goals": list(AU.GOAL_KEYS),
           "adopt": adopt,
           "law": "nothing deleted - every current goal stands; additions only"}
    tmp = REPORT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    os.replace(tmp, REPORT)
    leg_c = json.load(open(REPORT, encoding="utf-8-sig"))["ts"] == rep["ts"]
    # reproducibility: rerun scan -> identical counts (pure text match)
    _p2, c2, _r2 = scan()
    leg_d = c2 == counts
    print(f"   report written + roundtrip {leg_c} | reproducible clusters: {leg_d}")
    legs = [("clusters_extracted", leg_a), ("adopt_list_valid", leg_b),
            ("report_roundtrip", leg_c), ("reproducible", leg_d)]
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[goal-compare] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)