"""PAPER HARVEST 5: 100 documented papers/docs (2026) on AI agents EARNING
REAL USD - the documented methods: bug-bounty/vulnerability-reward agents,
freelance-marketplace agents, algorithmic trading agents (SOURCED: the
method research; OUR rail law: trading = human-gated design-only),
e-commerce/content agents, agentic-economy simulations, gig automation,
agentic payments/commerce protocols. Dedupe vs all 721 held.
Writes Config/papers_2026_earning.jsonl + receipts the tools used."""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "papers_2026_earning.jsonl")
NS = "{http://www.w3.org/2005/Atom}"
TARGET = 100
PRIORS = ["Config/papers_2026.jsonl", "Config/papers_2026_evolution.jsonl",
          "Config/papers_2026_agents.jsonl", "Config/papers_2026_coding.jsonl"]
QUERIES = [
    'abs:"agent" AND (abs:"bounty" OR abs:"bug bounty")',
    'abs:"vulnerability" AND abs:"agent" AND abs:"LLM"',
    'abs:"freelance" OR abs:"gig economy" AND abs:"automation"',
    'abs:"trading agent" AND (abs:"LLM" OR abs:"language model")',
    'abs:"e-commerce agent" OR abs:"shopping agent" OR abs:"commerce agent"',
    'abs:"auction" OR abs:"market" AND abs:"LLM agent" AND abs:"revenue"',
    'abs:"agent" AND abs:"monetiz"',
    'abs:"agentic commerce" OR abs:"agentic payments" OR abs:"transactions agent"',
    'abs:"upwork" OR abs:"fiverr" OR abs:"freelancer" AND abs:"LLM"',
]
COIN = re.compile(r"\$|usd|usdc|revenue|monetiz|bounty|payment|earn|income|"
                  r"profit|payout|wage|price|value", re.I)
TOOL_LEDGER = os.path.join(ROOT, "Config", "tools_used.jsonl")

have = set()
for fn in PRIORS:
    p = os.path.join(ROOT, fn)
    if os.path.exists(p):
        for line in open(p, encoding="utf-8-sig"):
            try:
                have.add(json.loads(line)["id"])
            except Exception:
                pass
print(f"[harvest5] dedupe base: {len(have)} papers held")

def money_score(text):
    return len(COIN.findall(text or "")) / max(1, len(text or "")) * 1000

rows_written = 0
pool = []
mode = "a"
for qI, q in enumerate(QUERIES):
    if rows_written >= TARGET:
        break
    for start in (0, 20, 40, 60):
        if rows_written >= TARGET:
            break
        url = ("https://export.arxiv.org/api/query?search_query=" +
               urllib.parse.quote(q) +
               f"&sortBy=submittedDate&sortOrder=descending&start={start}"
               f"&max_results=25")
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url, headers={"User-Agent": "apex-paper-harvest/5.0"}),
                    timeout=40) as r:
                root = ET.fromstring(r.read())
        except Exception as e:
            print(f"[harvest5] q{qI} p{start}: {str(e)[:60]}")
            time.sleep(4)
            continue
        n_q = 0
        for e in root.findall(NS + "entry"):
            pid = (e.findtext(NS + "id") or "").replace(
                "http://arxiv.org/abs/", "").strip()
            date = (e.findtext(NS + "published") or "")[:10]
            title = " ".join((e.findtext(NS + "title") or "").split())[:160]
            abst = " ".join((e.findtext(NS + "summary") or "").split())[:800]
            cats = [c.get("term") for c in e.findall(NS + "category")][:3]
            if (not pid or not date.startswith("2026") or pid in have):
                continue
            if not COIN.search(title + " " + abst) and "econ" not in str(cats):
                continue
            row = {"id": pid, "title": title, "published": date,
                   "categories": cats, "abstract": abst,
                   "money_score": round(money_score(title + " " + abst), 2),
                   "source_url": "https://arxiv.org/abs/" + pid,
                   "lane_class": ("bounty" if re.search(r"bounty|vulnerab", title + abst, re.I)
                                  else "marketplace" if re.search(r"freelance|gig|upwork|fiverr", title + abst, re.I)
                                  else "trading" if re.search(r"trading|market|auction", title + abst, re.I)
                                  else "commerce" if re.search(r"commerce|shopping|payment", title + abst, re.I)
                                  else "economy-sim")}
            pool.append(row)
            have.add(pid)
            n_q += 1
            rows_written += 1
            if rows_written >= TARGET:
                break
        print(f"[harvest5] q{qI} p{start}: +{n_q} | total {rows_written} "
              f"(pool {len(pool)})")
        time.sleep(3)

pool.sort(key=lambda x: -x["money_score"])
with open(OUT, "w", encoding="utf-8") as f:
    for r0 in pool[:TARGET]:
        f.write(json.dumps(r0) + "\n")
with open(TOOL_LEDGER, "a", encoding="utf-8") as f:
    for tn, purpose in (("arxiv-export-api", "the earning-canon source "
                         "endpoint (9 money-class queries)"),
                        ("python-urllib+xml", "fetch + ATOM (stdlib)"),
                        ("money-recognizer", "the COIN regex ranks each "
                         "paper's money-documentation density"),
                        ("lane-classifier", "bounty/marketplace/trading/"
                         "commerce/economy-sim tags per row")):
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "run": "harvest5", "tool": tn,
                            "purpose": purpose}) + "\n")
vals = [json.loads(x) for x in open(OUT, encoding="utf-8-sig") if x.strip()]
lane_n = {}
for r0 in vals:
    lane_n[r0["lane_class"]] = lane_n.get(r0["lane_class"], 0) + 1
print(f"[harvest5] COMPLETE: {len(vals)} rows -> {OUT} | lanes: {lane_n}")
for r0 in vals[:5]:
    print(f"   {r0['id']:16s} [{r0['lane_class']:12s}] {r0['title'][:70]}")