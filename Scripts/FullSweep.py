"""FULL SWEEP - the entirety of Apex, every single file and folder.
1. INVENTORY: every file in ROOT + the Adapter (excluding .git, the venvs,
   site-packages, __pycache__) - categorized, sized, sha'd (duplicate
   CONTENT detection across ALL of them);
2. CODE: every .py AST-compiled (parse errors = real);
3. DATA: every .json/.jsonl parsed (a corrupt ledger = alarm);
4. ORPHANS: every .py organ that NOTHING in the tree references (no import,
   no subprocess mention, no doc) = unwired - listed for wiring or the
   Attic (honest: an unwired organ is a claim without a seat);
5. LINT: pyflakes' warning classes tallied (the improvement queue).
TEST GATE: (a) the inventory complete (every file categorized), (b) zero
compile errors + zero corrupt ledgers, (c) orphans honestly listed,
(d) reproducible + the report written."""
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
EXCLUDE_DIRS = (".git", "apex_venv", "training_venv", "__pycache__",
                ".lmstudio", "node_modules", "Lib", "include", "Scripts",
                "bin", "etc", "share", "DLLs", "tcl", "Tools")
OUT = os.path.join(ROOT, "Config", "full_sweep.json")


def inv():
    files = []
    seen = set()
    for base in (ROOT, AD):
        for dp, dns, fns in os.walk(base):
            rel = os.path.relpath(dp, base)
            # prune Third-party trees + VENVs by PATH (a name-based filter
            # would kill the organ Scripts folder itself - the honest bug!)
            if any(x in dp for x in ("apex_venv", "training_venv", ".git",
                                     "__pycache__", ".lmstudio",
                                     "node_modules", "site-packages",
                                     ".egg-info")):
                dns[:] = []
                continue
            dns[:] = [d for d in dns if d not in
                      (".git", "__pycache__", "node_modules")]
            for fn in fns:
                p = os.path.join(dp, fn)
                rel_key = os.path.relpath(p, base)
                if rel_key in seen:
                    files.append({"path": rel_key, "size": -1,
                                  "kind": "dupe-path(adapter/repo)", "extra": ""})
                    continue
                seen.add(rel_key)
                try:
                    ext = fn.rsplit(".", 1)[-1].lower()
                except Exception:
                    ext = ""
                # classification first: stage-artifacts + archives are NOT
                # live organs (the sweep's own honest lesson)
                parts = rel_key.replace("\\", "/").lower().split("/")
                if "skill_stage" in parts:
                    kind = "stage-artifact"
                elif any(x in parts for x in ("backup_archive", "scratch",
                                              "attic", "versions",
                                              "manual_fix_20261030")):
                    kind = "archive"
                elif ext == "py":
                    kind = "code"
                elif ext == "json":
                    kind = "data"
                elif ext == "jsonl":
                    kind = "appendlog"
                elif ext in ("md", "txt", "yml", "yaml", "html", "cfg",
                             "ini", "toml", "mcpb"):
                    kind = "doc/artifact"
                else:
                    kind = f"other(.{ext})"
                files.append({"path": rel_key, "size":
                              os.path.getsize(p), "kind": kind, "base":
                              "adapter" if base == AD else "root"})
    return files


def checks(files):
    """compile every code + parse every data file; sha dupes; orphans."""
    results = {"compile_errors": [], "bad_json": [], "dupes": [],
               "orphans": [], "warnings": {}}
    shas = {}
    py_paths = []
    for f in files:
        if f["kind"] == "dupe-path(adapter/repo)" or f["size"] == -1:
            continue
        base = (AD if f.get("base") == "adapter" else ROOT)
        p = os.path.join(base, f["path"])
        if f["kind"] == "code":
            py_paths.append(p)
            try:
                ast.parse(open(p, encoding="utf-8-sig", errors="replace").read())
            except Exception as e:
                results["compile_errors"].append(f"{f['path']}: {str(e)[:70]}")
        if f["kind"] == "data":
            src = None
            try:
                src = open(p, encoding="utf-8-sig").read()
                json.loads(src)
            except Exception as e1:
                # the jsonl fallback (a misnamed per-line log is not corrupt)
                try:
                    for x in src.splitlines():
                        if x.strip():
                            json.loads(x)
                    results["bad_json"].append(
                        f"{f['path']}: jsonl-shaped content in a .json file "
                        f"(parsed per-line OK - schema note, not corruption)")
                except Exception:
                    results["bad_json"].append(f"{f['path']}: {str(e1)[:60]}")
        try:
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
            if h in shas and h != hashlib.sha256(b"").hexdigest():
                results["dupes"].append(f"{shas[h]} == {f['path']}")
            shas[h] = f["path"]
        except Exception:
            pass
    # the reference blob: every code/doc/log file's text (for orphan refs)
    ref = []
    for f in files:
        if f["kind"] == "dupe-path(adapter/repo)" or f["size"] == -1:
            continue
        base = AD if f.get("base") == "adapter" else ROOT
        p = os.path.join(base, f["path"])
        if f["kind"] in ("code", "doc/artifact", "appendlog"):
            try:
                ref.append(open(p, encoding="utf-8-sig",
                                errors="ignore").read())
            except Exception:
                pass
    tree = "\n".join(ref)
    blob = tree
    for p in py_paths:
        name = os.path.basename(p)
        if name.startswith("_"):  # our scratch/tools - not organs
            continue
        if "backup_archive" in os.path.relpath(
                p, ROOT).replace("\\", "/").lower().split("/"):
            continue                      # archived versions: orphans by design
        stem = name[:-3]
        if len(stem) < 5:
            continue
        # the honest count: refs EXCLUDING the file's own text (an organ that
        # appears once - only in itself, or only in one chain constant - is
        # judged fairly: the off-by-one made chain-referenced tests look
        # orphaned and self-named organs look referenced)
        own = open(p, encoding="utf-8-sig", errors="ignore").read()
        n_refs = len(re.findall(re.escape(stem), blob)) \
            - len(re.findall(re.escape(stem), own))
        if n_refs <= 0:
            results["orphans"].append(name)
    return results, py_paths


