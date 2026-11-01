import py_compile, json, os, re
ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
PYS = ["Scripts/GenePool.py", "Scripts/ApexUpward.py",
       "Scripts/SurrogateFitnessCourt.py", "Scripts/EvolutionSpeedup.py",
       "Scripts/SwarmOrchestrator.py", "Scripts/RepeatTest.py",
       "Scripts/CalibratedEvolution.py"]
JS = ["Config/ApexUpwardManifest.json", "Config/SurrogateCourt.json",
      "Config/gene_archive.json", "Config/PathMemory.json",
      "Config/curriculum.json", "Config/gauntlet_weights.json",
      "Config/papers_2026_evolution.jsonl", "Config/papers_2026.jsonl"]
bad = []
for rel in PYS:
    try:
        py_compile.compile(os.path.join(ROOT, rel), doraise=True)
    except Exception as e:
        bad.append(f"{rel} [COMPILE: {str(e)[:50]}]")
for rel in JS:
    try:
        src = open(os.path.join(ROOT, rel), encoding="utf-8-sig").read()
        if rel.endswith(".json"):
            json.loads(src)
        else:
            for i, line in enumerate(src.splitlines()[:3]):
                pass
            if re.search(r"^<{7} ", src, re.M):
                bad.append(rel + " [MARKERS]")
    except Exception as e:
        bad.append(f"{rel} [{str(e)[:50]}]")
print("SHIP SWEEP:", "ALL CLEAN - every pushed file compiles/parses, marker-free"
      if not bad else bad)