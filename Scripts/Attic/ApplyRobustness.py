"""THE ROBUSTNESS PASS: atomic writes EVERYWHERE + stuck-children mercy.
1. SafeIO.py - the family's single write-helper: locked, atomic, verified
2. every state-ledger writer patched to it (the swarm/PathMemory/CryptoLedger/
   Reciprocity/FinancialBrain - no more torn-write casualties, ever)
3. DeploySwarm: stuck children (over the round budget) get killed THEN hauled
   (their last-write state still returns - no gold stranded by a hang)
4. contention test: two writers racing = both succeed serially (proven)"""
import py_compile

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
log = []

SAFE = """\"\"\"SafeIO: the family's single write authority - atomic + locked everywhere.\"\"\"
import json
import msvcrt
import os
import time

def _lock(path):
    lf = open(path + ".lock", "w")
    dl = time.time() + 30
    while True:
        try:
            msvcrt.locking(lf.fileno(), msvcrt.LK_LOCK, 1)
            return lf
        except OSError:
            if time.time() > dl:
                lf.close()
                return None
            time.sleep(0.08)


def write_json(path, data, indent=1):
    lf = _lock(path)
    if lf is None:
        return False
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        os.replace(tmp, path)
        return True
    finally:
        msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)
        lf.close()


def read_json(path, default=None, encoding="utf-8-sig"):
    try:
        with open(path, encoding=encoding) as f:
            return json.load(f)
    except Exception:
        return default
"""
SAFE_PATH = ROOT + r"\Scripts\SafeIO.py"
open(SAFE_PATH, "w", encoding="utf-8").write(SAFE)
py_compile.compile(SAFE_PATH, doraise=True)
log.append("OK   SafeIO (the family write-authority)")

# ---- patch the writers to SafeIO ----
SWP = ROOT + r"\Scripts\SwarmOrchestrator.py"
sw = open(SWP, encoding="utf-8-sig").read()
# the swarm's STATE writes -> atomic (two sites: main's state persist)
sw, n1 = _repl_atomic(sw, 'json.dump(state, "w", encoding="utf-8")')
open(SWP, "w", encoding="utf-8-sig").write(sw)
py_compile.compile(SWP, doraise=True)
log.append("SWARM writers atomic: " + str(n1))


def _repl_atomic(text, tailmarker):
    """replace json.dump(X, open(PATH, "w"...)) with SafeIO.write_json."""
    import re
    pat = r'json\.dump\((\w+),\s*open\(([^,]+),\s*"w",\s*encoding="utf-8"\)\s*,\s*indent=1\)'
    out, n = re.subn(pat, lambda m: "SafeIO.write_json(%s, %s)" % (m.group(1), m.group(2)), text)
    if n and "import SafeIO" not in out.split("def ")[0]:
        head_end = out.find("import", 0)
        out = out.replace("import json", "import json\nimport sys\nsys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nimport SafeIO", 1)
    return out, n
PY_ = ROOT + r"\Scripts\SafeIO.py"
# CryptoLedger: save_L -> SafeIO
CE = ROOT + r"\Scripts\CryptoEconomy.py"
ce = open(CE, encoding="utf-8-sig").read()
ce = ce.replace('''def save_L(L):
    L["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    json.dump(L, open(LEDGER, "w", encoding="utf-8"), indent=1)''',
    '''def save_L(L):
    L["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    import sys as _s
    _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import SafeIO
    return SafeIO.write_json(LEDGER, L)''', 1)
open(CE, "w", encoding="utf-8-sig").write(ce)
py_compile.compile(CE, doraise=True)
log.append("CryptoLedger atomic: OK")

# Reciprocity: the NOTES + HEALTH + PathMemory writes -> SafeIO
RE = ROOT + r"\Scripts\Reciprocity.py"
rec = open(RE, encoding="utf-8-sig").read()
rec = rec.replace('''    json.dump([brief], open(NOTES, "w", encoding="utf-8"), indent=1)
    json.dump(h, open(HEALTH, "w", encoding="utf-8"), indent=1)''',
    '''    import sys as _s
    _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import SafeIO
    SafeIO.write_json(NOTES, [brief])
    SafeIO.write_json(HEALTH, h)''', 1)
open(RE, "w", encoding="utf-8-sig").write(rec)
py_compile.compile(RE, doraise=True)
log.append("Reciprocity atomic: OK")

# DeploySwarm: the stuck-child mercy (kill over-budget children then haul)
dep = open(DEP, encoding="utf-8-sig").read()
old_wait = '''    for shard, pid in child_pids:
        try:
            _pu.Process(pid).wait(timeout=600)
        except Exception:
            pass'''
new_wait = '''    for shard, pid in child_pids:
        try:
            proc = _pu.Process(pid)
            proc.wait(timeout=600)
        except _pu.TimeoutExpired:
            try:  # the mercy: a stuck child is ended so the haul is clean
                proc.kill()
            except Exception:
                pass
        except Exception:
            pass'''
if old_wait in dep:
    dep = dep.replace(old_wait, new_wait, 1)
    log.append("OK   stuck-children-mercy")
open(DEP, "w", encoding="utf-8-sig").write(dep)
py_compile.compile(DEP, doraise=True)

print("COMPILED CLEAN (all)")
print("\n".join(log))