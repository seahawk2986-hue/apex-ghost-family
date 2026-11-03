"""CapabilityMap - the router that learns (the 91-paper #1 gap-closer).

Paper family: "From Sampled Outcomes to Capability Distributions", LLMRank,
Expected Reward Prediction. The idea shipped: every graded run (the exam,
the bench, the arena) writes a (family, lane, accuracy) sample; the map
keeps the Bayesian-ish average per (lane, family) and the Sharder reads the
map at dispatch - free-tier routing that LEARNS instead of guessing.

Usage:
  record(family, lane, pass_bool)
  best_for(family) -> lane_name or None (falls back to static tiers)
"""
import json
import os
import time

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
MAPP = os.path.join(REPO, "scores", "capability_map.json")
PRIOR_RUNS = 2          # Bayesian prior: a lane needs 3+ samples to beat 50/50
PRIOR_ACC = 0.5


def _load():
    try:
        return json.load(open(MAPP, encoding="utf-8"))
    except Exception:
        return {}


def record(family, lane, correct):
    m = _load()
    fam = m.setdefault(family, {})
    rec = fam.setdefault(lane, {"runs": PRIOR_RUNS, "hits": PRIOR_ACC * PRIOR_RUNS})
    rec["runs"] += 1
    if correct:
        rec["hits"] += 1
    os.makedirs(os.path.dirname(MAPP), exist_ok=True)
    json.dump(m, open(MAPP, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def score(family, lane):
    rec = _load().get(family, {}).get(lane)
    if not rec or rec.get("runs", 0) <= PRIOR_RUNS:
        return None, 0            # not enough evidence - the prior stays prior
    return rec["hits"] / rec["runs"], rec["runs"]


def best_for(family, candidates):
    """The learned best lane among the candidates; None = no evidence yet
    (the static tier order stays in charge - the honest default)."""
    best, best_score = None, PRIOR_ACC
    for lane in candidates:
        s, n = score(family, lane)
        if n >= 3 and s > best_score:
            best, best_score = lane, s
    return best


if __name__ == "__main__":
    for f in ("math", "agentic", "code"):
        for lane in ("gpt-oss-120b", "qwen3.8-27b", "nim-v41f"):
            record(f, lane, lane != "nim-v41f")   # the smoke: two win, one trails
    m = _load()
    for f in ("math", "agentic", "code"):
        b = best_for(f, ["gpt-oss-120b", "qwen3.8-27b", "nim-v41f"])
        s = score(f, b)
        print(f"[{f}]: best = {b} | acc {round(100 * s[0], 1)}% over {s[1]} runs")
    print("[capability-map]: live at", MAPP)