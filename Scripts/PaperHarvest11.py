"""PAPER HARVEST 11: the MODEL-USE canon (100 docs) - the documented
SUCCESS-ways of using models: small-models, distillation, ensembles/
debate, routing/cascades, quantization, edge-inference, speculative
decoding, MoE. TARGET 100, dedupe vs ALL held. WRITES the class-tags the
ModelSweep/CrossBrain consume. RUNS ON GITHUB'S MACHINES (the runner:
actions lane = the outsourcing-max!)."""
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.environ.get("APEX_ROOT", r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed")
OUT = os.path.join(ROOT, "Config", "papers_2026_modeluse.jsonl")
NS = "{http://www.w3.org/2005/Atom}"
TARGET = 100
PRIORS = ["papers_2026", "papers_2026_evolution", "papers_2026_agents",
          "papers_2026_coding", "papers_2026_earning", "papers_2026_jobs",
          "papers_2026_techniques", "papers_2026_usdmaking",
          "papers_2026_marketing", "papers_2026_tech10"]
AXLES = [
    ("small_models", 'abs:"small language models" AND abs:"study"'),
    ("small_models", 'abs:"distillation" AND abs:"language model"'),
    ("ensemble_debate", 'abs:"debate" AND abs:"language models"'),
    ("ensemble_debate", 'abs:"self-consistency" AND abs:"reasoning"'),
    ("routing_cascade", 'abs:"model cascade" OR abs:"LLM routing"'),
    ("routing_cascade", 'abs:"cost" AND abs:"quality" AND abs:"model selection"'),
    ("quantization", 'abs:"quantization" AND abs:"large language model"'),
    ("edge_inference", 'abs:"on-device" AND abs:"language model"'),
    ("spec_decoding", 'abs:"speculative decoding"'),
    ("moe", 'abs:"mixture of experts"'),
    ("tool_use", 'abs:"tool use" AND abs:"language model" AND abs:"agent"'),
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
print(f"[harvest11] the dedupe base: {len(have)}")
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
                    url, headers={"User-Agent": "apex-harvest11/1.0"}),
                    timeout=40) as r:
                root = ET.fromstring(r.read())
        except Exception as e:
            print(f"[harvest11] {tag} p{start}: {str(e)[:50]}")
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
        print(f"[harvest11] {tag} p{start}: +{n} | pool {len(pool)}")
        time.sleep(3)
with open(OUT, "w", encoding="utf-8") as f:
    for r0 in pool[:TARGET]:
        f.write(json.dumps(r0) + "\n")
cls = {}
for r0 in pool:
    cls[r0["lane_class"]] = cls.get(r0["lane_class"], 0) + 1
print(f"[harvest11] COMPLETE: {len(pool[:TARGET])} -> {OUT.split(os.sep)[-1]} | {cls}")