"""LaneBandit - THE LEARNED LANE ORDER (2026-11-04, fleet organ #2).

THE WEAKNESS IT KILLS: the dispatch order was STATIC (a hardcoded tier list
with one CapabilityMap promotion) - the fleet knew WHO it used but never
learned WHICH lane answers fastest RIGHT NOW, cold lanes led dispatches
(nim-v41f ReadTimeout wastes the head of the order), and rate-walled lanes
weren't demoted inside the tier. A free fleet's true currency = time and
windows; the static order spends both.

THE ORGAN (novel, fleet-tier; every mechanism bounded):
  - eps-greedy ordering with a LATENCY-SHAPED reward: each call updates
    w/n + a TTFT EWMA per lane; q = success_rate / log(2 + ms_ewma/80):
    fast lanes win; reliable lanes win more.
  - EXPLORATION: eps=0.18 chance two adjacent lanes swap (the bandit
    keeps tasting the roster - a recovered lane re-earns position).
  - PACER AWARE: a lane in a 429-window demotes below healthy mediums
    (dispatch would skip it anyway - the order stays an honest receipt).
  - PRIOR: CapabilityMap's graded quality seeds earned weight (evidence-first).
  - the floor stays pinned first (the RAM law outranks the bandit).
Sources (verified):
  * Auer, Cesa-Bianchi & Fischer, "Finite-time Analysis of the Multiarmed
    Bandit Problem" (Machine Learning 47(2), 2002) - the eps-greedy/UCB
    class implemented here in miniature (classic + stable).
  * THE CURRENT CANON (scores/papers_speed_100.json, arXiv-sourced, 2026):
    "Token-Budget-Aware Pool Routing", "CALM: A Self-Adaptive Orchestration
    Approach for QoS-Aware Routing in Small Language Model based Systems",
    "DriftSched: Adaptive QoS-Aware Scheduling" - the bandit-for-LLM-
    routing class this organ applies at fleet scale.
$0, stdlib-only, single-file JSON state (no new deps, 16GB-safe).
"""
import json
import math
import os
import random
import time

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
STATE = os.path.join(REPO, "scores", "lane_state.json")
EPS = 0.18
MS_HALFLIFE_S = 80.0


def _load():
    try:
        return json.load(open(STATE, encoding="utf-8-sig"))
    except Exception:
        return {}


def _save(st):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, STATE)


def update(lane, ok, ms=0.0):
    """One honest observation: w/n + the latency EWMA (called by ApexShard)."""
    st = _load()
    b = st.setdefault("bandit", {}).setdefault(lane, {"n": 0, "w": 0, "ms": None})
    b["n"] += 1
    if ok:
        b["w"] += 1
        ms = float(ms or 0)
        b["ms"] = ms if b["ms"] is None else round(0.7 * b["ms"] + 0.3 * ms, 1)
    _save(st)
    return b


def q_score(lane_rec):
    """reward = success_rate / log(2 + ms/80): fast-and-alive wins.
    Unproven lanes get a modest curiosity prior (0.6 = just below a
    proven-1.0-slow lane, above a proven-failing lane)."""
    n = (lane_rec or {}).get("n", 0)
    if not n:
        return 0.6
    sr = (lane_rec or {}).get("w", 0) / n
    ms = (lane_rec or {}).get("ms") or 1500.0
    return sr / math.log(2.0 + ms / MS_HALFLIFE_S)


def order(tier_lanes, pacer_cool=None):
    """The ordered tier: the caller pins floors; the medium/deep tier =
    bandit-q sorted; pacer-windowed lanes pushed behind healthy lanes; an
    eps-greedy adjacent-swap keeps exploring."""
    st = _load()
    band = st.get("bandit", {})
    healthy, walled = [], []
    for lane in tier_lanes:
        if pacer_cool and pacer_cool(lane[0]):
            walled.append(lane)
        else:
            healthy.append((lane, band.get(lane[0])))
    healthy.sort(key=lambda t: -q_score(t[1]))
    if len(healthy) >= 2 and random.random() < EPS:
        i = random.randrange(len(healthy) - 1)
        healthy[i], healthy[i + 1] = healthy[i + 1], healthy[i]
    return [l for l, _ in healthy] + walled


def seed_from_capability_map():
    """The prior: CapabilityMap's graded verdicts become earned counts."""
    try:
        import CapabilityMap as CM
    except Exception:
        return "(no capability map - bandit learns from live traffic only)"
    st = _load()
    b = st.setdefault("bandit", {})
    for fam in ("chat", "code"):
        for lane in list(b.keys()) + ["groq-120b", "cerebras-120b"]:
            try:
                if CM.best_for(fam, [lane]) == lane:
                    r0 = b.setdefault(lane, {"n": 0, "w": 0, "ms": None})
                    if r0["n"] < 5:
                        r0["n"] += 4
                        r0["w"] += 4
            except Exception:
                continue
    _save(st)
    return "seeded from the capability map"


if __name__ == "__main__":
    import ApexShard as S
    print("LaneBandit selftest:")
    print(" ", seed_from_capability_map())
    med = [l for l in S.LANES if l[4] in ("medium", "deep")]
    print(" bandit order:", [l[0] for l in order(med)])
    update("cerebras-120b", True, 120.0)
    update("groq-120b", True, 350.0)
    print(" after 2 live observations (cerebras fast, groq slower):",
          [l[0] for l in order(med)][:3])