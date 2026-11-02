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


def env():
    e = {}
    for ln in open(os.path.join(REPO, ".env"), encoding="utf-8-sig"):
        if "=" in ln:
            k, v = ln.split("=", 1)
            e[k.strip()] = v.strip()
    return e


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


def call(env, order, messages, max_tokens=700, timeout=75):
    """Round-robin dispatch: throttle/503/timeout = flag + hot-swap, no state drop."""
    if os.path.isfile(CURSOR):
        cur = json.load(open(CURSOR, encoding="utf-8")).get("i", 0)
    else:
        cur = 0
    tried, notes = [], []
    for off in range(len(order)):
        name, url, key, model, tier = order[(cur + off) % len(order)]
        tried.append(name)
        if key and _cool(name):
            notes.append(f"{name}: honoring the pacer")
            continue
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = "Bearer " + env.get(key, "")
        try:
            r = requests.post(url, headers=headers, timeout=timeout,
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
                continue
            notes.append(f"{name}: HTTP {r.status_code} - honest skip")
        except Exception as e:
            notes.append(f"{name}: {type(e).__name__} - shard swapped")
    return None, None, None, notes


def order_for(tier3=False, code=False):
    base = ([CODE_FLOOR] if code else []) + \
           ([l for l in LANES if l[4] == "floor"]) + \
           [l for l in LANES if l[4] == "medium"] + \
           ([l for l in LANES if l[4] == "deep"] if tier3 else [])
    return base


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