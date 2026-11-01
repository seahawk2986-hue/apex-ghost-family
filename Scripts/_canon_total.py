import json
import os

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
tot, seen = 0, set()
for f in ("papers_2026", "papers_2026_evolution", "papers_2026_agents",
          "papers_2026_coding", "papers_2026_earning", "papers_2026_jobs"):
    p = os.path.join(ROOT, "Config", f + ".jsonl")
    rows = [json.loads(x) for x in open(p, encoding="utf-8-sig") if x.strip()]
    tot += len(rows)
    seen.update(r["id"] for r in rows)
    print(f"{f}: {len(rows)} rows")
print(f"CANON total: {tot} rows | UNIQUE: {len(seen)}")