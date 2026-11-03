"""ApexShard - PHASE 3: the upstream key array + 429/503/timeout hot-swap.

The honest shard = OUR REAL multi-provider array (one key per provider,
from .env - never identity games); the rotator honors LaneGuard's pace
ledger and the local Ollama/LM Studio floor = the absolute bottom layer.
"""
import json
import os
import threading
import time

import requests

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
STATE = os.path.join(REPO, "scores", "lane_state.json")
CURSOR = os.path.join(REPO, "scores", "shard_cursor.json")

# Tier 2 - the free external lanes (verified live this week)
# Tier 3 - the deep doors (pro class) - same array, flagged deep
LANES = [
    ("cerebras-120b", "https://api.cerebras.ai/v1/chat/completions",
     "CEREBRAS_API_KEY", "gpt-oss-120b", "medium"),
    ("groq-120b", "https://api.groq.com/openai/v1/chat/completions",
     "GROQ_API_KEY", "openai/gpt-oss-120b", "medium"),
    ("groq-qwen", "https://api.groq.com/openai/v1/chat/completions",
     "GROQ_API_KEY", "qwen/qwen3.8-27b", "medium"),
    # the NIM unlocks (free trial, verified 200 on 11/02): the spec's tier-2 exactly
    ("nim-v41f", "https://integrate.api.nvidia.com/v1/chat/completions",
     "NVIDIA_API_KEY", "deepseek-ai/deepseek-v4.1-flash", "medium"),
    ("nim-glm", "https://integrate.api.nvidia.com/v1/chat/completions",
     "NVIDIA_API_KEY", "z-ai/glm-5.3-flash", "medium"),
    # the catalog-verified auto-router: one key, whatever massive model is free
    ("or-auto", "https://openrouter.ai/api/v1/chat/completions",
     "OPENROUTER_API_KEY", "openrouter/free", "medium"),
    ("gemini-flash", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
     "GEMINI_API_KEY", "gemini-3.8-flash", "medium"),
    ("gemini-pro", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
     "GEMINI_API_KEY", "gemini-3.1-pro-preview", "deep"),
    # THE TITAN SEAT #1 (the kimi-k3 corpse replaced by its live lineage -
    # probed live 2026-11-04, moonshot's current frontier: FrontierSWE 81.2
    # class, the deep-reasoning + SWE-class code seat; free trial 60 RPM)
    ("nim-kimi-k26", "https://integrate.api.nvidia.com/v1/chat/completions",
     "NVIDIA_API_KEY", "moonshotai/kimi-k2.6", "deep"),
    # THE TITAN SEAT #2 (the deepseek-v4-pro corpse replaced by nvidia's
    # biggest listed brain: the 550B MoE - the deep tier's ceiling seat)
    ("nemotron-550b", "https://integrate.api.nvidia.com/v1/chat/completions",
     "NVIDIA_API_KEY", "nvidia/nemotron-3-ultra-550b-a55b", "deep"),
    ("local-floor", "http://localhost:11434/v1/chat/completions",
     None, "phi4-mini:latest", "floor"),
]
CODE_FLOOR = ("local-coder", "http://127.0.0.1:1234/v1/chat/completions",
              None, "qwen2.5-coder-7b-instruct", "floor-code")

_lock = threading.Lock()
STORM_BUDGET = {"protected": 30, "batch": 12}
# THE QoS CLASSES (2026-11-04; canon: DriftSched's QoS-aware scheduling +
# CALM's routing, both 2026-sourced in the speed ledger): the founder-facing
# calls draw from a PROTECTED budget the organs can never drain; the
# organs (gym/court/farm) draw from a smaller BATCH budget. A storm burns
# the class that CAUSED it - chat never starves behind organ churn.
DEFAULT_CLASS = "batch"

