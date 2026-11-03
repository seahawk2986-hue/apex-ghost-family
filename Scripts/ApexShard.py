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
    # the NIM flagships (build.nvidia.com, verified 11/02): dormant until the free trial key
    ("nim-k3", "https://integrate.api.nvidia.com/v1/chat/completions",
     "NVIDIA_API_KEY", "moonshotai/kimi-k3", "deep"),
    ("nim-v4pro", "https://integrate.api.nvidia.com/v1/chat/completions",
     "NVIDIA_API_KEY", "deepseek-ai/deepseek-v4-pro-0813", "deep"),
    ("local-floor", "http://localhost:11434/v1/chat/completions",
     None, "phi4-mini:latest", "floor"),
]
CODE_FLOOR = ("local-coder", "http://127.0.0.1:1234/v1/chat/completions",
              None, "qwen2.5-coder-7b-instruct", "floor-code")

_lock = threading.Lock()
STORM_BUDGET = 30            # RetryGuard-class cap: max swapped-retries per hour, fleet-wide

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


def _storm_ok():
    """The fleet-wide retry budget (RetryGuard lesson): a self-inflicted retry
    storm = worse than a wall. Reads+writes a rolling-hour counter."""
    try:
        now = time.time()
        log = []
        p = os.path.join(REPO, "scores", "shard_retries.jsonl")
        if os.path.isfile(p):
            for ln in open(p, encoding="utf-8"):
                try:
                    rec = json.loads(ln)
                    if now - rec.get("ts", 0) < 3600:
                        log.append(rec)
                except Exception:
                    continue
        if len(log) >= STORM_BUDGET:
            return False
        log.append({"ts": now})
        with open(p, "w", encoding="utf-8") as f:
            for rec in log:
                f.write(json.dumps(rec) + "\n")
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


def call(env, order, messages, max_tokens=700, timeout=None):
    """Round-robin dispatch: throttle/503/timeout = flag + hot-swap, no state drop.

    2026-11-04 hardening:
      - the LENGTH-AWARE TIER LADDER (see TIER_TIMEOUTS): per-tier cap +
        expected-length scaling; an explicit timeout still wins (compat).
      - the STORM BUDGET is ENFORCED at last (the audited bug: _storm_ok()
        was never called from call() - a self-inflicted retry storm could
        burn the fleet's hour unbounded; now each hot-swap consumes one
        unit of STORM_BUDGET and past the cap the fleet WALLS honestly)."""
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
        try:
            r = requests.post(url, headers=headers,
                              timeout=_tier_timeout(tier, max_tokens, timeout),
                              json={"model": model, "max_tokens": max_tokens,
                                    "temperature": 0.0, "messages": messages})
            if r.status_code == 200:
                with _lock:
                    json.dump({"i": (cur + off + 1) % len(order)},
                              open(CURSOR, "w", encoding="utf-8"))
                return name, model, r.json()["choices"][0]["message"].get(
                    "content", ""), notes
            if r.status_code in (429, 503, 500):
                notes.append(f"{name}: HTTP {r.status_code} - shard swapped")
                if not _storm_ok():
                    notes.append("storm budget exhausted - the fleet walls "
                                 "honestly this hour (no retry storm)")
                    return None, None, None, notes
                continue
            notes.append(f"{name}: HTTP {r.status_code} - honest skip")
        except Exception as e:
            notes.append(f"{name}: {type(e).__name__} - shard swapped")
            if not _storm_ok():
                notes.append("storm budget exhausted - the fleet walls "
                             "honestly this hour (no retry storm)")
                return None, None, None, notes
    return None, None, None, notes


def order_for(tier3=False, code=False):
    """THE LEARNED ORDER (the 91-paper combine #2): if CapabilityMap has
    graded evidence, the winning lane leads the medium tier; the static
    tier order = the honest fallback where no evidence exists."""
    base = ([CODE_FLOOR] if code else []) + \
           ([l for l in LANES if l[4] == "floor"]) + \
           [l for l in LANES if l[4] == "medium"] + \
           ([l for l in LANES if l[4] == "deep"] if tier3 else [])
    base[0] = _learner_promote(base) or base[0]
    return base


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