"""The 50-paper reference pass: the traffic/efficiency method-space, keyless.

Queries arXiv across the four families our strategy touches (pacing,
caching, cascading/routing, load-shedding), stores the raw records, and
distills the recurring PROVEN patterns for the compare-vs-Apex table.
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
OUT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\scores\papers_traffic_50.json"
QUERIES = [
    'all:"large language model" AND all:"rate limit"',
    'all:"prompt caching" OR all:"semantic cache" AND cat:cs.CL',
    'all:"LLM routing" OR all:"model cascade"',
    'all:"inference scheduling" AND cat:cs.DC',
    'all:"load shedding" AND all:"inference"',
]

def fetch(q, n=12):
    url = ("https://export.arxiv.org/api/query?search_query="
           + urllib.parse.quote(q) + "&max_results=" + str(n)
           + "&sortBy=relevance")
    with urllib.request.urlopen(url, timeout=45) as r:
        xml = r.read().decode("utf-8", errors="replace")
    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.S)
    out = []
    for e in entries:
        title = re.search(r"<title>(.*?)</title>", e, re.S)
        link = re.search(r"<id>(.*?)</id>", e)
        date = re.search(r"<published>(\d{4})-", e)
        out.append({"title": re.sub(r"\s+", " ", (title.group(1) if title else "").strip()),
                    "url": link.group(1) if link else "", "year": date.group(1) if date else ""})
    return out

allpapers, seen = [], set()
for q in QUERIES:
    try:
        for p in fetch(q):
            if p["url"] and p["url"] not in seen:
                seen.add(p["url"])
                allpapers.append(p)
        time.sleep(3)   # arXiv politeness
    except Exception as e:
        print("[query error]:", str(e)[:70])
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(allpapers, f, indent=1, ensure_ascii=False)
print("[sourced]:", len(allpapers), "papers -> scores/papers_traffic_50.json")
for p in allpapers[:40]:
    print("  ·", str(p["year"]) + " |", p["title"][:96])