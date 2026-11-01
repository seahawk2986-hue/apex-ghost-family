"""PAPER HARVEST 8: the PROVEN-USD-MAKING canon (as many as needed):
 - micro-SaaS / indie-hacking economics (the products' playbooks)
 - API/MCP-as-a-product (the paid endpoints' economics)
 - dataset/data-products selling (the licensing' documented cases)
 - automation-monetization studies (the honest: the affiliate/ads classes'
   gray-zone = source-only, our ethics law: no black-hat)
 - the platforms' payout economics (the bounties' real escrow flows)
Dedupe vs all held; writes papers_2026_usdmaking.jsonl."""
import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "papers_2026_usdmaking.jsonl")
NS = "{http://www.w3.org/2005/Atom}"
TARGET = 80
PRIORS = ["papers_2026", "papers_2026_evolution", "papers_2026_agents",
          "papers_2026_coding", "papers_2026_earning", "papers_2026_jobs",
          "papers_2026_techniques"]
QUERIES = [
    'abs:"micro-SaaS" OR (abs:"indie" AND abs:"hacker") AND abs:"LLM"',
    'abs:"API" AND (abs:"monetization" OR abs:"as a service") AND abs:"LLM"',
    'abs:"dataset" AND (abs:"license" OR abs:"sell" OR abs:"marketplace") AND abs:"quality"',
    'abs:"agent" AND abs:"SaaS" AND abs:"revenue"',
    'abs:"side hustle" OR abs:"passive income" AND abs:"AI"',
    'abs:"sponsorship" AND (abs:"github" OR abs:"open source") AND abs:"income"',
    'abs:"pricing" AND (abs:"agents" OR abs:"API") AND abs:"study"',
]
MONEY = re.compile(r"\$|revenue|monetiz|income|price|sell|market|payout", re.I)
have = set()
for fn in PRIORS:
    p = os.path.join(ROOT, "Config", fn + ".jsonl")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8-sig"):
            try:
                have.add(json.loads(line)["id"])
            except Exception:
                pass
print(f"[harvest8] dedupe base: {len(have)} | the politeness: starts after "
      f"the queue (the 90s delay)")
time.sleep(90)   # the arXiv's politeness between the concurrent harvests
pool = []
for qI, q in enumerate(QUERIES):
    if len(pool) >= TARGET:
        break
    for start in (0, 20, 40):
        if len(pool) >= TARGET:
            break
        url = ("https://export.arxiv.org/api/query?search_query=" +
               urllib.parse.quote(q) + f"&start={start}&max_results=25")
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url, headers={"User-Agent": "apex-harvest8/1.0"}),
                    timeout=40) as r:
                root = ET.fromstring(r.read())
        except Exception as e:
            print(f"[harvest8] q{qI} p{start}: {str(e)[:50]}")
            time.sleep(4)
            continue
        n = 0
        for e in root.findall(NS + "entry"):
            pid = (e.findtext(NS + "id") or "").replace(
                "http://arxiv.org/abs/", "").strip()
            date = (e.findtext(NS + "published") or "")[:10]
            title = " ".join((e.findtext(NS + "title") or "").split())[:160]
            abst = " ".join((e.findtext(NS + "summary") or "").split())[:600]
            if not pid or not date.startswith("2026") or pid in have:
                continue
            hay = title + " " + abst
            if not MONEY.search(hay):
                continue
            pool.append({"id": pid, "title": title, "published": date,
                         "class": ("saas" if re.search(r"saas|indie|side|hustle", hay, re.I)
                                   else "api-product" if re.search(r"api", hay, re.I)
                                   else "data-product" if re.search(r"dataset|data", hay, re.I)
                                   else "platform-economics"),
                         "abstract": abst,
                         "source_url": "https://arxiv.org/abs/" + pid})
            have.add(pid)
            n += 1
            if len(pool) >= TARGET:
                break
        print(f"[harvest8] q{qI} p{start}: +{n} | pool {len(pool)}")
        time.sleep(3)
with open(OUT, "w", encoding="utf-8") as f:
    for r0 in pool[:TARGET]:
        f.write(json.dumps(r0) + "\n")
cls = {}
for r0 in pool:
    cls[r0["class"]] = cls.get(r0["class"], 0) + 1
print(f"[harvest8] COMPLETE: {min(len(pool), TARGET)} -> {OUT} | classes: {cls}")