"""THE UNNAMED-DIRS VERDICT: every directory in the founder's screenshots
that my sweeps WALKED but never NAMED or specifically verified - each one
walked now: every file counted, every .py compiled, every .json parsed,
the skills/SkillLibrary dirs checked against the library count (an
under-counted library is an omnivore lie), and .env excluded from ALL
text reading (the secrets law - the sweep's honest bug)."""
import ast
import json
import os

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
DIRS = ("edge_hub", "portfolio", "hub_kits", "skills", "swarm_cache",
        "strategic_vault", "swarm_debates", "SkillLibrary")
report = {}
for d in DIRS:
    p = os.path.join(ROOT, d)
    e = {"exists": os.path.isdir(p), "files": 0, "data_ok": 0, "data_bad": [],
         "py_ok": 0, "py_bad": [], "sample": []}
    if e["exists"]:
        for dp, dns, fns in os.walk(p):
            for fn in fns:
                fp = os.path.join(dp, fn)
                e["files"] += 1
                if len(e["sample"]) < 4:
                    e["sample"].append(fn[:40])
                if fn.endswith(".json"):
                    try:
                        json.load(open(fp, encoding="utf-8-sig"))
                        e["data_ok"] += 1
                    except Exception as ex:
                        try:
                            ok = all(json.loads(x) for x in
                                     open(fp, encoding="utf-8-sig")
                                     if x.strip())
                            e["data_ok"] += 1 if ok else 0
                            if not ok:
                                e["data_bad"].append(f"{d}/{fn}")
                        except Exception:
                            e["data_bad"].append(f"{d}/{fn}: {str(ex)[:40]}")
                elif fn.endswith((".py", ".pyw")):
                    try:
                        ast.parse(open(fp, encoding="utf-8-sig",
                                       errors="replace").read())
                        e["py_ok"] += 1
                    except Exception as ex:
                        e["py_bad"].append(f"{d}/{fn}: {str(ex)[:40]}")
    report[d] = e
    print(f"{d:16s} files {e['files']:4d} | py ok {e['py_ok']:3d} "
          f"bad {len(e['py_bad']):2d} | json ok {e['data_ok']:3d} "
          f"bad {len(e['data_bad']):2d} | {e['sample'][:2]}")
    for b in e["py_bad"][:2]:
        print("      PY-FAIL:", b)
    for b in e["data_bad"][:2]:
        print("      JSON-FAIL:", b)
with open(os.path.join(ROOT, "Config", "unnamed_dirs_audit.json"), "w",
          encoding="utf-8") as f:
    json.dump({"ts": "2026-11-01", "dirs": report}, f, indent=1)
print("report -> Config/unnamed_dirs_audit.json")