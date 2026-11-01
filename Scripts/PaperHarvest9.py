"""PAPER HARVEST 9: 100 docs (2026) - the MARKETING/DISTRIBUTION canon
(the successful ways the software gets found): the OSS-adoption studies,
the network-effects, the community-led growth, the developer-marketing,
the SEO/discovery, the referral-mechanics, the social-platforms' spread
studies. Dedupe vs all held (1038). Writes papers_2026_marketing.jsonl
with growth_class tags (the TechniquesAdopter consumes)."""
import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "papers_2026_marketing.jsonl")
NS = "{http://www.w3.org/2005/Atom}"
TARGET = 100
PRIORS = ["papers_2026", "papers_2026_evolution", "papers_2026_agents",
          "papers_2026_coding", "papers_2026_earning", "papers_2026_jobs",
          "papers_2026_techniques", "papers_2026_usdmaking"]
QUERIES = [
    'abs:"open source" AND (abs:"adoption" OR abs:"growth") AND abs:"study"',
    'abs:"network effects" AND abs:"software"',
    'abs:"viral" AND (abs:"spread" OR abs:"marketing") AND abs:"software"',
    'abs:"developer" AND (abs:"marketing" OR abs:"relations") AND abs:"community"',
    'abs:"referral" AND (abs:"bonus" OR abs:"program") AND abs:"study"',
    'abs:"search engine optimization" AND abs:"content"',
    'abs:"community" AND abs:"open source" AND abs:"sustainability"',
    'abs:"reputation" AND abs:"developer" AND abs:"study"',
    'abs:"recommender" AND abs:"adoption" AND abs:"software products"',
    'abs:"creator economy" OR abs:"distribution channels"',
]
GROWTH = {
    "seo_discovery": re.compile(r"search|seo|discovery|recommend", re.I),
    "network_effects": re.compile(r"network effect|viral|spread|diffus", re.I),
    "community_growth": re.compile(r"community|contributor growth|sustainab", re.I),
    "reputation": re.compile(r"reputation|credib", re.I),
    "creator_economy": re.compile(r"creator|influencer|distribution channel", re.I),
    "general_growth": re.compile(r"adoption|marketing|growth", re.I),
}
have = set()
for fn in PRIORS:
    p = os.path.join(ROOT, "Config", fn + ".jsonl")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8-sig"):
            try:
                have.add(json.loads(line)["id"])
            except Exception:
                pass
print(f"[harvest9] the dedupe base: {len(have)}")
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
                    url, headers={"User-Agent": "apex-harvest9/1.0"}),
                    timeout=40) as r:
                root = ET.fromstring(r.read())
        except Exception as e:
            print(f"[harvest9] q{qI} p{start}: {str(e)[:50]}")
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
            kls = next((k for k, pat in GROWTH.items() if pat.search(hay)),
                       "general_growth")
            pool.append({"id": pid, "title": title, "published": date,
                         "growth_class": kls, "abstract": abst,
                         "source_url": "https://arxiv.org/abs/" + pid})
            have.add(pid)
            n += 1
            if len(pool) >= TARGET:
                break
        print(f"[harvest9] q{qI} p{start}: +{n} | pool {len(pool)}")
        time.sleep(3)
with open(OUT, "w", encoding="utf-8") as f:
    for r0 in pool[:TARGET]:
        f.write(json.dumps(r0) + "\n")
cls = {}
for r0 in pool:
    cls[r0["growth_class"]] = cls.get(r0["growth_class"], 0) + 1
print(f"[harvest9] COMPLETE: {min(len(pool), TARGET)} -> {OUT} | "
      f"classes: {cls}")