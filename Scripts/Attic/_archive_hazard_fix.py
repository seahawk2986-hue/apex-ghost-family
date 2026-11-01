"""THE ARCHIVE RESTORE-HAZARD CURE: the dunder-typo class in
Backup_Archive\\manual_fix_20261030\\ (the files a future restore would
copy over the live tree = the most dangerous bugs in the repo).
Each replacement = printed + verified."""
import os
import re

BASE = (r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
        r"\Backup_Archive\manual_fix_20261030")
FIXES = [
    ("ApexAutonomousAgent.py", r"____name____", "__name__"),
    ("ApexModelRouter.py", r"___name___", "__name__"),
    ("run_agent_foundry.py", r"____name____", "__name__"),
]
# Invoke-CodingMastery = both classes; ApexIPCEngine = the missing import
DUNDER = re.compile(r"____name____|___name___")
TOTAL = 0
for fn, pat, rep in FIXES:
    p = os.path.join(BASE, fn)
    if not os.path.exists(p):
        print(f"[skip] {fn} = not present")
        continue
    s = open(p, encoding="utf-8-sig", errors="replace").read()
    s2 = re.sub(pat, rep, s)
    if s2 != s:
        open(p, "w", encoding="utf-8").write(s2)
        n = len(re.findall(pat, s))
        TOTAL += n
        print(f"[fix] {fn}: {n}x {pat} -> {rep}")

p = os.path.join(BASE, "Invoke-CodingMastery.py")
if os.path.exists(p):
    s = open(p, encoding="utf-8-sig", errors="replace").read()
    n = len(DUNDER.findall(s)) + len(re.findall(r"_file_", s))
    s2 = re.sub(r"_file_", "__file__", re.sub(DUNDER, "__name__", s))
    open(p, "w", encoding="utf-8").write(s2)
    TOTAL += n
    print(f"[fix] Invoke-CodingMastery.py: {n}x dunders -> __name__/__file__")

p = os.path.join(BASE, "ApexIPCEngine.py")
if os.path.exists(p):
    s = open(p, encoding="utf-8-sig", errors="replace").read()
    if "from typing import" not in s and re.search(r"\bCallable\b", s):
        s = ("from typing import Callable\n" + s)
        open(p, "w", encoding="utf-8").write(s)
        TOTAL += 1
        print("[fix] ApexIPCEngine.py: +from typing import Callable")
print(f"[total] {TOTAL} restore-hazard bug(s) cured")