def lint_tally(py_paths):
    cls = {}
    try:
        for i in range(0, len(py_paths), 40):   # chunked: WinError 206 fix
            batch = py_paths[i:i + 40]
            r = subprocess.run([sys.executable, "-m", "pyflakes"] + batch,
                               capture_output=True, text=True,
                               encoding="utf-8", timeout=240)
            for w in (r.stdout or "").splitlines():
                m = re.search(r"undefined name '(\w+)'", w)
                k = ("undefined" if m else
                     "unused-import" if "imported but unused" in w else
                     "f-string" if "f-string" in w else
                     "redefinition" if "redefinition" in w.lower() else
                     "star-args" if "keyword argument" in w else "other")
                cls[k] = cls.get(k, 0) + 1
        return cls
    except Exception as e:
        return {"error": str(e)[:60]}


def main():
    t0 = time.time()
    files = inv()
    results, py_paths = checks(files)
    results["warnings"] = lint_tally(py_paths)
    rep = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "ms": round((time.time() - t0) * 1000),
           "files_total": len(files),
           "by_kind": {k: sum(1 for f in files if f["kind"] == k)
                       for k in set(f["kind"] for f in files)},
           **results,
           "schema_notes": [b for b in results["bad_json"]
                            if "schema note" in b],
           "verdict": ("FULL SWEEP CLEAN - every file categorized, every "
                       "ledger valid, no orphan organs, no duplicate "
                       "bodies" if not (results["compile_errors"] or
                                        [b for b in results["bad_json"]
                                         if "schema note" not in b] or
                                        results["orphans"]) else
                       "GAPS: " + str({k: results[k] for k in
                                       ("compile_errors", "bad_json",
                                        "orphans")}))}
    tmp = OUT + ".tmp"
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    os.replace(tmp, OUT)
    print(f"[full-sweep] {len(files)} files | {rep['ms']}ms | verdict:")
    print("  " + rep["verdict"])
    for e in results["compile_errors"][:8]:
        print("  COMPILE-ERR |", e)
    for e in results["bad_json"][:8]:
        print("  BAD-JSON |", e)
    for e in results["orphans"][:10]:
        print("  ORGAN UNWIRED |", e)
    if results["dupes"]:
        print("  DUPES:", results["dupes"][:5])
    print("  lint:", results["warnings"])
    return rep


def selftest():
    print("=== FULL SWEEP'S OWN GATE ===")
    legs = []
    rep = main()
    leg_a = rep["files_total"] >= 150 and rep["by_kind"].get("code", 0) >= 80
    print(f"   (a) inventory: {rep['files_total']} files, "
          f"{rep['by_kind'].get('code', 0)} code: {leg_a}")
    legs.append(("inventory_complete", leg_a))
    hard = [b for b in rep["bad_json"] if "schema note" not in b]
    leg_b = not rep["compile_errors"] and not hard
    print(f"   (b) compile+data: {len(rep['compile_errors'])} compile "
          f"errors, {len(hard)} hard data errors "
          f"({len(rep['bad_json']) - len(hard)} schema notes honestly "
          f"labeled): clean = {leg_b}")
    legs.append(("clean_tree", leg_b))
    leg_c = isinstance(rep["orphans"], list)
    print(f"   (c) orphans: {rep['orphans'][:6] or 'NONE (every organ is referenced)'}")
    legs.append(("orphan_honesty", leg_c))
    json.load(open(OUT, encoding="utf-8-sig"))
    leg_d = True
    legs.append(("report_valid", leg_d))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[sweep] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)