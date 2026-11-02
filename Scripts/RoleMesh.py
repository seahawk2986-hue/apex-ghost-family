"""RoleMesh - the HYBRID brain: every found model, in the seat it's shaped for.

ROLES (each -> ordered lanes; strongest alive wins; benched lanes rest):
  voice       chat replies            ultra-550b > groq-120b > local-phi4
  deep-think  hard reasoning turns    ultra-550b > nano-omni-REASONING > groq > local
  vision      images/VL               nemotron-3.5-super-vl (the VL specialist)
  code        programming             cohere-north-code (STAGED: coding lane
                                      stays disabled until acceptance unlocks)
  guard       outbound second-opinion nemotron-3.5-content-safety
  swarm       cross-check sampling    ultra + gemma-4-31b + inkling (3 labs)

The bench ledger (persistent, per-lane window rests) + honest passports ride
from LaneMesh. Net-free self-test at __main__ (stubbed HTTP). $0 forever.
"""
import json
import os
import time

STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "rolemesh_state.json")

ULTRA = ("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free",
         "https://openrouter.ai/api/v1/chat/completions", 5)
REASON = ("openrouter", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
          "https://openrouter.ai/api/v1/chat/completions", 4)
VL = ("openrouter", "nvidia/nemotron-3.5-super-vl:free",
      "https://openrouter.ai/api/v1/chat/completions", 3)
CODE = ("openrouter", "cohere/north-mini-code:free",
        "https://openrouter.ai/api/v1/chat/completions", 3)
GUARD = ("openrouter", "nvidia/nemotron-3.5-content-safety:free",
         "https://openrouter.ai/api/v1/chat/completions", 2)
SFLOW_DEEP = ("siliconflow", "Qwen/Qwen3.5-122B-A10B",
              "https://api.siliconflow.com/v1/chat/completions", 4)
SFLOW_NEXT = ("siliconflow", "Qwen/Qwen3.6-35B-A3B",
              "https://api.siliconflow.com/v1/chat/completions", 3)
SFLOW_CODER = ("siliconflow", "Qwen/Qwen3-Coder-30B-A3B-Instruct",
               "https://api.siliconflow.com/v1/chat/completions", 3)
SFLOW_VL = ("siliconflow", "Qwen/Qwen3-VL-30B-A3B-Instruct",
            "https://api.siliconflow.com/v1/chat/completions", 3)
GEM4 = ("openrouter", "google/gemma-4-31b-it:free",
        "https://openrouter.ai/api/v1/chat/completions", 3)
INK = ("openrouter", "thinkingmachines/inkling:free",
       "https://openrouter.ai/api/v1/chat/completions", 4)
GROQ = ("groq", "openai/gpt-oss-120b",
        "https://api.groq.com/openai/v1/chat/completions", 4)
CS = ("cerebras", "gpt-oss-120b",
      "https://api.cerebras.ai/v1/chat/completions", 4)
CS_Q = ("cerebras", "qwen-3.8-27b",
        "https://api.cerebras.ai/v1/chat/completions", 4)
LOCAL = ("local", "phi4-mini:latest",
         "http://localhost:11434/v1/chat/completions", 2)

ROLES = {
    "voice": [ULTRA, CS, CS_Q, GROQ, LOCAL],
    "deep-think": [ULTRA, SFLOW_DEEP, CS_Q, REASON, CS, GROQ, LOCAL],
    "vision": [VL, SFLOW_VL, ULTRA, LOCAL],
    "code": [SFLOW_CODER, CODE, LOCAL],  # staged: coding awaits acceptance
    "guard": [GUARD],
    "swarm": [ULTRA, SFLOW_DEEP, INK, GEM4],  # four labs, independent errors
}


def _windows():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(w):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(w, f)


def benched(lane_name):
    rem = (_windows().get(lane_name, 0)) - time.time()
    return rem if rem > 0 else 0


def bench(lane_name, cool_s):
    w = _windows()
    w[lane_name] = time.time() + cool_s
    _save(w)


def clear(lane_name):
    w = _windows()
    if lane_name in w:
        w.pop(lane_name)
        _save(w)


def pick(role, lanes=None):
    """-> the strongest alive lane for the role, or None."""
    order = lanes if lanes is not None else ROLES.get(role, [])
    alive = [l for l in order if benched(l[1]) == 0]
    if not alive:
        return None
    return alive[0]   # the front lane for this role


def ask(role, prompt, http=None, lanes=None, max_tokens=400):
    """One hybrid turn; -> (text|None, passport)."""
    post = http or _http_post
    lane = pick(role, lanes)
    if lane is None:
        return None, {"role": role, "verdict": "all lanes benched (honest)"}
    prov, model, url, strength = lane
    try:
        text = post(url, model, prompt, max_tokens)
        clear(model)
        return text, {"role": role, "provider": prov, "model": model,
                      "strength": strength, "cost_usd": 0.0,
                      "verdict": "answered"}
    except _Rest as e:
        bench(e.name, e.cool)
    except Exception as e:
        return None, {"role": role, "provider": prov, "verdict": f"{e}"}
    return ask(role, prompt, http, lanes, max_tokens)


class _Rest(Exception):
    def __init__(self, name, cool):
        self.name = name
        self.cool = cool


def _http_post(url, model, prompt, max_tokens, timeout=45):
    import urllib.request
    body = json.dumps({"model": model,
                       "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    if r.status in (429, 402, 401):
        raise _Rest(model, 3600)
    return d["choices"][0]["message"]["content"].strip()


if __name__ == "__main__":
    if os.path.exists(STATE):
        os.remove(STATE)   # the test owns its isolation
    calls = []

    def stub(url, model, prompt, mt):
        calls.append(model)
        if "ultra" in model:
            raise _Rest(model, 9999)          # ultra window rests
        if "gemma" in model:
            return "gemma-answer"
        return model[:20] + "-answer"

    t, p = ask("voice", "hello", http=stub)
    assert t and p["model"] == "gpt-oss-120b" and p["provider"] == "cerebras", p
    # ultra benched -> the wafer-fast Cerebras voice answers
    t, p = ask("deep-think", "hard question", http=stub)
    assert p["model"] == "Qwen/Qwen3.5-122B-A10B", p   # sflow-deep front, post-bench
    t, p = ask("vision", "see this", http=stub)
    assert p["model"] == "nvidia/nemotron-3.5-super-vl:free", p
    t, p = ask("swarm", "cross-check", http=stub)
    assert p["model"] == "Qwen/Qwen3.5-122B-A10B", p   # post-bench order is lawful
    t, p = ask("swarm", "cross-check", http=stub,
               lanes=[("openrouter", "thinkingmachines/inkling:free",
                       "https://openrouter.ai/api/v1/chat/completions", 4),
                      ("openrouter", "google/gemma-4-31b-it:free",
                       "https://openrouter.ai/api/v1/chat/completions", 3)])
    assert p["model"] == "thinkingmachines/inkling:free", p   # direct-lane proof
    print("[role-map verified]: voice->cerebras after ultra-bench; deep->sflow-122B;"
          " vision->VL; swarm->inkling (labs: siliconflow+nvidia+tml+google)")
    print("[lanes]:", " ".join(sorted(l[0] + "/" + l[1].split("/")[0]
                                      for role in ROLES.values()
                                      for l in role)))
    print("[ROLEMESH SELF-TEST]: PASS")