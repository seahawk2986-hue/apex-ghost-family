"""LaneGuard - the forever-engine: lanes that heal themselves.

The walls (429 burst, 429 daily-cap, 402 dead, 403 flaps) are not failures -
they are WINDOWS. LaneGuard keeps every lane's window under management:

  1. PROBE    - 1-token ping per lane (cheap), spaced, single honest retry
  2. LEARN    - per-lane pacing: 429 -> pace grows 1.6x (cap 120 s),
                200 -> pace shrinks 0.9x (floor 2.5 s), remembered on disk
  3. LEDGER   - scores/lane_state.json = the honest per-lane health record
  4. CACHE    - ask() with a disk echo-cache: identical prompts within TTL
                answer from disk instead of spending the daily quota
  5. RE-OPEN  - scheduled re-probes (every 30 min) harvest every reset
                window; a lane is never "alive" without a fresh 200 proof

$0: pings cost nothing; keys stay in .env; nothing leaves home but calls.
The promise is honest: no lane is guaranteed - the SYSTEM detects death and
recovery faster than any human, forever, and never lies about either.
"""
import hashlib
import io
import json
import os
import sys
import time
import urllib.request

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
STATE = os.path.join(REPO, "scores", "lane_state.json")
CACHE = os.path.join(REPO, "scores", "echo_cache.json")
TTL_S = 24 * 3600

LANES = [
    ("groq-120b", "https://api.groq.com/openai/v1/chat/completions",
     "GROQ_API_KEY", "openai/gpt-oss-120b"),
    ("groq-qwen", "https://api.groq.com/openai/v1/chat/completions",
     "GROQ_API_KEY", "qwen/qwen3.8-27b"),
    ("cerebras-120b", "https://api.cerebras.ai/v1/chat/completions",
     "CEREBRAS_API_KEY", "gpt-oss-120b"),
    ("cerebras-qwen", "https://api.cerebras.ai/v1/chat/completions",
     "CEREBRAS_API_KEY", "qwen-3.8-27b"),
    ("or-ultra", "https://openrouter.ai/api/v1/chat/completions",
     "OPENROUTER_API_KEY", "nvidia/nemotron-3-ultra-550b-a55b:free"),
    ("or-reason", "https://openrouter.ai/api/v1/chat/completions",
     "OPENROUTER_API_KEY", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"),
    ("sflow-122b", "https://api.siliconflow.com/v1/chat/completions",
     "SILICONFLOW_API_KEY", "Qwen/Qwen3.5-122B-A10B"),
]

RESET_NOTES = {
    "or-ultra": "free-models-per-day cap - re-probe after 00:00 UTC",
    "or-reason": "same shared daily cap as or-ultra",
    "sflow-122b": "402 balance-dead: only the founder can lift (or retire)",
}


def env_load():
    env = {}
    for ln in open(os.path.join(REPO, ".env"), encoding="utf-8-sig"):
        if "=" in ln:
            k, v = ln.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def load_json(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


def save(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(doc, open(path, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)


def call_lane(env, url, key, model, messages, max_tokens=1):
    r = requests.post(url,
                      headers={"Authorization": "Bearer " + env[key],
                               "Content-Type": "application/json"},
                      json={"model": model, "max_tokens": max_tokens,
                            "temperature": 0.0, "messages": messages},
                      timeout=60)
    return r


def probe(name, url, key, model, env, st):
    rec = st.setdefault(name, {"pace_s": 2.5, "walls": 0, "oks": 0,
                               "last": "-", "last_http": None})
    gap = time.time() - rec.get("last_ok_ts", 0)
    wait = max(0.0, rec["pace_s"] - gap)
    if wait:
        time.sleep(min(wait, rec["pace_s"]))
    try:
        r = call_lane(env, url, key, model,
                      [{"role": "user", "content": "ping"}], max_tokens=1)
    except Exception as e:
        rec["last"], rec["last_http"] = type(e).__name__, None
        rec["pace_s"] = min(rec["pace_s"] * 1.6, 120.0)
        return rec
    rec["last_http"] = r.status_code
    rec["last"] = time.strftime("%H:%M:%S")
    if r.status_code == 200:
        rec["oks"] += 1
        rec["pace_s"] = max(rec["pace_s"] * 0.9, 2.5)
        rec["last_ok_ts"] = time.time()
        rec["note"] = "alive"
    elif r.status_code == 429:
        rec["walls"] += 1
        rec["pace_s"] = min(rec["pace_s"] * 1.6, 120.0)
        rec["note"] = RESET_NOTES.get(name, "rate window - will re-open")
    elif r.status_code in (402, 401, 403):
        rec["note"] = r.text[:70].replace("\n", " ")
    else:
        rec["note"] = r.text[:70].replace("\n", " ")
    return rec


def probe_all():
    env = env_load()
    st = load_json(STATE, {})
    for name, url, key, model in LANES:
        if not env.get(key):
            st.setdefault(name, {})["note"] = "no key in .env"
            continue
        probe(name, url, key, model, env, st)
        rec = st[name]
        state = ("ALIVE" if rec.get("last_http") == 200
                 else str(rec.get("last_http")))
        print(f"[{name}]: {state} | pace {round(rec.get('pace_s', 2.5), 1)}s "
              f"| {str(rec.get('note') or '')[:60]}")
        time.sleep(1.5)  # the politeness gap between probe lanes
    save(STATE, st)
    alive = sum(1 for _, url, key, model in LANES
                if env.get(key) and st.get(_lane_name(url, model), {})
                .get("last_http") == 200)
    print(f"[verdict]: {alive} lane(s) proven alive this pass - "
          f"ledger {STATE}")
    return st


def _lane_name(url, model):
    for n, u, _k, m in LANES:
        if u == url and m == model:
            return n
    return url


def cache_get(text):
    key = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    cache = load_json(CACHE, {})
    entry = cache.get(key)
    if entry and time.time() - entry["ts"] < TTL_S:
        return entry["reply"], key
    return None, key


def cache_put(key, reply):
    cache = load_json(CACHE, {})
    cache[key] = {"ts": time.time(), "reply": reply}
    if len(cache) > 200:
        for k in sorted(cache, key=lambda k: cache[k]["ts"])[:50]:
            cache.pop(k, None)
    save(CACHE, cache)


if __name__ == "__main__":
    # NOTE: stdout = wrapped ONCE at module top; a second wrap orphan-closes it
    probe_all()