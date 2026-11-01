import re
src = open(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\_adapter_tidy.py",
           encoding="utf-8-sig").read()
m = re.search(r"PAT = re\.compile\(\s*r[\"'](.+?)[\"']\s*,\s*re\.I\)", src, re.S)
print("PAT pattern found in file:", bool(m))
pat_text = m.group(1) if m else "?"
print("pattern text:", pat_text[:150])
pat = re.compile(pat_text, re.I)
for n in ("build_completion_pack.py", "chat_v2_probe.py", "cleanup_sweep.py",
          "fetch_handoff.py", "v2_job_engine.py", "apply_credible_spine.py",
          "RecruitBoard_clean_backup.py"):
    print(f"  {n:34s} -> match: {bool(pat.match(n))}")