"""PAPER HARVEST 7: 200 docs (2026) - the TECHNIQUES canon: the
proven-successful agent techniques per class:
  agent-security (the prompt-injection defense/sandbox), self-healing,
  graph-rag/knowledge, LLM-judge/evaluation, prompt-optimization,
  post-training (the RL from runlogs), tool/MCP standards, memory systems,
  multi-agent org, test-gen (property/mutation).
Dedupe vs all held (921). Writes Config/papers_2026_techniques.jsonl with
technique_class tags + the tools' ledger receipts."""
import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "papers_2026_techniques.jsonl")
NS = "{http://www.w3.org/2005/Atom}"
TARGET = 200
PRIORS = ["papers_2026", "papers_2026_evolution", "papers_2026_agents",
          "papers_2026_coding", "papers_2026_earning", "papers_2026_jobs"]
QUERIES = [
    'abs:"prompt injection" AND (abs:"defense" OR abs:"attack")',
    'abs:"agent" AND abs:"sandbox" AND abs:"security"',
    'abs:"self-healing" OR abs:"self-repair" AND abs:"agent"',
    '"graph RAG" OR "GraphRAG" OR (abs:"knowledge graph" AND abs:"retrieval")',
    'abs:"LLM judge" OR abs:"LLM-as-judge" OR (abs:"evaluation" AND abs:"LLM" AND abs:"rubric")',
    'abs:"prompt optimization" OR abs:"DSPy" OR abs:"prompt engineering automation"',
    'abs:"reinforcement learning" AND (abs:"agent" OR abs:"trajectories") AND abs:"log"',
    'abs:"model context protocol" OR abs:"MCP" OR (abs:"tool calling" AND abs:"standard")',
    'abs:"memory" AND abs:"agent" AND (abs:"long-term" OR abs:"reflection")',
    'abs:"role" AND abs:"multi-agent" AND (abs:"organization" OR abs:"collaboration")',
    'abs:"property-based testing" OR abs:"fuzzing" OR abs:"mutation testing"',
    'abs:"test generation" AND abs:"agent" AND abs:"unit"',
]
CLS = {
    "agent_security": re.compile(r"prompt injection|sandbox|injection attack|jailbreak", re.I),
    "self_healing": re.compile(r"self-heal|self-repair|recovery|regression self", re.I),
    "graph_rag": re.compile(r"graph rag|graphrag|knowledge graph", re.I),
    "llm_judge": re.compile(r"judge|rubric|evaluat", re.I),
    "prompt_opt": re.compile(r"prompt optim|dspy|prompt engineer", re.I),
    "post_training": re.compile(r"reinforcement|RL|trajectories", re.I),
    "tool_standards": re.compile(r"model context protocol|MCP|tool call", re.I),
    "memory_systems": re.compile(r"memory|reflection", re.I),
    "multi_agent_org": re.compile(r"multi-agent|role", re.I),
    "test_gen": re.compile(r"property-based|fuzz|mutation|test-generation|unit tests", re.I),
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
print(f"[harvest7] dedupe base: {len(have)} held")
pool = []
for qI, q in enumerate(QUERIES):
    if len(pool) >= TARGET:
        break
    for start in (0, 20, 40, 60, 80):
        if len(pool) >= TARGET:
            break
        url = ("https://export.arxiv.org/api/query?search_query=" +
               urllib.parse.quote(q) +
               f"&sortBy=submittedDate&sortOrder=descending&start={start}"
               f"&max_results=25")
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url, headers={"User-Agent": "apex-paper-harvest/7.0"}),
                    timeout=40) as r:
                root = ET.fromstring(r.read())
        except Exception as e:
            print(f"[harvest7] q{qI} p{start}: {str(e)[:50]}")
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
            kls = next((k for k, pat in CLS.items() if pat.search(hay)),
                       "general-technique")
            pool.append({"id": pid, "title": title, "published": date,
                         "technique_class": kls, "abstract": abst,
                         "source_url": "https://arxiv.org/abs/" + pid})
            have.add(pid)
            n += 1
            if len(pool) >= TARGET:
                break
        print(f"[harvest7] q{qI} p{start}: +{n} | pool {len(pool)}")
        time.sleep(3)
with open(OUT, "w", encoding="utf-8") as f:
    for r0 in pool[:TARGET]:
        f.write(json.dumps(r0) + "\n")
cls = {}
for r0 in pool:
    cls[r0["technique_class"]] = cls.get(r0["technique_class"], 0) + 1
with open(os.path.join(ROOT, "Config", "tools_used.jsonl"), "a",
          encoding="utf-8") as f:
    f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "run": "harvest7", "tool": "the technique-classes "
                        "classifier (12 queries x 10 classes)",
                        "purpose": "the techniques canon"}) + "\n")
print(f"[harvest7] COMPLETE: {min(len(pool), TARGET)} -> {OUT} | classes: {cls}")