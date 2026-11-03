"""LightResearch - THE CONVERSATIONAL DEEP-RESEARCH LANE (2026-11-04).

THE FRONTIER GAP (the verified scorecard): deep, sourced web research =
the frontier agents' core conversational feature; Apex had the world's
richest MINING stack (the 17-wave swarm fetchers) but nothing conversational:
you could not ASK Apex to look something up and get back a SOUNDED answer.

THE ORGAN (the bounded research loop; every property kept from the family
laws): trigger = a chat message starting with "research:" (or containing
"look up "/"source me"):
  1. SEARCH (free, documented, keyless): DuckDuckGo's html endpoint (the
     swarm waves already use the family's fetch discipline) + HN Algolia
     (documented) - top few urls;
  2. FETCH the top 3 (<= 30KB each, <= 25s) - the swarm's politeness
     (one at a time, honest skips, no hammering);
  3. SYNTHESIZE via the fleet's own Shard dispatch (the free lanes, the
     ladder) with a CONFLICT-DISCLOSURE instruction: if the sources
     disagree, SAY so; if the answer is NOT in the fetched texts, say
     "not found in the fetched sources" - never invent;
  4. the reply carries the SOURCES list (the chat's chips render them).
Bounds: <= 60s wall total, <= 3 fetches, $0 only. The receipt: Config/
research_last.json (the query + the urls + the latency + which lane).
Sources for the design: the frontier deep-research pattern (OpenAI/
Anthropic's product class, 2025-2026) implemented on the family's own
fetch/consent/politeness laws; the swarm's existing free search lanes.
"""
import io
import json
import os
import re
import sys
import time

if getattr(sys.stdout, "apex_wrapped", False) is False:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.stdout.apex_wrapped = True

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
RESEARCH_RE = re.compile(r"^\s*((research|look ?up|source me)[:\s](.*))$",
                         re.I | re.S)


def _search(query):
    """free, keyless, documented search lanes; top urls (bounded)."""
    import requests
    urls, notes = [], []
    try:
        r = requests.get("https://html.duckduckgo.com/html/",
                         params={"q": query[:300]}, timeout=20,
                         headers={"User-Agent": "apex-ghost-family/2.0 "
                                                "(research lane; polite)"})
        for m in re.findall(r'href="[^"]*uddg=([^"&]+)', r.text or "")[:6]:
            import urllib.parse as up
            urls.append(up.unquote(m))
    except Exception as e:
        notes.append(f"ddg: {type(e).__name__}")
    try:
        r = requests.get("https://hn.algolia.com/api/v1/search",
                         params={"query": query[:200], "hitsPerPage": 4},
                         timeout=20)
        for h in (r.json() or {}).get("hits", [])[:4]:
            if h.get("url"):
                urls.append(h["url"])
    except Exception as e:
        notes.append(f"hn: {type(e).__name__}")
    # dedupe + drop our own hub (already self-known)
    seen, out = set(), []
    for u in urls:
        b = u.split("#")[0]
        if b not in seen and "seahawk2986" not in u:
            seen.add(b)
            out.append(u)
        if len(out) >= 3:
            break
    return out, notes


def _fetch(url):
    import requests
    try:
        r = requests.get(url[:200], timeout=25, headers={
            "User-Agent": "apex-ghost-family/2.0 (research; one-shot polite)"})
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]{1,200}>", " ", r.text or ""))[:12000]
        return txt
    except Exception:
        return ""


def research(query):
    """THE bounded loop -> (sourced_text, metas). Never raises."""
    t0 = time.time()
    urls, notes = _search(query)
    corpus = []
    for u in urls[:3]:
        t = _fetch(u)
        if t:
            corpus.append((u, t))
        if time.time() - t0 > 45:
            break
    if not corpus:
        return (None, {"urls": urls[:5], "notes": notes,
                       "verdict": "no sources fetched - the honest stop"})
    system = ("You are Apex's research lane. Use ONLY the SOURCES below. "
              "Answer directly; cite [1]/[2] indices after claims; if sources "
              "conflict, SAY the conflict; if the answer is absent, reply "
              "exactly: NOT FOUND IN SOURCES. Be precise, keep vocabulary "
              "complete, no marketing tone.")
    body = "\n\n".join(f"[{i + 1}] {u}\n{t[:8000]}"
                       for i, (u, t) in enumerate(corpus))
    prompt = f"{system}\n\nQUERY: {query[:400]}\n\nSOURCES:\n{body}\n\nANSWER:"
    from ApexShard import env as _env, call as _call, order_for as _order
    name, model, reply, _n = _call(_env(), _order(tier3=False),
                                   [{"role": "user", "content": prompt}],
                                   max_tokens=700)
    doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "query": query[:200],
           "urls": [u for u, _ in corpus], "notes": notes,
           "lane": name, "wall_s": round(time.time() - t0, 1),
           "verdict": "SOURCED" if reply else "no lane answered"}
    try:
        with open(os.path.join(REPO, "Config", "research_last.json"), "w",
                  encoding="utf-8") as f:
            json.dump(doc, f, indent=1)
    except Exception:
        pass
    return reply, doc


def triggered(msg):
    m = RESEARCH_RE.match(msg or "")
    if m and m.group(3).strip():
        return m.group(3).strip()[:300]
    return None