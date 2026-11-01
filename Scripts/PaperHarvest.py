"""PAPER HARVEST: the 2026 canon - 100 verified papers, systematically.
Method: arXiv API (export.arxiv.org), six domain queries from the family's
own lanes (multi-agent, LLM agents, agentic SE, LLM serving, swarms,
evolutionary), each PAGED by start-offset; every entry parsed from the live
Atom XML; filter: published date must start '2026-'; dedupe by arXiv id;
append rows {id, title, published, categories, abstract[:300]} to
Config/papers_2026.jsonl until 100 unique 2026 papers are ledgered.
Politeness: 3 s between queries; UA honest; bounded."""
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

OUT = os.path.join(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Config",
                   "papers_2026.jsonl")
NS = "{http://www.w3.org/2005/Atom}"
QUERIES = [
    'cat:cs.MA AND all:"multi-agent"',
    'cat:cs.AI AND all:"LLM agents"',
    'cat:cs.SE AND (all:"agentic" OR all:"software agent")',
    'cat:cs.DC AND all:"LLM serving"',
    '(all:"swarm" OR all:"evolutionary") AND cat:cs.AI',
    'cat:cs.CL AND (all:"multi-agent" OR all:"agentic")',
    'all:"agent" AND all:"self-improv"',
    'cat:cs.MA AND (all:"collaboration" OR all:"marketplace")',
]
TARGET = 100

have = set()
if os.path.exists(OUT):
    for line in open(OUT, encoding="utf-8-sig"):
        try:
            have.add(json.loads(line)["id"])
        except Exception:
            pass
written = 0
print(f"[harvest] already ledgered: {len(have)}; raising to {TARGET} (2026-only)")

mode = "a" if have else "w"
for qI, q in enumerate(QUERIES):
    if len(have) >= TARGET:
        break
    for start in (0, 20, 40):
        if len(have) >= TARGET:
            break
        url = ("https://export.arxiv.org/api/query?search_query=" +
               urllib.parse.quote(q) +
               f"&sortBy=submittedDate&sortOrder=descending&start={start}&max_results=20")
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url, headers={"User-Agent": "apex-paper-harvest/1.0"}), timeout=40) as r:
                xml = r.read()
            root = ET.fromstring(xml)
        except Exception as e:
            print(f"[harvest] query {qI} page {start}: {str(e)[:70]}")
            time.sleep(4)
            continue
        n_q = 0
        for e in root.findall(NS + "entry"):
            pid = (e.findtext(NS + "id") or "").replace("http://arxiv.org/abs/", "").strip()
            date = (e.findtext(NS + "published") or "")[:10]
            if not pid or not date.startswith("2026") or pid in have:
                continue
            title = " ".join((e.findtext(NS + "title") or "").split())[:140]
            abst = " ".join((e.findtext(NS + "summary") or "").split())[:300]
            cats = [c.get("term") for c in e.findall(NS + "category")][:3]
            with open(OUT, mode, encoding="utf-8") as f:
                f.write(json.dumps({"id": pid, "title": title, "published": date,
                                    "categories": cats, "abstract": abst}) + "\n")
            have.add(pid)
            n_q += 1
            mode = "a"
            if len(have) >= TARGET:
                break
        print(f"[harvest] q{qI} page{start}: +{n_q} (2026-only) | total {len(have)}")
        time.sleep(3)

print()
print(f"[harvest] LEDGER COMPLETE: {len(have)} unique 2026 papers -> {OUT}")
kinds = {}
for pid in list(have):
    pass
print("[harvest] sample titles:")
i = 0
for line in open(OUT, encoding="utf-8-sig"):
    r0 = json.loads(line)
    i += 1
    if i <= 8 or i in (40, 70, 100):
        print(f"   {i:3d}. {r0['id']:16s} {r0['title'][:90]}")
    if i >= TARGET:
        break