# THE TIERED, LENGTH-AWARE TIMEOUT LADDER (2026-11-04 — the long-promised
# combine, canon-verified: *Clairvoyant* [Predictive Shortest-Job-First Admission]
# = fast lanes answer FIRST with short waits; *OUTLETS* [Output-Length
# Prediction] + *Scheduling with Uncertainty-Aware Output Length Predictions* =
# scale the wait by the EXPECTED OUTPUT LENGTH, not a fixed wall):
#   every lane previously shared ONE timeout=75 — smalls starved behind deep -
#   brain waits; now tier caps + max_tokens-derived expected length bound the
#   dispatch. An explicit caller timeout STILL WINS (back-compat contract).
TIER_TIMEOUTS = {"floor": 45, "floor-code": 60, "medium": 60, "deep": 150}


def _tier_timeout(tier, max_tokens, timeout):
    if timeout is not None:
        return timeout                       # explicit callers keep the old contract
    cap = TIER_TIMEOUTS.get(tier or "medium", 60)
    est = 10.0 + 0.04 * float(max_tokens or 700)   # length-aware expectation
    return max(12.0, min(est, cap))


def _storm_ok(cls=None):
    """The per-CLASS retry budget (RetryGuard lesson + DriftSched QoS):
    a self-inflicted retry storm = worse than a wall; burns ITS OWN class's
    budget (organs cannot drain the founder-facing protected budget)."""
    cls = cls or DEFAULT_CLASS
    budget = STORM_BUDGET.get(cls, 12)
    try:
        now = time.time()
        log = []
        p = os.path.join(REPO, "scores", f"shard_retries_{cls}.jsonl")
        if os.path.isfile(p):
            for ln in open(p, encoding="utf-8"):
                try:
                    rec = json.loads(ln)
                    if now - rec.get("ts", 0) < 3600:
                        log.append(rec)
                except Exception:
                    continue
        if len(log) >= budget:
            return False
        log.append({"ts": now})
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for rec in log:
                f.write(json.dumps(rec) + "\n")
        os.replace(tmp, p)
        return True
    except Exception:
        return True  # the ledger must never block honest attempts


def env():
    """DELEGATED TO THE SPINE (2026-11-04): the same parser as every other
    organ (ApexIO.env) - the 3-schema drift class is dead."""
    import ApexIO
    return ApexIO.env(REPO)


def _cool(name):
    st = {}
    try:
        st = json.load(open(STATE, encoding="utf-8"))
    except Exception:
        pass
    rec = st.get(name, {})
    if rec.get("last_http") in (200,):
        return False
    return time.time() - rec.get("last_ok_ts", 0) < 60  # honor the pacer


def call(env, order, messages, max_tokens=700, timeout=None, cls=None):
    """Round-robin dispatch: throttle/503/timeout = flag + hot-swap, no state drop.

    2026-11-04 hardening:
      - the LENGTH-AWARE TIER LADDER (see TIER_TIMEOUTS): per-tier cap +
        expected-length scaling; an explicit timeout still wins (compat).
      - per-CLASS storm budgets (chat protected / organs batch).
      - LIVE BANDIT OBSERVATIONS: every answer updates the LaneBandit's
        latency/ success record; every 410 feeds the corpse retirement."""
    if os.path.isfile(CURSOR):
        cur = json.load(open(CURSOR, encoding="utf-8")).get("i", 0)
    else:
        cur = 0
    tried, notes = [], []
    for off in range(len(order)):
        name, url, key, model, tier = order[(cur + off) % len(order)]
        if name in tried[1:]:
            continue                          # one honest try per lane per call
        tried.append(name)
        if key and _cool(name):
            notes.append(f"{name}: honoring the pacer")
            continue
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = "Bearer " + env.get(key, "")
        _t0 = time.time()
        try:
            r = requests.post(url, headers=headers,
                              timeout=_tier_timeout(tier, max_tokens, timeout),
                              json={"model": model, "max_tokens": max_tokens,
                                    "temperature": 0.0, "messages": messages})
            _ms = (time.time() - _t0) * 1000.0
            if r.status_code == 200:
                with _lock:
                    json.dump({"i": (cur + off + 1) % len(order)},
                              open(CURSOR, "w", encoding="utf-8"))
                try:
                    import LaneBandit as LB
                    LB.update(name, True, _ms)
                except Exception:
                    pass
                return name, model, r.json()["choices"][0]["message"].get(
                    "content", ""), notes
            if r.status_code == 410:
                notes.append(f"{name}: HTTP 410 - the model is GONE (retire-count +1)")
                try:
                    _st_p = STATE
                    _st = json.load(open(_st_p, encoding="utf-8-sig")) if os.path.isfile(_st_p) else {}
                    _rec = _st.setdefault(name, {})
                    _rec["last_http"] = 410
                    _rec["e410"] = _rec.get("e410", 0) + 1
                    _tmp = _st_p + ".tmp"
                    json.dump(_st, open(_tmp, "w", encoding="utf-8"), indent=1)
                    os.replace(_tmp, _st_p)
                except Exception:
                    pass
                continue
            if r.status_code in (429, 503, 500):
                notes.append(f"{name}: HTTP {r.status_code} - shard swapped")
                if not _storm_ok(cls):
                    notes.append(f"storm budget ({cls or DEFAULT_CLASS}) exhausted "
                                 "- the fleet walls honestly this hour")
                    return None, None, None, notes
                continue
            notes.append(f"{name}: HTTP {r.status_code} - honest skip")
        except Exception as e:
            notes.append(f"{name}: {type(e).__name__} - shard swapped")
            if not _storm_ok(cls):
                notes.append(f"storm budget ({cls or DEFAULT_CLASS}) exhausted "
                             "- the fleet walls honestly this hour")
                return None, None, None, notes
    return None, None, None, notes


