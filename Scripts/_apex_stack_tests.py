"""THE A+-STACK TESTS, stage 1 (net-free, throwaway copies only):
VetLineRemote's vet-lanes + the register-shape + the idempotence + the
meter-math, and the workflow-yaml's parse+field-asserts."""
import ast as _ast
import json
import os
import shutil
import sys
import tempfile

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
import VetLineRemote as R  # noqa: E402

PASS = []
def ok(name, cond, detail=""):
    PASS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (" | " + detail if detail else ""))

# 1) the vet-lanes
GOOD = ("import re, sys\n"
        "def clamp(x, lo, hi):\n"
        "    \"\"\"bounded clamp\"\"\"\n"
        "    return max(lo, min(hi, x))\n")
ok("vet: clean module passes", R.vet_text(GOOD)[0])
ok("vet: banned import refused",
   R.vet_text("import socket\nprint(0)\n")[1].get("why", "").startswith("banned:socket"))
ok("vet: dynamic-exec refused",
   R.vet_text("x = 1\n" + "eval('x')\n")[1].get("why", "").startswith("banned:dynamic-exec"))
ok("vet: over-size refused",
   R.vet_text("x = 0\n" * 50000)[1].get("why") == "caps")
ok("vet: syntax-error refused",
   not R.vet_text("def broken(:\n")[0])

# 2) the register-row shape + the idempotence + the meter-math
tmp = tempfile.mkdtemp()
os.makedirs(os.path.join(tmp, "Config"))
os.makedirs(os.path.join(tmp, "family"))
lib = {"skills": [], "built": ""}
rw = {"points": 0}
json.dump(lib, open(os.path.join(tmp, "Config", "SkillLibrary.json"), "w"))
json.dump(rw, open(os.path.join(tmp, "Config", "GymRewards.json"), "w"))
grain = {"leads": [{"repo": "ghost/fake-repo", "score": 90, "tier": "GOLD",
                    "stars": 10, "license": "MIT"}] * 3}
json.dump(grain, open(os.path.join(tmp, "family", "leads_grain.json"), "w"))
# patch the module's paths to the throwaway tree + stub the fetch-lane
R.LIB = os.path.join(tmp, "Config", "SkillLibrary.json")
R.REWARDS = os.path.join(tmp, "Config", "GymRewards.json")
R.GRAIN = os.path.join(tmp, "family", "leads_grain.json")
R.ROOT = tmp
real_gh = R.gh
calls = {"n": 0}
def fake_gh(url, timeout=30):
    calls["n"] += 1
    if "/git/trees/" in url:
        return json.dumps({"tree": [
            {"path": "tools/clamp.py", "type": "blob",
             "url": "https://api.github.com/x", "size": len(GOOD)}]}).encode()
    return GOOD.encode()
R.gh = fake_gh
R.MAX_REPOS = 5
R.main()
lib2 = json.load(open(R.LIB, encoding="utf-8-sig"))
rw2 = json.load(open(R.REWARDS, encoding="utf-8-sig"))
rows = lib2.get("skills", [])
ok("register: one vetted row", len(rows) == 1, str(rows[:1]))
ok("register row: sha + provenance + vetby",
   len(rows) == 1 and rows[0]["sha256"] and rows[0]["source_repo"]
   == "ghost/fake-repo" and rows[0].get("vetby") == "hub-runner-v1")
ok("register row: imports non-empty", rows and rows[0]["imports"] == ["re", "sys"])
ok("meter: +10 per vetted", rw2["points"] == 10 and
   rw2["library_points"] == 10, f"total={rw2['points']}")
ok("dedupe: 3 dup-leads = 1 repo = 1 row (idempotent shape)",
   len(rows) == 1 and calls["n"] >= 1)
# the re-run = the sha/library-dedupe = the empty result (the honest no-op)
R.main()
lib3 = json.load(open(R.LIB, encoding="utf-8-sig"))
rw3 = json.load(open(R.REWARDS, encoding="utf-8-sig"))
ok("idempotence: a re-run adds nothing / pays nothing", len(lib3["skills"]) == 1
   and rw3["points"] == 10, f"skills={len(lib3['skills'])} pts={rw3['points']}")

# 3) the workflow-yaml parse + the field-asserts
try:
    import yaml
    y = yaml.safe_load(open(os.path.join(ROOT, ".github", "workflows",
                                         "vet-line.yml"), encoding="utf-8"))
    ok("yml: parses", True)
    sect = y.get("on") or y.get(True) or {}
    ok("yml: hourly-cron + dispatch + the write-permission",
       "schedule" in sect and "workflow_dispatch" in sect
       and y["permissions"]["contents"] == "write",
       str(list(y.keys()))[:80])
except ImportError:
    ok("yml: pyyaml-missing (the pip-install = the fix)", False)

R.gh = real_gh
shutil.rmtree(tmp, ignore_errors=True)
fails = [n for n, c in PASS if not c]
print(f"\n== STAGE-1 VERDICT: {len(PASS) - len(fails)}/{len(PASS)} PASS"
      + (f" | FAILS: {fails}" if fails else " — ALL GREEN =="))