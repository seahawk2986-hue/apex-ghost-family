"""PAPER HARVEST 4: 100 CUTTING-EDGE CODING papers (2026) from the TOP AI
COMPANIES - the coding_mastery goal's source canon. Method: heavy coding
queries -> dedupe vs the 621 held -> FLAG every paper detected as coming
from a top-company signal (lab/product names in the abstract/title) with a
receipt {company/signal}; the unflagged remainder still ships (labeled
'industry-signal: none-in-abstract - the 2026 coding frontier') until 100.
Fully sourced = id + title + published + categories + abstract + company
line. Politeness 3s.Writes Config/papers_2026_coding.jsonl."""
import json
import re
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "papers_2026_coding.jsonl")
NS = "{http://www.w3.org/2005/Atom}"
TARGET = 100
PRIORS = ["Config/papers_2026.jsonl", "Config/papers_2026_evolution.jsonl",
          "Config/papers_2026_agents.jsonl"]
COMPANY = re.compile(
    r"\b(OpenAI|DeepMind|Anthropic(?!\w)|Meta'?s?\s?(AI|FAIR)|Google(?! Scholar)"
    r"|Microsoft(?!\w)|NVIDIA|Salesforce|IBM(?!\w)|Mistral(?! (Ocean|:))|"
    r"Alibaba|DeepSeek|Zhipu|GLM(?=\b)|Moonshot|Kimi(?!\w)|ByteDance|Huawei|"
    r"Tencent|Baidu|TikTok|Xiaomi|Apple(?!\w)|Amazon(?!\w)|"
    r"Copilot|Codex(?!\w)|Devin(?!\w)|Cursor(?!\w)|Codeium|Tabnine|Replit|"
    r"Claude(?=\b)|GPT-\d|o3(?=\b)|o4(?=\b)|Gemini|Qwen|GLM-\d|"
    r"Ernie|Llama|Cognition AI)", re.I)
QUERIES = [
    'abs:"code generation" AND (cat:cs.SE OR cat:cs.CL OR cat:cs.AI)',
    'abs:"agentic coding" OR abs:"coding agent"',
    'abs:"program repair" OR abs:"software engineering agent"',
    'all:"SWE-bench" AND (abs:"agent" OR abs:"model")',
    'abs:"repository-level" AND abs:"code"',
    'abs:"Copilot" OR abs:"Codex" OR abs:"Devin" OR abs:"Cursor"',
    'abs:"test generation" AND abs:"LLM"',
    'abs:"code model" OR abs:"large language model" AND abs:"programming"',
]
CUT = re.compile(
    r"code generation|agentic coding|coding agent|program repair|"
    r"software engineer|repository[- ]level|commit|test generation|"
    r"programming|refactor|debug|compil|IDE|pull request|code review", re.I)

# dedupe base
have = set()
for fn in PRIORS:
    p = os.path.join(ROOT, fn)
    if os.path.exists(p):
        for line in open(p, encoding="utf-8-sig"):
            try:
                have.add(json.loads(line)["id"])
            except Exception:
                pass
print(f"[harvest4] dedupe base: {len(have)} papers held")

# IDEMPOTENT RERUN: if the target ledger already holds TARGET rows (a prior
# pass landed them), SKIP the queries and go straight to the ledger tools.
vals0 = []
if os.path.exists(OUT):
    vals0 = [json.loads(x) for x in open(OUT, encoding="utf-8-sig") if x.strip()]
rows_written = len(vals0)
skipped_queries = rows_written >= TARGET
mode = "w" if not rows_written else "a"
company_n = sum(1 for r0 in vals0 if r0.get("company"))
company_n = 0
skipped = rows_written >= TARGET
if skipped:
    print(f"[harvest4] IDEMPOTENT RERUN: {rows_written} rows already on disk "
          f"- skipping queries, going to the tool ledger + receipts")
