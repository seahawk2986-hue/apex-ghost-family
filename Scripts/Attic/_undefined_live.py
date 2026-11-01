import glob
import subprocess
import sys
import os

# the LIVE-code files outside Scripts (root + adapter + family)
targets = set(["ApexWebScraper.py", "PublishMcp.py", "ScanMechanisms.py",
               "run_apex_evolution.py", "test_reward.py", "ApexInstaller.py",
               "ApexIPCEngine.py", "ApexMemory.py", "ApexNetScraper.py",
               "ApexPacing.py", "optimized_agent.py", "TrainingCalc.py",
               "TrainingLogParser.py", "TrainingMinStack.py"])
paths = []
for base in (r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed",
             r"C:\Users\seaha\Apex-Adapter"):
    for dp, dns, fns in os.walk(base):
        if any(x in dp for x in ("venv", ".git", "__pycache__", "Scratch",
                                 "site-packages", "skill_stage",
                                 "Backup_Archive", "versions", "Attic",
                                 "Lib", ".ruff_cache", "_handoff")):
            dns[:] = []
            continue
        for fn in fns:
            p = os.path.join(dp, fn)
            if fn.endswith(".py") and (fn in targets or dp.endswith("Scripts")
                                       or "Scripts" in dp):
                paths.append(p)
seen_und = {}
for i in range(0, len(paths), 40):
    batch = paths[i:i + 40]
    r = subprocess.run([sys.executable, "-m", "pyflakes"] + batch,
                       capture_output=True, text=True, encoding="utf-8",
                       timeout=240)
    for w in (r.stdout or "").splitlines():
        m = re.search(r"undefined name '(\w+)'", w) if (re := __import__("re")) else None
        if m:
            key = m.group(1)
            f = w.split(":")[0]
            seen_und.setdefault(key, []).append(f)
for k, v in sorted(seen_und.items(), key=lambda kv: -len(kv[1])):
    print(f"{k:24s} x{len(v):3d}  e.g. {v[0][-60:]}")
print("TOTAL undefined names (live code):", sum(len(v) for v in seen_und.values()))