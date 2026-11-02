"""THE 200-PAPER GI-CANON (the current-first: the top-AI-companies' general-
intelligence research, sorted newest-first, deduped to 200). Free arXiv API,
12 targeted queries x 25, submittedDate-desc. Output: Config/GIPapers200.jsonl
+ a digest. $0. Bounded ~1 minute."""
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "GIPapers200.jsonl")

QUERIES = [
    ("tool-use", 'all:"agentic tool use" OR all:"tool learning" AND all:"agents"'),
    ("function-calling", 'all:"function calling" AND cat:cs.CL'),
    ("llm-agents", 'all:"large language model agents"'),
    ("test-time-compute", 'all:"test-time compute"'),
    ("self-correction", 'all:"self-correction" AND cat:cs.CL'),
    ("rl-agents", 'all:"reinforcement learning" AND all:"tool call" AND cat:cs.LG'),
    ("agentic-memory", 'all:"memory" AND all:"LLM agents" AND cat:cs.CL'),
    ("streaming-asr", 'cat:eess.AS AND all:"streaming" AND all:"speech recognition"'),
    ("long-horizon", 'all:"long horizon" AND all:"agents" AND cat:cs.CL'),
    ("self-consistency", 'all:"self-consistency" AND cat:cs.CL'),
    ("general-intelligence", 'all:"general intelligence" AND (cat:cs.AI OR cat:cs.CL)'),
    ("gi-benchmarks", 'all:"AGI" AND all:"benchmark" AND cat:cs.AI'),
]
NS = "{http://www.w3.org/2005/Atom}"
papers = {}
for tag, q in QUERIES:
    try:
        url = ("https://export.arxiv.org/api/query?search_query="
               + urllib.parse.quote(q)
               + "&start=0&max_results=25&sortBy=submittedDate&sortOrder=descending")
        with urllib.request.urlopen(url, timeout=30) as r:
            root = ET.fromstring(r.read().decode("utf-8", "replace"))
        got = 0
        for e in root.iter(NS + "entry"):
            aid = (e.findtext(NS + "id") or "").split("/abs/")[-1]
            if not aid or aid in papers:
                continue
            title = " ".join((e.findtext(NS + "title") or "").split())
            year = (e.findtext(NS + "published") or "")[:10]
            if year < "2025":        # the CURRENT-first law
                continue
            authors = [(a.findtext(NS + "name") or "")
                       for a in e.iter(NS + "author")]
            coms = ",".join(a for a in authors
                            if any(dom in a for dom in
                                   ("OpenAI", "Anthropic", "DeepMind", "Google",
                                    "Meta", "Microsoft", "NVIDIA", "Alibaba",
                                    "Tencent", "DeepSeek", "Qwen", "Mistral",
                                    "xAI", "Meta AI", "Apple")))
            papers[aid] = {"id": aid, "title": title[:150], "year": year,
                           "tag": tag,
                           "authors": ", ".join(authors[:3])
                                      + (" et al." if len(authors) > 3 else ""),
                           "industry": coms[:120] or "(academia/other)"}
            got += 1
        print(f"[{tag}]: +{got}")
    except Exception as ex:
        print(f"[{tag}] error: {str(ex)[:70]}")
    time.sleep(3)

rows = sorted(papers.values(), key=lambda p: -int(p["year"].replace("-", "")))[:200]
with open(OUT, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"\n[GI-canon]: {len(rows)} papers (newest-first) -> {OUT}")
by = {}
for r in rows:
    by[r["tag"]] = by.get(r["tag"], 0) + 1
print("[by tag]:", json.dumps(by))