def order_for(tier3=False, code=False):
    """THE ONE-ROSTER LEARNED ORDER v3 (2026-11-04):
      one roster contract = the shard's LANES + AutoRoster's verified extras;
      the corpses (410-Gone x2) excluded from rotation;
      CapabilityMap's graded prior still promotes the winner to lead;
      the LaneBandit's live speed/ success evidence orders the tiers.
    The floors stay pinned per the RAM law (never bandit-rearranged)."""
    extras = []
    try:
        ex = json.load(open(os.path.join(REPO, "Config", "lane_extra.json"),
                            encoding="utf-8-sig")).get("lanes", [])
        seen = {l[0] for l in LANES}
        extras = [(l[0], l[1], l[2], l[3], l[4] if len(l) > 4 else "medium")
                  for l in ex if isinstance(l, (list, tuple)) and len(l) >= 3
                  and isinstance(l[0], str) and l[0] not in seen]
    except Exception:
        extras = []
    all_lanes = list(LANES) + extras
    st = {}
    try:
        st = json.load(open(STATE, encoding="utf-8-sig"))
    except Exception:
        pass
    retired = {k for k, v in (st or {}).items()
               if isinstance(v, dict) and v.get("retired")}
    flo = ([CODE_FLOOR] if code else []) + \
          [l for l in all_lanes if l[4] == "floor" and l[0] not in retired]
    med = [l for l in all_lanes if l[4] == "medium" and l[0] not in retired]
    deep = ([l for l in all_lanes if l[4] == "deep" and l[0] not in retired]
            if tier3 else [])
    ordered = flo + med + deep
    try:
        import LaneBandit as LB
        ordered = flo + LB.order(med + deep, pacer_cool=_cool)
    except Exception:
        pass
    ordered[0] = _learner_promote(ordered) or ordered[0]
    return ordered


def _learner_promote(order):
    """CapabilityMap's verdict: the measured-best lane moves to the front."""
    try:
        sys.path.insert(0, os.path.join(REPO, "Scripts"))
        import CapabilityMap as CM
        fam = "code" if any(l[0] == "local-coder" for l in order) else "chat"
        cands = [l[0] for l in order if l[4] in ("medium", "deep")]
        winner = CM.best_for(fam, cands)
        if winner:
            for lane in order:
                if lane[0] == winner:
                    return lane
    except Exception:
        pass
    return None


if __name__ == "__main__":
    e = env()
    order = order_for(tier3=False)
    sys.path.insert(0, os.path.join(REPO, "Scripts"))
    import ApexCache as C
    msgs = [{"role": "user", "content": "Say SHARD-OK in 2 words."}]
    name, model, reply, notes = call(e, order, msgs, max_tokens=12)
    for n in notes:
        print("   ", n)
    print("[shard]:", name, model, "->", (reply or "")[:40])
    print("[order]:", [o[0] for o in order])