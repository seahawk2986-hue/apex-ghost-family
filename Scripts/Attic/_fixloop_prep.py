"""THE FIX-LOOP'S PREP: show the exact offending lines (fix-with-eyes)."""
import re

CHECKS = [
    (r"Scripts\ApexAutonomousAgent.py", r"____name____|___name___|_file_"),
    (r"Scripts\ApexModelRouter.py", r"___name___|____name____"),
    (r"Scripts\Invoke-CodingMastery.py", r"___name___|____name____|_file_"),
    (r"Scripts\run_agent_foundry.py", r"____name____|___name___"),
    (r"Scripts\QualityGate.py", r"\bshutil\b"),
    (r"Scripts\WireShop.py", r"\btime\b"),
]
for rel, pat in CHECKS:
    p = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed" + "\\" + rel
    try:
        lines = open(p, encoding="utf-8-sig", errors="replace").readlines()
    except Exception as e:
        print(f"[{rel}] unreadable: {str(e)[:50]}")
        continue
    print(f"== {rel} ==")
    hits = []
    for i, ln in enumerate(lines, 1):
        if re.search(pat, ln):
            hits.append((i, ln.rstrip()))
    # the import-lines too (to see what's already imported)
    for i, ln in hits[:6]:
        print(f"  L{i}: {ln[:120]}")
    if not hits:
        print("  (no hits)")

import glob
print("== where do the scraper-copies live? ==")
for pat in ("**/ApexNetScraper_v_*.py", "**/ApexWebScraper_v_*.py"):
    for f in glob.glob(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
                       "\\" + pat, recursive=True)[:6]:
        print("  ", f.replace(r"C:\Users\seaha\Downloads\Apex-With"
                              r"-Triggers-Fixed", "."))
print("== reward_telemetry.json = the first bytes ==")
try:
    b = open(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
             r"\Config\reward_telemetry.json", "rb").read()
    print("  head:", b[:60])
    print("  the 0xe5 check:", [i for i, x in enumerate(b[:40]) if x > 0x7f])
except Exception as e:
    print("  honest:", str(e)[:60])