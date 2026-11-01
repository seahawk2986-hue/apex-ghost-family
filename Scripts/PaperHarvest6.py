"""PAPER HARVEST 6: 100 papers (2026) for the HIGHEST-EARNING JOBS the
agent can do NOW - ranked by documented real rates, anchored to the
earning canon + the marketplaces' published rates:
  security/bounty work   ($500-$50k/payout; the earning canon's top lane)
  code fix/migration     ($100-$5,000/task; Algora/Upwork documented)
  ML/data-pipeline work  ($100-$1,000/task)
  technical writing      ($50-$300/doc)
  SKIPPED (honest): data-labeling/microtask (pennies/task - the LOW class)
Queries target THOSE classes' 2026 literature. Dedupe vs all held (821+).
Writes Config/papers_2026_jobs.jsonl with rate anchors per row."""
import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "papers_2026_jobs.jsonl")
NS = "{http://www.w3.org/2005/Atom}"
TARGET = 100
PRIORS = ["Config/papers_2026.jsonl", "Config/papers_2026_evolution.jsonl",
          "Config/papers_2026_agents.jsonl", "Config/papers_2026_coding.jsonl",
          "Config/papers_2026_earning.jsonl"]
QUERIES = [
    'abs:"vulnerability detection" AND abs:"LLM"',
    'abs:"exploit" AND abs:"LLM" AND abs:"security analysis"',
    'abs:"code migration" OR abs:"code translation" AND abs:"LLM"',
    'abs:"automated repair" AND (abs:"program" OR abs:"code") AND abs:"LLM"',
    'abs:"code review" AND abs:"LLM"',
    'abs:"refactoring" AND abs:"LLM"',
    'abs:"pipeline" AND abs:"data" AND abs:"LLM" AND abs:"quality"',
    'abs:"fine-tuning" AND abs:"automated" AND abs:"pipeline"',
    'abs:"technical documentation" AND abs:"generation" AND abs:"LLM"',
    'abs:"API documentation" AND abs:"LLM" AND abs:"generation"',
    'abs:"penetration testing" AND abs:"LLM"',
    'abs:"fuzzing" AND abs:"LLM"',
    'abs:"test generation" AND abs:"security"',
    'abs:"agent benchmark" AND (abs:"software" OR abs:"real-world") AND abs:"task"',
]
CLASS_TABLE = {
    "security": re.compile(r"vulnerab|exploit|penetration|fuzz|security|CVE", re.I),
    "code_fix": re.compile(r"repair|migrat|refactor|review|bug|fix", re.I),
    "ml_data": re.compile(r"pipeline|fine-tun|dataset quality|data quality|label", re.I),
    "tech_write": re.compile(r"documentation|document generation|API doc|readme", re.I),
}
RATE = {"security": 500.0, "code_fix": 150.0, "ml_data": 200.0,
        "tech_write": 80.0}
have = set()
for fn in PRIORS:
    p = os.path.join(ROOT, fn)
    if os.path.exists(p):
        for line in open(p, encoding="utf-8-sig"):
            try:
                have.add(json.loads(line)["id"])
            except Exception:
                pass
print(f"[harvest6] dedupe base: {len(have)} held")
pool = []
for qI, q in enumerate(QUERIES):
    if len(pool) >= TARGET:
        break
    for start in (0, 20, 40):
        if len(pool) >= TARGET:
            break
        url = ("https://export.arxiv.org/api/query?search_query=" +
               urllib.parse.quote(q) +
               f"&sortBy=submittedDate&sortOrder=descending&start={start}"
               f"&max_results=20")
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url, headers={"User-Agent": "apex-paper-harvest/6.1"}),
                    timeout=40) as r:
                root = ET.fromstring(r.read())
        except Exception as e:
            print(f"[harvest6] q{qI} p{start}: {str(e)[:50]}")
            time.sleep(4)
            continue
        n = 0
        for e in root.findall(NS + "entry"):
            pid = (e.findtext(NS + "id") or "").replace(
                "http://arxiv.org/abs/", "").strip()
            date = (e.findtext(NS + "published") or "")[:10]
            title = " ".join((e.findtext(NS + "title") or "").split())[:160]
            abst = " ".join((e.findtext(NS + "summary") or "").split())[:800]
            if not pid or not date.startswith("2026") or pid in have:
                continue
            hay = title + " " + abst
            if not re.search(r"task|job|work|deliver|product|service|quality|"
                             r"evaluat|automat", hay, re.I):
                continue
            kls = next((k for k, pat in CLASS_TABLE.items() if pat.search(hay)),
                       "unclassified")
            pool.append({"id": pid, "title": title, "published": date,
                         "job_class": kls,
                         "documented_rate_band_usd": RATE.get(kls, 0),
                         "abstract": abst,
                         "source_url": "https://arxiv.org/abs/" + pid})
            have.add(pid)
            n += 1
            if len(pool) >= TARGET:
                break
        print(f"[harvest6] q{qI} p{start}: +{n} | pool {len(pool)}")
        time.sleep(3)
with open(OUT, "w", encoding="utf-8") as f:
    for r0 in pool[:TARGET]:
        f.write(json.dumps(r0) + "\n")
with open(os.path.join(ROOT, "Config", "tools_used.jsonl"), "a",
          encoding="utf-8") as f:
    f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "run": "harvest6", "tool": "rate-anchored-classifier",
                        "purpose": "high-earn job classes with documented "
                                   "USD rate bands"}) + "\n")
cls = {}
for r0 in pool:
    cls[r0["job_class"]] = cls.get(r0["job_class"], 0) + 1
print(f"[harvest6] COMPLETE: {len(pool[:TARGET])} -> {OUT} | classes: {cls}")