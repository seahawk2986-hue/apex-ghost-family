"""ApexResearch - research-augmented prompting (retrieval-augmented coding).

Fetches short community snippets for a library the task mentions (DuckDuckGo
HTML, hard-bounded, cached), so the coder sees real-world usage before writing.
Everything is labeled UNVERIFIED reference notes - the sandbox still rules.
"""

import json
import os
import re
import time

import requests

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(R, "Config", "ResearchCache.json")


def _load_cache():
    try:
        with open(CACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(c):
    try:
        c = dict(list(c.items())[-20:])
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, "w", encoding="utf-8") as f:
            json.dump(c, f)
    except Exception:
        pass


def _snippets(html_text):
    raw = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html_text, re.DOTALL)[:4]
    out = []
    for s in raw:
        t = re.sub(r"<[^>]+>", "", s)
        t = t.replace("&quot;", '"').replace("&#x27;", "'").replace("&amp;", "&").strip()
        if len(t) > 40:
            out.append(t[:300])
    return out


def fetch(query, timeout_sec=8):
    """Returns a short reference-notes string, or '' (never raises)."""
    try:
        cache = _load_cache()
        if query in cache and time.time() - cache[query].get("ts", 0) < 7 * 86400:
            return cache[query].get("notes", "")
        r = requests.get("https://duckduckgo.com/html/", params={"q": query},
                         headers={"User-Agent": "Mozilla/5.0 (Apex research)"},
                         timeout=timeout_sec)
        if r.status_code != 200:
            return ""
        notes = "\n- ".join(_snippets(r.text))
        if not notes:
            return ""
        cache[query] = {"ts": time.time(), "notes": notes[:1500]}
        _save_cache(cache)
        return notes[:1500]
    except Exception:
        return ""


def library_from_task(task_text):
    m = re.search(r"\b(?:using|with)\s+([A-Za-z_][A-Za-z0-9_\.]{1,30})\b", task_text or "")
    return m.group(1) if m else None


if __name__ == "__main__":
    print(fetch("requests library python GET example")[:300])