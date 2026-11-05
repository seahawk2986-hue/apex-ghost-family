"""Scriptorium - the script census + quarantine (2026-11-04, hygiene organ).

LAW-COMPLIANT: nothing deleted. Debris is MOVED to Scripts/Attic/Quarantine/
(reversible; every move is receipted). Classification is by EVIDENCE:
  LIVE = name appears in a workflow .yml, in another script, in an Apel
  scheduled-task XML, is a workflow-import dependency, or is fresh (<45d).
  DEBRIS = none of the above AND matches the one-off naming patterns.

Outputs:
  Scripts/MANIFEST.md   - the full census table (instrument OR debris tag)
  Config/scriptorium.jsonl - per-run receipt
"""
import json, os, re, time, shutil, subprocess

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
SCR = os.path.join(ROOT, "Scripts")
QUAR = os.path.join(SCR, "Attic", "Quarantine")
TASKS = r"C:\Windows\System32\Tasks"
RECEIPT = os.path.join(ROOT, "Config", "scriptorium.jsonl")
FRESH = 45 * 86400

WFS = ["_runner_prfile", "Apex10Loop", "CapabilityRescan", "ClaimCheck",
       "CodeProfiler", "DemoDesk", "EarnLaneMatrix", "FeatureLedger",
       "FleetDoctor", "GeneralIntellectFitness", "NodeDesk", "PrWatch",
       "Reinforce", "RoleMarket", "SourcingDesk", "SwarmCert", "SWEProbe",
       "VetLineRemote"]

def main():
    t0 = time.time()
    scripts = sorted(f[:-3] for f in os.listdir(SCR)
                     if f.endswith(".py") and not f.startswith("_"))

    # one-pass referencer corpus: every .py OUTSIDE Scripts + every yml
    refs = {}          # stem -> set of referencing files
    def note(name, where):
        refs.setdefault(name, set()).add(where)

    for dirp, subds, files in os.walk(ROOT):
        subds[:] = [d for d in subds
                    if d not in {".git", "training_venv", "venv", "node_modules",
                                 "apex_venv", "Attic", "__pycache__", ".opencode",
                                 "Scripts"}]
        for fn in files:
            if fn.endswith((".py", ".yml", ".yaml", ".vbs", ".cmd", ".json",
                            ".jsonl", ".md", ".txt", ".ps1", ".bat", ".html",
                            ".js", ".toml")):
                where = fn
                txt = open(os.path.join(dirp, fn), encoding="utf-8",
                           errors="ignore").read()
                for s in scripts:
                    if s in txt:
                        note(s, where)

    # scheduled task XMLs via user-level query (System32 listdir = denied)
    task_txt = ""
    try:
        cp = subprocess.run(["schtasks", "/Query", "/FO", "LIST", "/V"],
                            capture_output=True, text=True, errors="ignore",
                            timeout=180)
        task_txt = cp.stdout or ""
    except Exception:
        task_txt = ""    # the census classifies by other evidence then

    rows, moved = [], []
    now = time.time()
    ORPHANS_GO = os.environ.get("QUARANTINE_ORPHANS") == "1"
    os.makedirs(QUAR, exist_ok=True)
    for f in sorted(os.listdir(SCR)):
        if not f.endswith(".py") or f.startswith("_scriptorium"):
            continue
        stem = f[:-3]
        p = os.path.join(SCR, f)
        mtime = os.path.getmtime(p)
        fresh = (now - mtime) < FRESH
        in_wf = stem in WFS
        ref_files = refs.get(stem, set())
        in_task = (stem + ".py") in task_txt or stem in task_txt
        imported = False
        # import-form check inside Scripts itself (other organs importing it)
        for other in os.listdir(SCR):
            if not (other.endswith(".py")) or other == f or other.startswith("Attic"):
                continue
            try:
                t = open(os.path.join(SCR, other), encoding="utf-8",
                         errors="ignore").read()
            except OSError:
                continue
            if re.search(r"^\s*(import|from)\s+" + re.escape(stem) + r"\b", t,
                         re.MULTILINE):
                imported = True
                break

        live = bool(in_wf) or bool(in_task) or imported or bool(ref_files)
        debris_pat = (f.startswith("_fix") or f.startswith("_probe")
                      or f.startswith("_acceptance") or f.startswith("_try"))
        cls = "INSTRUMENT" if live else ("SUSPECT" if debris_pat else "UNREFERENCED")
        if (not live) and debris_pat and not fresh:
            dst = os.path.join(QUAR, f)
            shutil.move(p, dst)
            moved.append(f)
            cls = "QUARANTINED"
        elif ORPHANS_GO and cls == "UNREFERENCED" and not fresh:
            # THE FRESH GUARD (added after the 217 roll-back): a file
            # younger than 45 days is presumed intended work, no matter
            # how quiet the referencer corpus is.
            dst = os.path.join(QUAR, f)
            shutil.move(p, dst)
            moved.append(f)
            cls = "QUARANTINED-ORPHAN"
        rows.append((f, cls, int(now - mtime) // 86400,
                     sorted(ref_files)[:2]))

    # manifest
    counts = {}
    for _, c, _, _ in rows:
        counts[c] = counts.get(c, 0) + 1
    with open(os.path.join(SCR, "MANIFEST.md"), "w", encoding="utf-8") as f:
        f.write("# THE SCRIPTORIUM - script census (auto)\n\n"
                "Evidence classes: INSTRUMENT (referenced by workflow/task/"
                "importer), SUSPECT (one-off `_fix*` pattern, unreferenced), "
                "UNREFERENCED (orphan), QUARANTINED (moved to Attic - "
                f"reversible, nothing deleted).\n\n"
                f"Totals: {json.dumps(counts)}\n\n"
                "| script | class | age_days | referenced-by |\n|---|---|---|---|\n")
        for fn, c, age, rf in rows:
            f.write(f"| {fn} | {c} | {age} | {', '.join(rf) if rf else '-'} |\n")

    with open(RECEIPT, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "scripts": len(rows), "counts": counts,
                            "quarantined": moved,
                            "secs": round(time.time() - t0, 1)}) + "\n")
    print(f"[scriptorium]: {len(rows)} scripts; {json.dumps(counts)}; "
          f"quarantined {len(moved)}: {moved}")

def glob_tasks():
    out = []
    base = os.path.join(TASKS)
    for tn in os.listdir(base):
        if tn.upper().startswith("APEX"):
            out.append(os.path.join(base, tn))
    return out

if __name__ == "__main__":
    main()
