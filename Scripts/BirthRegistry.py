"""THE BIRTH REGISTRY: every child's birth certificate, forever counted."""
import py_compile

DEP = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\DeploySwarm.py"
BIRTHS = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\Births.py"

# 0. the births registry module (the census's ledger)
births_mod = '''"""The family's birth registry - every child counted, every death recorded."""
import json
import os
import time

BIRTHS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "Config", "family_births.jsonl")


def birth(shard, variant, territory, pid):
    _append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "event": "birth",
             "child_pid": pid, "shard": shard, "variant": variant,
             "territory": territory})


def death(shard, variant):
    _append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "event": "dissolved",
             "child_pid": None, "shard": shard, "variant": variant})


def census():
    try:
        rows = [json.loads(x) for x in open(BIRTHS, encoding="utf-8-sig") if x.strip()]
        b = sum(1 for x in rows if x["event"] == "birth")
        d = sum(1 for x in rows if x["event"] == "dissolved")
        return {"born_total": b, "dissolved_total": d, "alive_now": b - d}
    except Exception:
        return {"born_total": 0, "dissolved_total": 0, "alive_now": 0}


def _append(row):
    try:
        with open(BIRTHS, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\\n")
    except Exception:
        pass
'''
open(BIRTHS, "w", encoding="utf-8").write(births_mod)

# 1. wire births into the launcher's spawn + the grain haul (dissolutions)
src = open(DEP, encoding="utf-8-sig").read()
if "import Births" not in src:
    src = src.replace("import json\nimport time",
                      "import json\nimport sys as _sys\n"
                      "_sys.path.insert(0, r\"C:\\\\Users\\\\seaha\\\\Downloads\\\\Apex-With-Triggers-Fixed\\\\Scripts\")\n"
                      "import Births\nimport time", 1)
    log1 = "births-import"
else:
    log1 = "births-import (already)"

# birth rows at spawn:
if "Births.birth(" not in src:
    src = src.replace("    _heredity(shard, fleet_n)",
                      "    Births.birth(shard, env.get('APEX_VARIANT'), note, 0)\n"
                      "    _heredity(shard, fleet_n)", 1)
    log1 += " + birth-rows"
if "Births.death(" not in src:
    src = src.replace('''        print(f"grain line: shard {shard} -> {json.dumps(r1 or {})[:120]}")''',
                      '''        print(f"grain line: shard {shard} -> {json.dumps(r1 or {})[:120]}")
        try:
            Births.death(shard, "child")   # the census: dissolved, not lost
        except Exception:
            pass''', 1)
    log1 += " + death-rows"
open(DEP, "w", encoding="utf-8-sig").write(src)
py_compile.compile(DEP, doraise=True)
py_compile.compile(BIRTHS, doraise=True)
print("COMPILED CLEAN |", log1)
print("census now:", __import__("sys").modules)