"""PAPER HARVEST 12: the CHAT-MODEL canon (100 docs, the latest ways):
the instruction-tuning/alignment, RLHF/DPO, the chat-quality evals, the
persona/honesty calibration, the conversational-agent studies, the
small-chat-model work. Dedupe vs ALL held. (The env-rooted runner.)"""
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.environ.get("APEX_ROOT",
                      r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed")
OUT = os.path.join(ROOT, "Config", "papers_2026_chatmodels.jsonl")
NS = "{http://www.w3.org/2005/Atom}"
TARGET = 100
PRIORS = ["papers_2026", "papers_2026_evolution", "papers_2026_agents",
          "papers_2026_coding", "papers_2026_earning", "papers_2026_jobs",
          "papers_2026_techniques", "papers_2026_usdmaking",
          "papers_2026_marketing", "papers_2026_tech10",
          "papers_2026_modeluse"]
AXLES = [
    ("instruction_tuning", 'abs:"instruction tuning"'),
    ("alignment", 'abs:"RLHF" OR abs:"direct preference optimization"'),
    ("chat_quality", 'abs:"chatbot" AND abs:"evaluation" AND abs:"study"'),
    ("chat_quality", 'abs:"conversational" AND abs:"benchmark" AND abs:"LLM"'),
    ("honesty_persona", 'abs:"honesty" AND abs:"large language model"'),
    ("honesty_persona", 'abs:"calibration" AND abs:"LLM" AND abs:"truthful"'),
    ("small_chat", 'abs:"edge" AND abs:"dialogue" AND abs:"model"'),
    ("safety", 'abs:"safety" AND abs:"chat" AND abs:"language model"'),
    ("serving", 'abs:"inference serving" AND abs:"LLM"'),
    ("prompting", 'abs:"prompt" AND abs:"conversational agent"'),
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
print(f"[harvest12] the dedupe base: {len(have)}")
pool = []
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
                    url, headers={"User-Agent": "apex-harvest12/1.0"}),
                    timeout=40) as r:
                root = ET.fromstring(r.read())
        except Exception as e:
            print(f"[harvest12] {tag} p{start}: {str(e)[:50]}")
            time.sleep(4)
            continue
        n = 0
        for e in root.findall(NS + "entry"):
            pid = (e.findtext(NS + "id") or "").replace(
                "http://arxiv.org/abs/", "").strip()
            date = (e.findtext(NS + "published") or "")[:10]
            if not pid or not date.startswith("2026") or pid in have:
                continue
            pool.append({"id": pid, "title": " ".join((
                e.findtext(NS + "title") or "").split())[:150],
                "published": date, "lane_class": tag,
                "abstract": " ".join((e.findtext(NS + "summary") or "")
                                     .split())[:450],
                "source_url": "https://arxiv.org/abs/" + pid})
            have.add(pid)
            n += 1
            if len(pool) >= TARGET:
                break
        print(f"[harvest12] {tag} p{start}: +{n} | pool {len(pool)}")
        time.sleep(3)
with open(OUT, "w", encoding="utf-8") as f:
    for r0 in pool[:TARGET]:
        f.write(json.dumps(r0) + "\n")
cls = {}
for r0 in pool:
    cls[r0["lane_class"]] = cls.get(r0["lane_class"], 0) + 1
print(f"[harvest12] COMPLETE: {len(pool[:TARGET])} | {cls}")