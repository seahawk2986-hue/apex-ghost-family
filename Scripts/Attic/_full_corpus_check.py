import json, os, re
ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
FILES = ["Config/papers_2026.jsonl", "Config/papers_2026_evolution.jsonl",
         "Config/papers_2026_agents.jsonl"]
import sys
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
import GoalComparison as GC

ALL = [os.path.join(ROOT, f) for f in FILES]
papers, counts, reps = GC.scan_all(ALL) if hasattr(GC, "scan_all") else (None, None, None)
if papers is None:
    # inline full-corpus scan (GoalComparison only has the agents scan())
    rows_all, counts = [], {k: 0 for k in GC.CLUSTERS}
    reps = {k: [] for k in GC.CLUSTERS}
    for path in ALL:
        try:
            rows_all += [json.loads(x) for x in open(path, encoding="utf-8-sig") if x.strip()]
        except Exception:
            pass
        for p in rows_all:
            hay = p.get("title", "") + " " + p.get("abstract", "")
            for k, pat in GC.CLUSTERS.items():
                if pat.search(hay):
                    counts[k] += 1
                    if len(reps[k]) < 2:
                        reps[k].append(p["id"])
        rows_all = rows_all  # accumulate? no: dedupe by scanning whole set once
    print(f"FULL CORPUS: {len(rows_all)} rows (with repeats across scans - dedupe below)")
    ids = {p["id"] for p in rows_all}
    print(f"unique papers: {len(ids)} (expected 621: {'OK' if len(ids) == 621 else 'MISMATCH'})")
    print("clusters: " + " | ".join(f"{k}:{v}" for k, v in counts.items()))
    # NEW recurring capability terms not yet in our clusters/registry
    known_terms = re.compile(
        r"surrogate|bandit|evaluator|verif|runtime|long[- ]horizon|context|memory|"
        r"skill|self[- ]improv|autonomous|benchmark|efficien|calibrat|fitness|"
        r"genetic|evolutionary|open[- ]ended|quality[- ]diversity|godel|darwin|"
        r"curriculum|lamarck|pareto|self[- ]play|deception|speculative|reward|mcts|"
        r"tree of thoughts?|reflection|tool use|agent communicat|swarm|multi[- ]agent|"
        r"world model|planning|curiosit|reward hacking|alignment|safet", re.I)
    freq = {}
    for p in rows_all:
        hay = p.get("title", "") + " " + p.get("abstract", "")
        for w in set(re.findall(r"[a-zA-Z][a-zA-Z-]{6,}", hay.lower())):
            if not known_terms.search(w):
                freq[w] = freq.get(w, 0) + 1
    top = sorted(freq.items(), key=lambda kv: -kv[1])[:18]
    print("unclustered recurring terms:", ", ".join(f"{w}({n})" for w, n in top))