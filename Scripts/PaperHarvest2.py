"""PAPER HARVEST 2: 100 EVOLUTION-focused 2026 papers (the full year).
Queries target evolution-of-agents canon: self-improving, evolutionary,
quality-diversity, open-ended, Darwin-class, auto-curriculum, mutation.
Paged (start 0/20/40/60), sorted newest-first, filtered published-2026,
deduped across harvests (reads papers_2026.jsonl's existing set as prior),
writes Config/papers_2026_evolution.jsonl until TARGET met. Politeness 3s."""
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "papers_2026_evolution.jsonl")
PRIOR = os.path.join(ROOT, "Config", "papers_2026.jsonl")
NS = "{http://www.w3.org/2005/Atom}"
QUERIES = [
    'all:"self-improving agent"',
    'all:"self-evolving" AND (cat:cs.AI OR cat:cs.MA OR cat:cs.SE)',
    'all:"quality diversity"',
    'all:"open-ended learning"',
    'abs:"evolutionary" AND (all:"agent" OR all:"prompt")',
    'all:"Godel machine" OR all:"darwin" AND cat:cs.AI',
    'abs:"automatic curriculum"',
    'all:"mutation" AND all:"LLM"',
]
TARGET = 100

have = set()
for src in (PRIOR, OUT):
    if os.path.exists(src):
        for line in open(src, encoding="utf-8-sig"):
            try:
                have.add(json.loads(line)["id"])
            except Exception:
                pass
prior_count = len(have)
print(f"[harvest2] prior known: {prior_count}; harvesting EVOLUTION-focused 2026 -> {TARGET}")

rows_written = 0
mode = "w"
for qI, q in enumerate(QUERIES):
    if rows_written >= TARGET:
        break
    for start in (0, 20, 40, 60):
        if rows_written >= TARGET:
            break
        url = ("https://export.arxiv.org/api/query?search_query=" +
               urllib.parse.quote(q) +
               f"&sortBy=submittedDate&sortOrder=descending&start={start}&max_results=20")
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url, headers={"User-Agent": "apex-paper-harvest/2.0"}), timeout=40) as r:
                root = ET.fromstring(r.read())
        except Exception as e:
            print(f"[harvest2] q{qI} p{start}: {str(e)[:60]}")
            time.sleep(4)
            continue
        n_q = 0
        for e in root.findall(NS + "entry"):
            pid = (e.findtext(NS + "id") or "").replace("http://arxiv.org/abs/", "").strip()
            date = (e.findtext(NS + "published") or "")[:10]
            if not pid or not date.startswith("2026") or pid in have:
                continue
            title = " ".join((e.findtext(NS + "title") or "").split())[:150]
            abst = " ".join((e.findtext(NS + "summary") or "").split())[:400]
            cats = [c.get("term") for c in e.findall(NS + "category")][:3]
            with open(OUT, mode, encoding="utf-8") as f:
                f.write(json.dumps({"id": pid, "title": title, "published": date,
                                    "categories": cats, "abstract": abst}) + "\n")
            have.add(pid)
            n_q += 1
            mode = "a"
            if rows_written >= TARGET:
                break
        print(f"[harvest2] q{qI} p{start}: +{n_q} | total evolution-ledger {rows_written}")
        time.sleep(3)

print()
print(f"[harvest2] COMPLETE: {rows_written} NEW evolution-focused 2026 papers "
      f"({prior_count} prior + {rows_written} = {prior_count + rows_written} total canon)")
i = 0
for line in open(OUT, encoding="utf-8-sig"):
    r0 = json.loads(line)
    i += 1
    if i <= 6 or i in (30, 60, i >= 98 and i <= 100):
        print(f"   {i:3d}. {r0['id']:16s} {r0['title'][:88]}")