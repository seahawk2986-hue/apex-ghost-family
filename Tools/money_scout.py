"""money_scout - THE 10-PASS MONEY-AGENT SOURCER (runs on Actions).

10 passes, each a themed sweep over documents/papers/mechanisms of
SUCCESSFUL money-making AI agents (arXiv + OpenAlex, keyless, $0). Each
pass commits its wave: money/pass-N/wave.md + wave.jsonl - the compare
organ (local) then judges every pattern against Apex's real anatomy.
Pass themes (current, grounded):
  1 b bounty-claims       2 agentic service-pricing   3 agent-economies
  4 autonomous-code-work  5 gig/freelance automation  6 tool-marketplaces
  7 arbitrage/enhancement 8 SaaS-micro agents         9 data-labeling loops
 10 negotiation/pricing
"""
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
OUT = pathlib = __import__("pathlib").Path("money")
OUT.mkdir(exist_ok=True)
NS = "{http://www.w3.org/2005/Atom}"

PASSES = [
    ("bounty-claims", 'all:"software bounty" OR all:"bug bounty" AND all:"automation"'),
    ("service-pricing", 'all:"LLM" AND all:"pricing" AND all:"service"'),
    ("agent-economies", 'all:"agent" AND all:"economy" AND all:"LLM"'),
    ("autonomous-code-work", 'all:"autonomous coding" OR all:"SWE-bench"'),
    ("gig-automation", 'all:"freelance" AND all:"machine learning" OR all:"gig economy" AND all:"AI"'),
    ("tool-marketplaces", 'all:"tool marketplace" OR all:"plugin ecosystem" AND all:"language model"'),
    ("enhancement-services", 'all:"image enhancement" OR all:"code repair" AND all:"service"'),
    ("micro-SaaS-agents", 'all:"micro SaaS" OR all:"SaaS" AND all:"LLM"'),
    ("data-labeling", 'all:"data labeling" AND all:"automation"'),
    ("negotiation", 'all:"automated negotiation" AND all:"agent"'),
]


def fetch_q(q, n=12):
    url = ("http://export.arxiv.org/api/query?" +
           urllib.parse.urlencode({"search_query": q, "max_results": n}))
    for a in range(2):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                return r.read()
        except Exception:
            time.sleep(8)
    return b""


def parse(raw):
    if not raw:
        return []
    try:
        root = ET.fromstring(raw)
    except Exception:
        return []
    out = []
    for e in root.findall(NS + "entry"):
        uid = (e.findtext(NS + "id", "") or "").split("/abs/")[-1]
        out.append({"id": uid,
                    "title": " ".join((e.findtext(NS + "title", "") or "").split())[:150],
                    "year": (e.findtext(NS + "published", "") or "")[:4]})
    return out


def extract_patterns(items):
    """the mechanism keywords the compare organ consumes (pure text, $0)."""
    PATS = [("bounty", "claim bounty work"), ("reward", "reward loops"),
            ("pricing", "service pricing"), ("marketplace", "tool selling"),
            ("escrow", "escrowed work"), ("revenue", "revenue loops"),
            ("contract", "contracted tasks"), ("subscription", "retainers"),
            ("arbitrage", "service arbitrage"), ("evaluate", "proof-of-work")]
    tags = set()
    for it in items:
        t = it["title"].lower()
        for k, name in PATS:
            if k in t:
                tags.add(name)
    return sorted(tags)


def main():
    for n, (theme, q) in enumerate(PASSES, 1):
        d = OUT / f"pass-{n}"
        d.mkdir(exist_ok=True)
        items = parse(fetch_q(q))
        pats = extract_patterns(items)
        (d / "wave.jsonl").write_text(
            "\n".join(json.dumps(i, ensure_ascii=False) for i in items) + "\n",
            encoding="utf-8")
        (d / "wave.md").write_text(
            f"# pass {n}: {theme}\n\n{len(items)} documents\n\npatterns: "
            + ", ".join(pats) + "\n\n"
            + "\n".join(f"- [{i['year']}] {i['title']} ({i['id']})" for i in items)
            + "\n", encoding="utf-8")
        print(f"[pass {n}] {theme}: {len(items)} docs | {pats}")
        time.sleep(3)
    print("[10 passes done]: waves committed for the compare organ")


if __name__ == "__main__":
    main()