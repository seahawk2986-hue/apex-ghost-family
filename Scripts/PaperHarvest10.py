"""PAPER HARVEST 10: the 10/10-lane canon (target 200 docs) - the sourcing
directive's biggest sweep. Classes = the EXACT weak-lane map from the
capability rating: context_eng / long_horizon / llm_judge / self_healing /
injection / swe_agent / testing / coding_review / ecommerce_trust /
marketplace. Dedupe vs ALL held ledgers. Writes papers_2026_tech10.jsonl
(the TechniquesAdopter + SkillForge consume). Network-bound: ~30MB RAM."""
import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.environ.get("APEX_ROOT",
                      r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed")
OUT = os.path.join(ROOT, "Config", "papers_2026_tech10.jsonl")
NS = "{http://www.w3.org/2005/Atom}"
TARGET = 200
PRIORS = ["papers_2026", "papers_2026_evolution", "papers_2026_agents",
          "papers_2026_coding", "papers_2026_earning", "papers_2026_jobs",
          "papers_2026_techniques", "papers_2026_usdmaking",
          "papers_2026_marketing"]
AXLES = [
    ("context_eng", r"context window|in-context|retrieval|rag|context compression"),
    ("context_eng", 'abs:"retrieval augmented generation"'),
    ("context_eng", 'abs:"in-context learning" AND abs:"selection"'),
    ("long_horizon", 'abs:"long-horizon" AND abs:"agent"'),
    ("long_horizon", 'abs:"task decomposition" AND abs:"LLM"'),
    ("long_horizon", 'abs:"multi-agent" AND abs:"planning"'),
    ("llm_judge", 'abs:"LLM-as-a-judge"'),
    ("llm_judge", 'abs:"evaluating" AND abs:"language models" AND abs:"judge"'),
    ("llm_judge", 'abs:"automated" AND abs:"peer review" AND abs:"model"'),
    ("self_healing", 'abs:"automated program repair"'),
    ("self_healing", 'abs:"self-healing" AND abs:"software"'),
    ("injection", 'abs:"prompt injection"'),
    ("injection", 'abs:"LLM" AND abs:"adversarial" AND abs:"defense"'),
    ("swe_agent", 'abs:"SWE-bench"'),
    ("swe_agent", 'abs:"LLM" AND abs:"bug fixing"'),
    ("swe_agent", 'abs:"repository" AND abs:"patch" AND abs:"LLM"'),
    ("coding_review", 'abs:"code review" AND abs:"automated"'),
    ("coding_review", 'abs:"static analysis" AND abs:"LLM"'),
    ("testing", 'abs:"property-based testing"'),
    ("testing", 'abs:"metamorphic testing"'),
    ("ecommerce_trust", 'abs:"trust" AND abs:"e-commerce" AND abs:"study"'),
    ("ecommerce_trust", 'abs:"checkout" AND abs:"conversion"'),
]
have = set()
for fn in PRIORS:
    p = os.path.join(ROOT, "Config", fn + ".jsonl")
    if os.path.exists(p):
        for ln in open(p, encoding="utf-8-sig"):
            try:
                have.add(json.loads(ln)["id"])
            except Exception:
                pass
print(f"[harvest10] the dedupe base: {len(have)}")
pool = []
per = TARGET // max(1, len(AXLES))
for tag, q in AXLES:
    if len(pool) >= TARGET:
        break
    for start in (0, 15, 30):
        if len(pool) >= TARGET:
            break
        url = ("https://export.arxiv.org/api/query?search_query="
               + urllib.parse.quote(q) + f"&start={start}&max_results=18")
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url, headers={"User-Agent": "apex-harvest10/1.0"}),
                    timeout=40) as r:
                root = ET.fromstring(r.read())
        except Exception as e:
            print(f"[harvest10] {tag} p{start}: {str(e)[:50]}")
            time.sleep(4)
            continue
        n = 0
        for e in root.findall(NS + "entry"):
            pid = (e.findtext(NS + "id") or "").replace(
                "http://arxiv.org/abs/", "").strip()
            date = (e.findtext(NS + "published") or "")[:10]
            title = " ".join((e.findtext(NS + "title") or "").split())[:160]
            if not pid or not date.startswith("2026") or pid in have:
                continue
            pool.append({"id": pid, "title": title, "published": date,
                         "lane_class": tag, "abstract":
                         " ".join((e.findtext(NS + "summary") or "").split())
                         [:500], "source_url":
                         "https://arxiv.org/abs/" + pid})
            have.add(pid)
            n += 1
            if len(pool) >= TARGET:
                break
        print(f"[harvest10] {tag} p{start}: +{n} | pool {len(pool)}")
        time.sleep(3)
with open(OUT, "w", encoding="utf-8") as f:
    for r0 in pool[:TARGET]:
        f.write(json.dumps(r0) + "\n")
cls = {}
for r0 in pool:
    cls[r0["lane_class"]] = cls.get(r0["lane_class"], 0) + 1
print(f"[harvest10] COMPLETE: {len(pool[:TARGET])} -> {OUT} | {cls}")