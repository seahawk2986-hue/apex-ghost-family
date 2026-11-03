"""Round-3 sourcing: 100 papers on fleet SPEED/latency.

Families: continuous batching, speculative decoding, prefix-reuse,
prompt/output-length prediction, SLO serving, distillation-for-latency.
"""
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure") and not getattr(sys.stdout, "_apex_reconfigured", False):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout._apex_reconfigured = True   # reconfigure the EXISTING wrapper
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr._apex_reconfigured = True   # NEVER replace sys.stdout: the GC
                                           # closes the original = the shared buffer dies
OUT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\scores\papers_speed_100.json"
QUERIES = [
    'all:"continuous batching" AND all:"inference"',
    'all:"speculative decoding"',
    'all:"prefix reuse" AND all:"inference"',
    'all:"prompt compression" AND all:"latency"',
    'all:"output length prediction" AND all:"LLM"',
    'all:"latency" AND all:"small language model"',
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
        print("[ +" + str(len(allpapers)) + " ]", q[:64])
        time.sleep(3)
    except Exception as e:
        print("[query error]:", str(e)[:70])
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(allpapers, f, indent=1, ensure_ascii=False)
print("[sourced]:", len(allpapers), "->", OUT)
for p in allpapers:
    print("  ·", str(p["year"]) + " |", p["title"][:100])