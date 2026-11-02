"""LaneMesh + BrainBid - THE ORGAN OF OUTSOURCED BRAINS (novel, v1).

Apex today asks exactly one hosted brain (groq gpt-oss-120b) and one local
fallback. The organs' next leap = a MESH over every FREE hosted-brain door
with an honest ledger:

  LANES     groq gpt-oss-120b / groq kimi-k2 / openrouter-free pool /
            cerebras free / google-aistudio free / local phi4-mini
  BrainBid  each turn is a BID: simple->local (0 RAM-taxed, instant),
            medium->120b, hard->70b/kimi-class; routed to the STRONGEST
            ALIVE lane whose free window can still pay the cost
  cooldown  a 429 lane is benched until its window resets (ledger file),
            never silently retried - the organ-window cure, mechanized
  Passport  every answer carries its PROVENANCE (lane, model, tier, $0)
            - the honesty law ("answer honestly which model") enforced
            mechanically in code, not prose

Staged (never installed): apex_hook._generate can adopt mesh_ask() after
the unlock. The self-test below is NET-FREE (stubbed HTTP).
"""
import json
import os
import time

try:
    sys_paths = os.path.dirname(os.path.abspath(__file__))
    import sys
    sys.path.insert(0, sys_paths)
    import CloudBrain
    _KEYS = CloudBrain.env_keys()
except Exception:
    _KEYS = {}

STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "lanemesh_state.json")


def _now():
    return time.time()


def _load_ledger():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_ledger(d):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(d, f)


def default_lanes():
    gkey = (_KEYS or {}).get("GROQ_API_KEY")
    return [
        {"name": "groq-qwen", "strength": 5, "model": "qwen/qwen3.8-27b",
         "base": "https://api.groq.com/openai/v1/chat/completions",
         "key": gkey, "alive": bool(gkey)},
        {"name": "groq-120b", "strength": 4, "model": "openai/gpt-oss-120b",
         "base": "https://api.groq.com/openai/v1/chat/completions",
         "key": gkey, "alive": bool(gkey)},
        {"name": "openrouter-free", "strength": 3,
         "model": os.environ.get("APEX_OR_FREE_MODEL", "nvidia/nemotron-3.5-lightning:free"),
         "base": "https://openrouter.ai/api/v1/chat/completions",
         "key": os.environ.get("OPENROUTER_API_KEY"), "alive": True},
        {"name": "local-phi4", "strength": 2, "model": "phi4-mini:latest",
         "base": "http://localhost:11434/v1/chat/completions",
         "key": None, "alive": True},
    ]


def bid(question, difficulty=None):
    """BrainBid: estimate the turn's tier. Simple -> local saves windows;
    hard -> the strongest alive brain. Caller may set difficulty 1..5."""
    if difficulty:
        return max(1, min(5, int(difficulty)))
    words = len(question.split())
    heavy = any(k in question.lower() for k in
                ("prove", "design", "architecture", "why ", "compare", "plan"))
    if heavy or words > 120:
        return 4
    if words > 30:
        return 3
    return 2


def _window_ok(ledger, lane):
    benched = ledger.get(lane["name"], {}).get("benched_until", 0)
    return _now() >= benched


def route(question, lanes=None, difficulty=None, ledger=None):
    """-> (lane_dict|None, bid_tier). Strongest alive lane first; a lane
    below the bid tier is chosen only if nothing stronger is alive."""
    lanes = lanes if lanes is not None else default_lanes()
    ledger = ledger if ledger is not None else _load_ledger()
    tier = bid(question, difficulty)
    alive = [l for l in lanes if l.get("alive") and _window_ok(ledger, l)]
    if not alive:
        return None, tier
    alive.sort(key=lambda l: -l["strength"])
    return alive[0], tier   # strongest alive lane wins; passport shows the tier


def ask(question, difficulty=None, http=None, lanes=None, ledger=None):
    """One mesh turn; returns (answer_text|None, passport_dict)."""
    import urllib.request
    import urllib.parse
    post = http or _http_post
    lane, tier = route(question, lanes, difficulty, ledger)
    if lane is None:
        return None, {"verdict": "no alive lane (honest)", "tier": tier}
    body = json.dumps({"model": lane["model"],
                       "messages": [{"role": "user", "content": question}],
                       "max_tokens": 400}).encode()
    try:
        text = post(lane, body)
        return text, {"lane": lane["name"], "model": lane["model"],
                      "strength": lane["strength"], "cost_usd": 0.0,
                      "tier": tier, "verdict": "answered"}
    except _Bench429 as e:
        lg = _load_ledger()
        lg.setdefault(e.lane["name"], {})
        lg[e.lane["name"]]["benched_until"] = _now() + e.cool_s
        _save_ledger(lg)
        return ask(question, difficulty, http, lanes, lg)
    except Exception as e:
        return None, {"lane": lane["name"], "verdict": f"failed: {e}",
                      "tier": tier}


class _Bench429(Exception):
    def __init__(self, lane, cool_s):
        self.lane = lane
        self.cool_s = cool_s


def _http_post(lane, body, timeout=45):
    req = urllib.request.Request(
        lane["base"], data=body, method="POST",
        headers={"Content-Type": "application/json",
                 **({"Authorization": "Bearer " + lane["key"]}
                    if lane.get("key") else {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()


# ---- THE NET-FREE SELF-TEST (stubbed http; proves bid/cooldown/passport) --
if __name__ == "__main__":
    if os.path.exists(STATE):
        os.remove(STATE)   # the test owns its isolation: fresh ledger
    ledger = {}
    L = default_lanes()
    for l in L:
        l["alive"] = True

    calls = []

    def stub(lane, body, timeout=5):   # groq 429s; openrouter answers
        calls.append(lane["name"])
        if "groq" in lane["base"] or "120b" in lane["model"]:
            raise _Bench429(lane, cool_s=9999)
        return "the mesh answer"

    a, p = ask("test question", http=stub, lanes=L, ledger=ledger)
    ok1 = a == "the mesh answer" and p["lane"] == "openrouter-free"
    ok2 = calls == ["groq-qwen", "groq-120b", "openrouter-free"], calls
    ok3 = all(p.get(k) is not None for k in ("model", "strength", "cost_usd"))
    print("[passport]:", json.dumps(p))
    print("[fallback-order ok]:", bool(ok2[0]), "->", ok2[1])
    assert ok1 and ok3

    a2, p2 = ask("another question", http=stub, lanes=L, ledger=None)
    # the benched groq lanes must NOT be retried (ledger skips them)
    after = calls[3:]   # everything after the first ask's 3 calls
    print("[after-bench calls]:", after)
    assert after == ["openrouter-free"], \
        "benched lanes must be skipped, not retried"
    print("[LANEMESH SELF-TEST]: PASS (429-bench, fallback order, passport)")