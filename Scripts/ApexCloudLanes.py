"""
ApexCloudLanes - Cloud burst capacity for Apex.

The LOCAL stack (LM Studio + Ollama) is always the primary engine: free, fast,
private, unlimited. The cloud free tiers are ONLY used when local calls fail
or stall, tried fastest-first:

    Lane 1 (Groq,        ~0.2s verified): qwen/qwen3.8-27b
    Lane 2 (OpenRouter,  ~54s  verified): best matching :free model
    Lane 3 (Gemini,      ~152s verified): gemini-3.8-flash

ask() returns "" if every lane fails/rate-limits - callers must treat that as
"cloud unavailable" and continue with local-only behavior. Keys come from .env.
"""

import os
import time

import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))

_GROQ_MODEL = "qwen/qwen3.8-27b"
_OR_MODEL = "nvidia/nemotron-3.5-lightning:free"   # verified live 2026-10-30
_GEMINI_MODEL = "gemini-3.8-flash"


class _LaneFailure(Exception):
    pass


def _groq(prompt, max_tokens, timeout):
    k = os.getenv("GROQ_API_KEY")
    if not k:
        raise _LaneFailure("no GROQ_API_KEY")
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {k}"},
        json={"model": _GROQ_MODEL,
              "messages": [{"role": "user", "content": prompt}],
              "max_tokens": max_tokens, "temperature": 0.2},
        timeout=timeout)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"]
    raise _LaneFailure(f"groq HTTP {r.status_code}")


def _openrouter(prompt, max_tokens, timeout):
    k = os.getenv("OPENROUTER_API_KEY")
    if not k:
        raise _LaneFailure("no OPENROUTER_API_KEY")
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {k}",
                 "HTTP-Referer": "https://apex.local",
                 "X-Title": "Apex Autonomous Agent"},
        json={"model": _OR_MODEL,
              "messages": [{"role": "user", "content": prompt}],
              "max_tokens": max_tokens},
        timeout=timeout)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"].get("content") or ""
    raise _LaneFailure(f"openrouter HTTP {r.status_code}")


def _gemini(prompt, max_tokens, timeout):
    k = os.getenv("GEMINI_API_KEY")
    if not k:
        raise _LaneFailure("no GEMINI_API_KEY")
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{_GEMINI_MODEL}:generateContent?key={k}",
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"maxOutputTokens": max_tokens}},
        timeout=timeout)
    if r.status_code == 200:
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    raise _LaneFailure(f"gemini HTTP {r.status_code}")


# (name, fn, timeout_seconds) - fastest verified lane first
LANES = [
    ("groq", _groq, 25),
    ("openrouter", _openrouter, 120),
    ("gemini", _gemini, 240),
]


def _adaptive_order(lane_list):
    """Reorder lanes by measured telemetry when enough samples exist.

    Reads the adapter's LaneStats.json (per-lane count/errors/avg_s written by
    every generation call). Lanes with higher error-rate or latency drift down.
    Falls back to static order silently whenever data is thin or unreadable -
    never a failure path, just a preference.
    """
    try:
        stats_path = os.path.join(os.path.dirname(R), "Apex-Adapter", "Config", "LaneStats.json")
        if not os.path.exists(stats_path):
            return lane_list
        with open(stats_path, "r", encoding="utf-8") as f:
            st = json.load(f)
        if not isinstance(st, dict):
            return lane_list
        scored = []
        for name, fn, budget in lane_list:
            e = st.get(name)
            if isinstance(e, dict) and int(e.get("count", 0)) >= 5:
                errors = int(e.get("errors", 0)) / max(1, int(e["count"]))
                scored.append((round(errors * 2 + float(e.get("avg_s", 0.0)), 3), name, fn, budget))
            else:
                scored.append((0.0, name, fn, budget))  # insufficient data = default priority
        scored.sort(key=lambda kv: kv[0])
        return [(n, f, b) for _, n, f, b in scored]
    except Exception:
        return lane_list


def ask(prompt, max_tokens=400, verbose=True):
    """Try each cloud lane fastest-first. Return text or '' if all fail."""
    for name, fn, budget in _adaptive_order(LANES):
        try:
            t0 = time.time()
            out = fn(prompt, max_tokens, budget)
            if out and out.strip():
                if verbose:
                    print(f"[CLOUD] lane={name} {time.time() - t0:.1f}s len={len(out)}")
                return out.strip()
        except _LaneFailure as e:
            if verbose:
                print(f"[CLOUD] lane {name} failed: {e}")
        except requests.RequestException as e:
            if verbose:
                print(f"[CLOUD] lane {name} error: {e}")
    return ""


if __name__ == "__main__":
    print("lane test ->", ask("Reply with exactly: APEX CLOUD FAILSAFE OK")[:100])
