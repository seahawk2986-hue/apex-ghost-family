"""papers-100 - THE OUTSOURCE SCOUT (runs on GitHub Actions runners).

Compiles 100 papers (arXiv API + OpenAlex fill, both keyless and $0)
documenting how people integrate the strongest available models into real
systems, tagged by integration mechanism. Writes:
  papers/papers.jsonl  - the register (one paper per line)
  papers/README.md     - the themed summary
Local never runs the full harvest (outsourcing law); the smoke test caps
at 2 API calls. Politeness: >=3s between arXiv calls (their docs).
"""
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

OUT = pathlib.Path("papers")
OUT.mkdir(exist_ok=True)
NS = {"a": "{http://www.w3.org/2005/Atom}"}
ARXIV = "http://export.arxiv.org/api/query"
MAX_CALLS = 2 if "--smoke" in sys.argv else 60
TARGET = 100

# (theme, relevance query, recency query)
THEMES = [
    ("frontier-API agents", 'all:"GPT-4" AND all:"agent"', 'all:"frontier model" AND all:"agent"'),
    ("tool-use & function-calling", 'all:"function calling" AND all:"large language model"', 'all:"tool use" AND all:"language models"'),
    ("retrieval-augmented (RAG)", 'all:"retrieval-augmented generation"', 'all:"RAG" AND all:"language model"'),
    ("routing & cascades", 'all:"routing" AND all:"large language models"', 'all:"model cascade" AND all:"cost"'),
    ("multi-agent systems", 'all:"multi-agent" AND all:"large language model"', 'all:"LLM agents" AND all:"cooperation"'),
    ("code & SWE agents", 'all:"software engineering" AND all:"large language model"', 'all:"coding agent"'),
    ("evaluation & judge", 'all:"LLM-as-a-judge"', 'all:"evaluation" AND all:"language model agents"'),
    ("serving & inference infra", 'all:"inference serving" AND all:"language model"', 'all:"LLM serving"'),
    ("memory & context", 'all:"memory" AND all:"language model agents"', 'all:"context window" AND all:"efficiency"'),
    ("MCP & protocols", 'all:"model context protocol"', 'all:"tool protocol" AND all:"language model"'),
    ("adaptation (FT/LoRA)", 'all:"LoRA" AND all:"language model"', 'all:"fine-tuning" AND all:"language model"'),
    ("security of integrated LLMs", 'all:"prompt injection"', 'all:"jailbreak" AND all:"language model"'),
]

TAGS = [
    (("tool call", "function call", "tool use"), "tool-calling"),
    (("retrieval", "rag"), "retrieval-augmented"),
    (("cascade", "rout", "frugal"), "routing/cascade"),
    (("multi-agent", "multi agent"), "multi-agent"),
    (("code generation", "software engineering", "repo", "program synthesis"), "code-execution"),
    (("judge", "evaluat", "benchmark"), "evaluation/judge"),
    (("serving", "inference engine", "vllm", "kv cache"), "serving-infra"),
    (("fine-tun", "lora", "adapt"), "adaptation"),
    (("injection", "jailbreak", "secur"), "security"),
    (("memory", "context"), "memory/context"),
]


def fetch(url, tries=3):
    for a in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return r.read()
        except Exception:
            time.sleep(10 * (a + 1))   # the 429-cure: polite backoff 10/20/30s
    return b""


def arxiv_query(q, n, sort="relevance"):
    url = ARXIV + "?" + urllib.parse.urlencode(
        {"search_query": q, "max_results": n, "sortBy": sort})
    raw = fetch(url)
    if not raw:
        return []
    out = []
    try:
        root = ET.fromstring(raw)
    except Exception:
        return []
    for e in root.findall("a:entry", NS):
        uid = (e.findtext("a:id", "", NS) or "").split("/abs/")[-1]
        title = " ".join((e.findtext("a:title", "", NS) or "").split())
        abstract = " ".join((e.findtext("a:summary", "", NS) or "").split())
        authors = [a_.findtext("a:name", "", NS) for a_ in e.findall("a:author", NS)]
        pub = (e.findtext("a:published", "", NS) or "")[:10]
        out.append({"arxiv_id": uid, "title": title, "abstract": abstract[:600],
                    "authors": [a2 for a2 in authors if a2][:4],
                    "published": pub})
    return out


def tag_paper(p):
    text = (p["title"] + " " + p["abstract"]).lower()
    tags = sorted({name for pats, name in TAGS if any(k in text for k in pats)})
    return tags or ["general-integration"]


def openalex_fill(need):
    got = []
    for q in ("large language model tool use agent",
              "language model retrieval augmented generation system",
              "LLM cascade routing efficient"):
        url = ("https://api.openalex.org/works?per-page=25&search="
               + urllib.parse.quote(q))
        raw = fetch(url)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        for w in data.get("results", []):
            got.append({"arxiv_id": "OA:" + str(w.get("id", "")).rsplit("/", 1)[-1],
                        "title": w.get("display_name", "")[:160],
                        "abstract": "", "authors": [],
                        "published": str(w.get("publication_date", ""))[:10]})
            if len(got) >= need:
                return got
    return got


def main():
    calls, reg, seen = 0, [], set()
    for theme, q_rel, q_new in THEMES:
        for q, sort in ((q_rel, "relevance"), (q_new, "submittedDate")):
            if calls >= MAX_CALLS:
                break
            for p in arxiv_query(q, 12, sort):
                if p["arxiv_id"] and p["arxiv_id"] not in seen:
                    seen.add(p["arxiv_id"])
                    p["theme"] = theme
                    p["tags"] = tag_paper(p)
                    reg.append(p)
            calls += 1
            time.sleep(3.2)
        if calls >= MAX_CALLS:
            break
    if len(reg) < TARGET and "--smoke" not in sys.argv:
        reg += openalex_fill(TARGET - len(reg))
    reg = reg[:TARGET] if "--smoke" not in sys.argv else reg[:4]
    with open(OUT / "papers.jsonl", "w", encoding="utf-8") as f:
        for p in reg:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    by_theme = {}
    for p in reg:
        by_theme.setdefault(p.get("theme", "?"), []).append(p)
    lines = ["# The 100-paper register: documented ways the strongest models",
             "get integrated into systems", "",
             f"papers: **{len(reg)}** (arXiv + OpenAlex; keyless, $0)", ""]
    for t, ps in by_theme.items():
        lines.append(f"## {t} ({len(ps)})")
        lines += ["- " + p["published"][:4] + " " + p["title"][:120]
                  + " (" + p["arxiv_id"] + ") tags: " + ",".join(p["tags"])
                  for p in ps]
        lines.append("")
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[register]: {len(reg)} papers | calls: {calls}")


if __name__ == "__main__":
    main()