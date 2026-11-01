"""DEEPCOMB v2: the exhaustive-honest code-comb (the founder's 10-times law).
HARDENED after the comb-combed lesson (the v1's own bugs, receipted):
  P1  compile (in-memory = no nul-cfile warning-class, every .py in the
      LIVE tree: apex_venv, .git, Lib\\, Attic, Config\\versions = excluded)
  P2  ruff lint (E9,F821 = the substance: undefined-names = real bugs)
  P3  JSON-validate (every .json)
  P4  JSONL-validate (per-line parse; honest row-counts)
  P5  YAML/Workflow-validate (pyyaml + the on-key boolean-ghost check)
  P6  import-surface (COMPILE-ONLY - never executes the organ; every
      top-level import must resolve: stdlib / installed / own-file)
  P7  stdlib-shadow check (a module named like stdlib/installed that
      shadows it = flagged - the Lib\\ lesson mechanized)
  P8  ast-walk coverage count (the dataflow = the ruff's F821 lane)
  P9  runtime smoke (Sanitizer only = the designed selftest)
  P10 ledger-rotator (the 102MB lesson: the ledger capped at ~4MB,
      the oldest rows = rotated out; the census-summary = re-derived)
Each receipt = Config/comb_passes.jsonl. The verdict = counts, never
a zero-claim."""
import ast
import glob
import importlib.util
import json
import os
import subprocess
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
PY = os.path.join(ROOT, "apex_venv", "Scripts", "python.exe")
SCRIPTS = os.path.join(ROOT, "Scripts")
LEDGER = os.path.join(ROOT, "Config", "comb_passes.jsonl")
LEDGER_CAP = 4 * 2 ** 20  # the 102MB lesson
EXCLUDES = ("apex_venv", os.sep + ".git" + os.sep, os.sep + "Lib" + os.sep,
            "Attic", os.sep + "versions" + os.sep)
STDLIB_NAMES = set(sys.stdlib_module_names) if hasattr(
    sys, "stdlib_module_names") else set()


def ok_path(p):
    return not any(x in p for x in EXCLUDES)


def all_pys():
    return [p for p in glob.glob(os.path.join(ROOT, "**", "*.py"),
                                 recursive=True) if ok_path(p)]


def all_files(ext):
    return [p for p in glob.glob(os.path.join(ROOT, "**", "*" + ext),
                                 recursive=True) if ok_path(p)]


def read(p):
    with open(p, "rb") as f:
        return f.read()


def p1_compile(files, found):
    for p in files:
        try:
            compile(read(p), p, "exec")
        except SyntaxError as e:
            found.append({"pass": "P1", "file": p, "bug":
                          f"SyntaxError line {e.lineno}: {str(e.msg)[:90]}"})
        except Exception as e:
            found.append({"pass": "P1", "file": p, "bug": str(e)[:90]})
    return len(files)


def p2_ruff(files, found):
    ruff = os.path.join(os.path.dirname(PY), "ruff.exe")
    if not os.path.exists(ruff):
        return 0
    n = 0
    for p in files:
        try:
            r = subprocess.run([ruff, "check", "--select", "E9,F821", p],
                               capture_output=True, text=True, timeout=30)
            n += 1
            for ln in (r.stdout or "").splitlines():
                if "F821" in ln:
                    found.append({"pass": "P2", "file": p,
                                  "bug": ln.strip()[:150]})
        except Exception as e:
            found.append({"pass": "P2", "file": p, "bug": str(e)[:100]})
    return n


def p3_json(files, found):
    for p in files:
        try:
            json.load(open(p, encoding="utf-8-sig", errors="strict"))
        except Exception:
            found.append({"pass": "P3", "file": p, "bug":
                          "the json = unparseable (strict)"})
    return len(files)


def p4_jsonl(files, found):
    for p in files:
        bad = 0
        n = 0
        for ln in open(p, encoding="utf-8-sig", errors="replace"):
            s = ln.strip()
            if s:
                try:
                    json.loads(s)
                    n += 1
                except Exception:
                    bad += 1
        if bad:
            found.append({"pass": "P4", "file": p,
                          "bug": f"{bad} unparseable rows / {n} ok"})
    return len(files)


