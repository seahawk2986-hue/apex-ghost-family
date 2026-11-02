"""100 papers: the K3-for-free method-space.

Families: open-weights economics, quantization-for-consumer-hardware,
free-inference platforms & credits, MoE serving at reduced RAM, trial
credits & education tiers, cloud-bursting, and capability-matching
(achieving frontier results on smaller free brains).
"""
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
OUT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\scores\papers_k3_free.json"
QUERIES = [
    'all:"open weights" AND all:"flagship"',
    'all:"quantization" AND all:"1TB" OR all:"MoE" AND all:"consumer GPU"',
    'all:"free tier" AND all:"API"',
    'all:"inference provider" AND all:"trial"',
    'all:"quantized MoE" AND all:"offload"',
    'all:"student license" OR all:"academic free" AND all:"API key"',
    'all:"distributed inference" AND all:"volunteer"',
    'all:"Kimi K3" OR all:"Moonshot AI"',
]

def fetch(q, n=16):
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
        got = fetch(q)
        for p in got:
            if p["url"] and p["url"] not in seen:
                seen.add(p["url"])
                allpapers.append(p)
        print("[ +" + str(len(allpapers)) + " ]", q[:64])
        time.sleep(3)
    except Exception as e:
        print("[query error]:", str(e)[:70])
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(allpapers, f, indent=1, ensure_ascii=False)
print("[sourced]:", len(allpapers), "papers ->", OUT)
for p in allpapers:
    print("  ·", str(p["year"]) + " |", p["title"][:100])