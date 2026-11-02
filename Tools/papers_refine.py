"""papers_refine - curate the harvested register through the OUTSOURCE lens.

The lens = Apex's own architecture ("like we do with gpt-oss-120b"):
Tier 1 hosted-brain     - the model runs elsewhere, the system orchestrates
Tier 2 tool-call loops  - the hosted brain drives verified local tools
Tier 3 routing/cascades - which outsourced brain, when, at what cost
Tier 4 RAG/memory       - outsourcing facts and recall to stores
Tier 5 sandboxed code   - the container-execution pattern (our V2)
Tier 6 protocols        - MCP-style integration contracts
Tier 7 serving infra    - the other side: making hosted inference cheap
Tier 8 boundaries       - trust, injection, fail-closed chat
Adds ~14 seed-canonicals (hand-annotated, provenance-marked), curates
exactly 100, writes papers_outsource.jsonl + OUTSOURCE.md, zips to Desktop.
$0, net-free at run time (seeds are hardcoded metadata).
"""
import io
import json
import pathlib
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = pathlib.Path(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed")
SRC = REPO / "_out" / "papers" / "papers.jsonl"

SEEDS = [
    ("2302.04761", "Toolformer", "2023", 2, "teaches LMs to self-issue API calls"),
    ("2210.03629", "ReAct", "2022", 2, "the reason-act loop our own engine runs"),
    ("2305.15334", "Gorilla", "2023", 2, "LM calling 1600+ hosted APIs precisely"),
    ("2303.17580", "HuggingGPT", "2023", 1, "hosted LLM as controller outsourcing tasks to specialist models"),
    ("2305.09678", "FrugalGPT", "2023", 3, "cascade across hosted providers to cut cost 98%"),
    ("2406.18665", "RouteLLM", "2024", 3, "router picks the strongest cheap-enough hosted brain"),
    ("2308.08155", "AutoGen", "2023", 1, "multi-agent apps on hosted backends"),
    ("2308.00352", "MetaGPT", "2023", 1, "software company of outsourced role-agents"),
    ("2405.15793", "SWE-agent", "2024", 5, "hosted brain inside a terminal/container interface"),
    ("2303.17760", "CAMEL", "2023", 1, "role-play agents cooperating over APIs"),
    ("2309.06180", "vLLM/PagedAttention", "2023", 7, "the serving layer that made hosted inference cheap"),
    ("2302.01314", "Orca", "2023", 7, "progressive learning from big-hosted to small-local"),
    ("2307.16789", "ToolLLM", "2023", 2, "16000+ real-world API tool calls"),
    ("2310.01805", "MemGPT", "2023", 4, "OS-style memory paging for bounded contexts"),
    ("2402.05129", "MoE inference surveys", "2024", 1, "the gpt-oss-120b MoE-class hosted pattern"),
]
TIERS = {
    1: "hosted-brain-orchestration", 2: "tool-call loops",
    3: "routing/cascades", 4: "RAG-memory-context", 5: "sandboxed code-execution",
    6: "protocols/MCP", 7: "serving-infra", 8: "trust boundaries",
}
TAG2TIER = [
    (("tool-call",), 2), (("retrieval-augmented",), 4),
    (("routing/cascade",), 3), (("multi-agent",), 1),
    (("code-execution",), 5), (("evaluation/judge",), 8),
    (("serving-infra",), 7), (("adaptation",), 1),
    (("security",), 8), (("memory/context",), 4),
    (("general-integration",), 1),
]


def tier_of(p):
    for t, tier in TAG2TIER:
        if t[0] in p.get("tags", []):
            return tier
    return 1


def main():
    if not SRC.exists():
        print("[ABORT]: extract first via _papers_finalize.py")
        sys.exit(1)
    papers, seen = [], set()
    for line in SRC.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        p = json.loads(line)
        for s_id, title in SEEDS:
            if s_id in p["arxiv_id"] or title.lower() in p["title"].lower():
                break
        else:
            seen.add(p["arxiv_id"])
            p["tier"] = tier_of(p)
            p["provenance"] = "harvested-actions-runner"
            papers.append(p)
    for aid, title, year, tier, note in SEEDS:
        if aid not in seen:
            seen.add(aid)
            papers.append({"arxiv_id": aid, "title": title + " - " + note,
                           "abstract": "", "authors": [],
                           "published": year + "-01-01",
                           "theme": "seed-canonical",
                           "tags": ["seed-canonical"], "tier": tier,
                           "provenance": "hand-annotated-seed"})
    picked = []
    per_tier = {t: 0 for t in set(TIERS.values())}
    seeds = [p for p in papers if "seed-canonical" in p.get("tags", [])]
    rest = sorted((p for p in papers if p not in seeds),
                  key=lambda p: -len(p.get("tags", [])))
    picked += seeds
    for p in seeds:
        per_tier[TIERS[p["tier"]]] = per_tier.get(TIERS[p["tier"]], 0) + 1
    for p in rest:
        if len(picked) >= 100:
            break
        t = TIERS[p["tier"]]
        picked.append(p)
        per_tier[t] = per_tier.get(t, 0) + 1
    out = REPO / "_out" / "papers"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "papers_outsource.jsonl", "w", encoding="utf-8") as f:
        for p in picked:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    lines = ["# Outsource-100: documented ways the strongest models get",
             "hosted elsewhere and driven by ordinary systems", "",
             "(the gpt-oss-120b pattern: heavy brain remote, orchestration local)", "",
             f"total: **{len(picked)}** | provenance: seeds hand-annotated,",
             "rest harvested by a GitHub Actions runner (keyless, $0)", ""]
    order = ["hosted-brain-orchestration", "tool-call loops", "routing/cascades",
             "RAG-memory-context", "sandboxed code-execution", "protocols/MCP",
             "serving-infra", "trust boundaries"]
    for tier in order:
        tp = [p for p in picked if TIERS[p["tier"]] == tier]
        lines.append(f"## {tier} ({len(tp)})")
        lines += ["- " + p["published"][:4] + " " + p["title"][:130]
                  + " [" + p["arxiv_id"] + "]" for p in tp]
        lines.append("")
    (out / "OUTSOURCE.md").write_text("\n".join(lines), encoding="utf-8")
    zpath = pathlib.Path(r"C:\Users\seaha\OneDrive\Desktop") / "Outsource-100.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ("papers.jsonl", "README.md", "papers_outsource.jsonl",
                     "OUTSOURCE.md"):
            p = out / name
            if p.exists():
                z.write(p, name)
    print("[curated]:", len(picked), "| per-tier:", per_tier, "seeds:", len(seeds))
    print("[zipped]:", zpath, f"({zpath.stat().st_size}b)")


if __name__ == "__main__":
    main()