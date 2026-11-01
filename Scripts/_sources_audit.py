import json, os, re, subprocess
ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
FILES = {
    "papers_2026.jsonl": 100,
    "papers_2026_evolution.jsonl": 421,
    "papers_2026_agents.jsonl": 100,
    "papers_2026_coding.jsonl": 100,
}
ok_all = True
seen_ids = {}
for fn, expected in FILES.items():
    p = os.path.join(ROOT, "Config", fn)
    rows = []
    bad_json = 0
    for line in open(p, encoding="utf-8-sig"):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            bad_json += 1
    ids = [r.get("id") for r in rows if r.get("id")]
    dupes_in_file = len(ids) - len(set(ids))
    dates = sorted(set(r.get("published", "?")[:10] for r in rows))
    tracked = subprocess.run(["git", "-C", ROOT, "ls-files", "Config/" + fn],
                             capture_output=True, text=True,
                             encoding="utf-8").stdout.strip() != ""
    status = subprocess.run(["git", "-C", ROOT, "status", "--short",
                             "--", "Config/" + fn],
                            capture_output=True, text=True,
                            encoding="utf-8").stdout.strip() or "clean"
    ok = (len(rows) == expected and bad_json == 0 and dupes_in_file == 0
          and tracked and status == "clean" and all(d.startswith("2026") for d in dates))
    ok_all = ok_all and ok
    # cross-file dedupe check
    for pid in ids:
        if pid in seen_ids:
            ok_all = False
            print(f"   CROSS-DUP: {pid} in {fn} AND {seen_ids[pid]}")
        seen_ids[pid] = fn
    print(f"{'PASS' if ok else 'FAIL'} | {fn}: {len(rows) if len(rows) == expected else str(len(rows)) + ' != ' + str(expected)} rows"
          f" | dates {dates[0]}..{dates[-1]} | in-file dupes {dupes_in_file}"
          f" | bad json {bad_json} | git-tracked {tracked} | status '{status}'")
print(f"\nTOTAL CANON: {len(seen_ids)} unique papers across 3 ledgers")
missing = [fn for fn in ("Config/goal_comparison.json", "Config/skill_gaps.json",
                         "Config/goal_coherence.json", "Config/benchmark_card.json",
                         "Config/backlog_snapshot.json", "Config/SurrogateCourt.json",
                         "Config/ApexUpwardManifest.json",
                         "Config/runtime_receipts.jsonl",
                         "family/work_specs.jsonl")
           if not subprocess.run(["git", "-C", ROOT, "ls-files", fn],
                                 capture_output=True, text=True,
                                 encoding="utf-8").stdout.strip()]
print("instrument receipts NOT git-tracked:", missing or "NONE (all tracked)")
dirty = subprocess.run(["git", "-C", ROOT, "status", "--short"],
                        capture_output=True, text=True, encoding="utf-8").stdout
print("working tree:", dirty.strip() or "CLEAN (everything committed)")
print("SOURCES AUDIT:", "ALL RECEIPTS CURRENT + COMMITTED" if ok_all and not missing
      and not dirty.strip() else "GAPS FOUND (see above)")