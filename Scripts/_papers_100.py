"""Round-2 sourcing: 100 papers on keeping a free-tier fleet rock-solid.

Six families: (1) caching/serving, (2) routing/cascades, (3) pacing/backoff,
(4) retries/reliability, (5) batching/scheduling, (6) distillation-to-small
(the local-first lever). arXiv keyless, politeness-gapped, dedup by id.
"""
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
OUT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\scores\papers_fleet_100.json"
QUERIES = [
    'all:"LLM inference" AND all:"cache"',
    'all:"model routing" AND cat:cs.CL',
    'all:"retry" AND all:"exponential backoff"',
    'all:"batch inference" AND all:"scheduling"',
    'all:"small language model" AND all:"distillation"',
    'all:"LLM serving" AND all:"overload"',
]

def fetch(q, n=20):
    url = ("https://export.arxiv.org/api/query?search_query="
           + urllib.parse.quote(q) + "&max_results=" + str(n)
           + "&sortBy=relevance")
    with urllib.request.urlopen(url, timeout=45) as r:
        xml = r.read().decode("utf-8", errors="replace")
    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        t = re.search(r"<title>(.*?)</title>", e, re.S)
        i = re.search(r"<id>(.*?)</id>", e)
        y = re.search(r"<published>(\d{4})-", e)
        out.append({"title": re.sub(r"\s+", " ", (t.group(1) if t else "").strip()),
                    "url": i.group(1) if i else "", "year": y.group(1) if y else ""})
    return out

allpapers, seen = [], set()
for q in QUERIES:
    try:
        for p in fetch(q):
            if p["url"] and p["url"] not in seen:
                seen.add(p["url"])
                allpapers.append(p)
        print("[ +" + str(len(allpapers)) + " ] ", q[:60])
        time.sleep(3)
    except Exception as e:
        print("[query error]:", str(e)[:70])
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(allpapers, f, indent=1, ensure_ascii=False)
print("[sourced]:", len(allpapers), "papers ->", OUT)
for p in allpapers:
    print("  ·", str(p["year"]) + " |", p["title"][:100])