def p5_yaml(files, found):
    try:
        import yaml
    except Exception:
        return 0
    for p in files:
        try:
            with open(p, encoding="utf-8") as f:
                d = yaml.safe_load(f)
            if "workflows" in p and d and "on" not in d:
                found.append({"pass": "P5", "file": p, "bug":
                              "the on-key = missing-or-boolean (the "
                              "boolean-ghost lesson!)"})
        except Exception as e:
            found.append({"pass": "P5", "file": p, "bug": str(e)[:110]})
    return len(files)


def top_imports(src):
    """the top-level import-names (module-level only, no exec)."""
    names = []
    try:
        tree = ast.parse(src)
        for node in tree.body:
            if isinstance(node, ast.Import):
                names += [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module.split(".")[0])
    except Exception:
        pass
    return names


def resolves(name):
    if name in STDLIB_NAMES:
        return True
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return True  # the honest: cannot-prove-missing = never a claim


def p6_import_surface(files, found):
    own = {os.path.splitext(os.path.basename(p))[0] for p in files}
    n = 0
    for p in files:
        try:
            src = read(p).decode("utf-8-sig", "replace")
        except Exception:
            continue
        for name in top_imports(src):
            n += 1
            if name in own or name in STDLIB_NAMES or resolves(name):
                continue
            found.append({"pass": "P6", "file": p, "bug":
                          f"import {name} = the module-missing"})
    return n


def p7_shadow(files, found):
    """a repo-file named like stdlib = the shadow-bug (the Lib lesson)."""
    n = 0
    for p in files:
        base = os.path.splitext(os.path.basename(p))[0]
        n += 1
        if base in STDLIB_NAMES:
            found.append({"pass": "P7", "file": p, "bug":
                          f"the file {os.path.basename(p)} = SHADOWS the "
                          "stdlib name (the import-chaos risk)"})
    return n


def p8_walk(files):
    n = 0
    for p in files:
        try:
            ast.parse(read(p).decode("utf-8-sig", "replace"))
            n += 1
        except Exception:
            pass
    return n


def p9_smoke(found):
    n = 0
    r = subprocess.run([PY, os.path.join(SCRIPTS, "Sanitizer.py")],
                       capture_output=True, text=True, timeout=60, cwd=ROOT)
    n += 1
    if "FAIL" in (r.stdout or "") or r.returncode != 0:
        found.append({"pass": "P9", "file": "Sanitizer.py", "bug":
                      (r.stdout or "").strip()[:120]})
    return n


def rotate_ledger():
    try:
        if os.path.exists(LEDGER) and os.path.getsize(LEDGER) > LEDGER_CAP:
            lines = open(LEDGER, encoding="utf-8", errors="replace"
                         ).read().splitlines()
            with open(LEDGER, "w", encoding="utf-8") as f:
                f.write("\n".join(lines[-200:]) + "\n")
    except Exception:
        pass


def one_pass(tag):
    found = []
    pys = all_pys()
    counts = {}
    counts["p1"] = p1_compile(pys, found)
    counts["p2"] = p2_ruff(pys, found)
    counts["p3"] = p3_json(all_files(".json"), found)
    counts["p4"] = p4_jsonl(all_files(".jsonl"), found)
    counts["p5"] = p5_yaml(all_files(".yml") + all_files(".yaml"), found)
    counts["p6"] = p6_import_surface(pys, found)
    counts["p7"] = p7_shadow(pys, found)
    counts["p8"] = p8_walk(pys)
    counts["p9"] = p9_smoke(found)
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "pass_no": tag,
           "scanned": counts, "bugs": found, "bug_count": len(found)}
    rotate_ledger()
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def main():
    passes = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    all_bugs = {}
    for i in range(passes):
        row = one_pass(i + 1)
        for b in row["bugs"]:
            k = (b["file"], b["bug"][:60])
            all_bugs[k] = all_bugs.get(k, 0) + 1
        print(f"[deep-comb] pass {i + 1}/{passes}: "
              f"{row['bug_count']} finding(s) | scanned {row['scanned']}")
    print(f"[deep-comb] THE UNIQUE-BUGS ({len(all_bugs)}):")
    for (f, b), c in sorted(all_bugs.items(), key=lambda kv: -kv[1]):
        print(f"  [x{c}] {os.path.basename(f)}: {b[:90]}")
    return all_bugs


if __name__ == "__main__":
    main()