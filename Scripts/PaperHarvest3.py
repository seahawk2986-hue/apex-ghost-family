"""PAPER HARVEST 3: 100 new 2026 papers on the BEST-AGENT goal cluster.
The founder's new goals: coding mastery (as good as the best coding agents),
skill omnivory (learn every skill, find what is missing), efficient upward
evolution. Queries target the capability frontier: coding agents + benches,
skill acquisition/libraries, tool use mastery, agent memory, self-knowledge.
Dedupe against BOTH existing ledgers (100 + 421). Writes
Config/papers_2026_agents.jsonl until TARGET met. Politeness 3s."""
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "papers_2026_agents.jsonl")
PRIORS = [os.path.join(ROOT, "Config", "papers_2026.jsonl"),
          os.path.join(ROOT, "Config", "papers_2026_evolution.jsonl")]
NS = "{http://www.w3.org/2005/Atom}"
QUERIES = [
    'all:"coding agent" AND (cat:cs.SE OR cat:cs.AI OR cat:cs.PL)',
    'abs:"SWE-bench" OR abs:"software engineering agent"',
    'abs:"skill acquisition" AND all:"agent"',
    'all:"skill library" OR abs:"lifelong learning" AND cat:cs.AI',
    'abs:"tool use" AND (all:"LLM" OR all:"agent") AND all:"mastery"',
    'abs:"agent memory" OR abs:"procedural memory"',
    'abs:"code generation" AND abs:"agent" AND abs:"verification"',
    'abs:"self-knowledge" OR abs:"calibration" AND all:"agent" AND cat:cs.AI',
    'abs:"agentic coding" OR abs:"program synthesis agent"',
]
TARGET = 100

have = set()
for src in PRIORS:
    if os.path.exists(src):
        for line in open(src, encoding="utf-8-sig"):
            try:
                have.add(json.loads(line)["id"])
            except Exception:
                pass
prior_count = len(have)
print(f"[harvest3] dedupe base: {prior_count} known papers")

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
                    url, headers={"User-Agent": "apex-paper-harvest/3.0"}),
                    timeout=40) as r:
                root = ET.fromstring(r.read())
        except Exception as e:
            print(f"[harvest3] q{qI} p{start}: {str(e)[:60]}")
            time.sleep(4)
            continue
        n_q = 0
        for e in root.findall(NS + "entry"):
            pid = (e.findtext(NS + "id") or "").replace(
                "http://arxiv.org/abs/", "").strip()
            date = (e.findtext(NS + "published") or "")[:10]
            if not pid or not date.startswith("2026") or pid in have:
                continue
            title = " ".join((e.findtext(NS + "title") or "").split())[:150]
            abst = " ".join((e.findtext(NS + "summary") or "").split())[:400]
            cats = [c.get("term") for c in e.findall(NS + "category")][:3]
            with open(OUT, mode, encoding="utf-8") as f:
                f.write(json.dumps({"id": pid, "title": title,
                                    "published": date, "categories": cats,
                                    "abstract": abst}) + "\n")
            have.add(pid)
            n_q += 1
            rows_written += 1
            mode = "a"
            if rows_written >= TARGET:
                break
        print(f"[harvest3] q{qI} p{start}: +{n_q} | total {rows_written}")
        time.sleep(3)

print(f"[harvest3] COMPLETE: {rows_written} new papers -> {OUT}")
i = 0
for line in open(OUT, encoding="utf-8-sig"):
    r0 = json.loads(line)
    i += 1
    if i <= 5:
        print(f"   {i:3d}. {r0['id']:16s} {r0['title'][:80]}")