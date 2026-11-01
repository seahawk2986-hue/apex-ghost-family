import json, os, re
ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
TERMS = re.compile(r"surrogate|bandit|evaluator|offline (evaluation|policy)|"
                   r"fitness (predictor|landscap)|evaluation (efficient|cost)|"
                   r"sample[- ]efficient|cheap (evaluation|fitness)|"
                   r"learned (critic|evaluator)", re.I)
hits = []
for fn in ("papers_2026.jsonl", "papers_2026_evolution.jsonl"):
    p = os.path.join(ROOT, "Config", fn)
    n = 0
    for line in open(p, encoding="utf-8-sig"):
        if not line.strip():
            continue
        n += 1
        r = json.loads(line)
        hay = (r.get("title", "") + " " + r.get("abstract", ""))
        if TERMS.search(hay):
            hits.append((fn, r["id"], r["title"][:90],
                         re.findall(r"(surrogate|bandit|evaluator|"
                                    r"offline evaluation|offline policy|"
                                    r"fitness predictor|sample-efficient|"
                                    r"learned evaluator)", hay, re.I)[:3]))
    print(f"{fn}: scanned {n} rows")
print(f"\nEVALUATOR/SURROGATE/BANDIT CLUSTER: {len(hits)} papers")
for fn, pid, t, kw in hits[:25]:
    print(f"  {pid:16s} {t}")
    print(f"                    signals: {', '.join(kw) or '-'}")