"""CODE PROFILER - the AST-level scanner the rescan lacked (header-regex
could not see FUNCTIONS/IMPORTS/CALLS). Scans every live organ:
 - AST: functions, classes, imports, network calls (urllib/openai), the
   subprocess spawns, the lock/atomic-write discipline markers per file;
 - PYFLAKES: the undefined/unused-name warnings (quality dimension);
 - BANDIT: the security lint flags (already resident in the venv);
 - THE INSTALLED TOOLS: pip freeze -> Config/tools_installed.json (the
   omnivore law: everything on the box, receipted).
TEST GATE: (a) >=60 organs AST-parsed, (b) pyflakes+bandit run and counted,
(c) the tools inventory written (>=30 packages), (d) read-only + report.
"""
import ast
import json
import os
import re
import subprocess
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
S = os.path.join(ROOT, "Scripts")
OUT = os.path.join(ROOT, "Config", "code_profile.json")
TOOLS_OUT = os.path.join(ROOT, "Config", "tools_installed.json")


def profile_one(path):
    src = open(path, encoding="utf-8-sig", errors="replace").read()
    try:
        tree = ast.parse(src)
        funcs = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    for n in ast.walk(tree))
        classes = sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
        imports = [n.names[0].name for n in ast.walk(tree)
                   if isinstance(n, (ast.Import, ast.ImportFrom))
                   and n.names][:8]
    except Exception as e:
        return {"file": os.path.basename(path), "parse_error": str(e)[:60]}
    has_net = "urllib.request" in " ".join(imports)
    has_subp = "subprocess" in src
    has_lock = "locking" in src or "msvcrt" in src or "SafeIO" in src
    return {"file": os.path.basename(path), "lines": src.count("\n") + 1,
            "funcs": funcs, "classes": classes,
            "imports": imports,
            "net_calls": has_net, "spawns": has_subp,
            "locked_writes": has_lock}


def lint():
    """pyflakes + bandit over Scripts (skip Attic/venv): counted warnings."""
    targets = [os.path.join(S, f) for f in os.listdir(S) if f.endswith(".py")]
    out = {"pyflakes": {}, "bandit": {}}
    try:
        r = subprocess.run([sys.executable, "-m", "pyflakes"] + targets,
                           capture_output=True, text=True, encoding="utf-8",
                           timeout=120)
        warns = (r.stdout or "").strip().splitlines()
        out["pyflakes"] = {"n_organs_flagged": len(set(w.split("'")[0]
                               .split("(")[0].strip(":") for w in warns if w)),
                           "n_warnings": len(warns),
                           "sample": warns[:5]}
    except Exception as e:
        out["pyflakes"] = {"error": str(e)[:60]}
    try:
        r = subprocess.run([sys.executable, "-m", "bandit", "-q", "-r",
                            S, "--skip", "B101,B404,B603,B105,B110,Btry"],
                           capture_output=True, text=True, encoding="utf-8",
                           timeout=180)
        m = re.search(r"(Total issues[^\n]*)", r.stdout or "")
        out["bandit"] = {"summary": (m.group(1) if m else
                                     (r.stdout or "").strip()[-200:]),
                         "rc": r.returncode}
    except Exception as e:
        out["bandit"] = {"error": str(e)[:60]}
    return out


def tools_inventory():
    r = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                       capture_output=True, text=True, encoding="utf-8",
                       timeout=120)
    pkgs = [x.strip() for x in (r.stdout or "").splitlines() if "==" in x]
    with open(TOOLS_OUT, "w", encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "python": sys.version.split()[0],
                   "packages": len(pkgs), "list": pkgs,
                   "note": "the omnivore tool law: everything installed, "
                           "$0, receipted"}, f, indent=1)
    return pkgs


def selftest():
    print("=== CODE PROFILER'S OWN GATE ===")
    legs = []
    files = [os.path.join(S, f) for f in os.listdir(S) if f.endswith(".py")
             and not f.startswith("_")]
    profs = [profile_one(p) for p in files]
    ok_a = len(profs) >= 60 and sum(1 for p in profs if "parse_error" in p) <= 2
    print(f"   (a) AST: {len(profs)} organs profiled "
          f"({sum(1 for p in profs if 'parse_error' in p)} parse errors): {ok_a}")
    legs.append(("ast_inventory", ok_a))
    ln = lint()
    ok_b = ("error" not in ln["pyflakes"]) and ("error" not in ln["bandit"])
    print(f"   (b) pyflakes: {ln['pyflakes'].get('n_warnings', '?')} warnings "
          f"on {ln['pyflakes'].get('n_organs_flagged', '?')} organs | bandit: "
          f"{str(ln['bandit'].get('summary', ln['bandit'].get('error', '?')))[:90]}"
          f" -> {ok_b}")
    legs.append(("linters_ran", ok_b))
    pkgs = tools_inventory()
    ok_c = len(pkgs) >= 30 and os.path.exists(TOOLS_OUT)
    print(f"   (c) tools inventory: {len(pkgs)} packages receipted: {ok_c}")
    legs.append(("tools_receipted", ok_c))
    # (d) the profile report written + spot-check a known organ
    doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "organs": profs, "lint": ln, "tools_installed": len(pkgs),
           "py": sys.version.split()[0]}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    os.replace(tmp, OUT)
    spot = next((p for p in profs if p["file"] == "GenePool.py"), {})
    ok_d = spot.get("funcs", 0) >= 5 and os.path.exists(OUT)
    print(f"   (d) report written; GenePool spot-check: {spot.get('funcs')}")
    legs.append(("report_valid", ok_d))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[profiler] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)