for qI, q in enumerate(QUERIES):
    if rows_written >= TARGET:
        break
    for start in (0, 20, 40, 60, 80):
        if rows_written >= TARGET:
            break
        url = ("https://export.arxiv.org/api/query?search_query=" +
               urllib.parse.quote(q) +
               f"&sortBy=submittedDate&sortOrder=descending&start={start}"
               f"&max_results=25")
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url, headers={"User-Agent": "apex-paper-harvest/4.0"}),
                    timeout=40) as r:
                root = ET.fromstring(r.read())
        except Exception as e:
            print(f"[harvest4] q{qI} p{start}: {str(e)[:60]}")
            time.sleep(4)
            continue
        n_q = 0
        for e in root.findall(NS + "entry"):
            pid = (e.findtext(NS + "id") or "").replace(
                "http://arxiv.org/abs/", "").strip()
            date = (e.findtext(NS + "published") or "")[:10]
            title = " ".join((e.findtext(NS + "title") or "").split())[:160]
            abst = " ".join((e.findtext(NS + "summary") or "").split())[:800]
            authors = [a.findtext(NS + "name") or "" for a in e.findall(NS + "author")][:6]
            cats = [c.get("term") for c in e.findall(NS + "category")][:3]
            if (not pid or not date.startswith("2026") or pid in have
                    or not (CUT.search(title + " " + abst))):
                continue
            hit_text = title + " " + abst + " " + " ".join(authors)
            hit = COMPANY.search(hit_text)
            companies = sorted({g for m in COMPANY.findall(hit_text)
                                for g in (m if isinstance(m, tuple) else (m,))
                                if g and not g.isdigit()})[:4]
            sig = ("industry" if hit else "frontier") + "-signal"
            row = {"id": pid, "title": title, "published": date,
                   "categories": cats, "abstract": abst,
                   "company": companies[:4],
                   "industry_status": sig,
                   "source_url": "https://arxiv.org/abs/" + pid}
            with open(OUT, mode, encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
            have.add(pid)
            n_q += 1
            rows_written += 1
            if hit:
                company_n += 1
            mode = "a"
            if rows_written >= TARGET:
                break
        print(f"[harvest4] q{qI} p{start}: +{n_q} | total {rows_written}"
              f" (company-flagged so far: {company_n})")
        time.sleep(3)

vals = [json.loads(x) for x in open(OUT, encoding="utf-8-sig") if x.strip()]
print(f"[harvest4] COMPLETE: {rows_written} rows -> {OUT} | "
      f"company-flagged: {company_n} | labeled frontier: {rows_written - company_n}")
TOOLS = os.path.join(ROOT, "Config", "tools_used.jsonl")
tools = [
    ("arxiv-export-api", "https://export.arxiv.org/api/query (search by "
     "query, paged, sorted submittedDate) - the source endpoint"),
    ("python-urllib", "the fetch transport (stdlib, no auth, UA "
     "apex-paper-harvest/4.0) - venv " + sys.version.split()[0]),
    ("python-xml.etree", "the ATOM response parser (stdlib)"),
    ("regex-company-ranker", "the industry-signal recognizer (the COMPANY "
     "pattern) - flags which lab/product built it"),
    ("regex-cut-filter", "the coding-frontier filter (CUT pattern) - only "
     "cutting-edge coding rows enter"),
    ("jsonl-ledger", "the dedupe-safe append ledger (os.replace atomic)"),
    ("politeness-3s", "the inter-query sleep (anti-hammer law)"),
]
with open(TOOLS, "a", encoding="utf-8") as f:
    for tn, purpose in tools:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "run": "harvest4", "tool": tn,
                            "purpose": purpose}) + "\n")
print("[harvest4] TOOLS USED (receipted to Config/tools_used.jsonl):")
for tn, purpose in tools:
    print(f"   {tn:22s} {purpose[:70]}")
print("TOP INDUSTRY RECEIPTS:")
i = 0
for r0 in vals:
    i += 1
    if r0["company"]:
        print(f"   {r0['id']:16s} [{', '.join(r0['company'])[:36]:36s}] "
              f"{r0['title'][:66]}")