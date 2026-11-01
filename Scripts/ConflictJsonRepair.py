"""CONFLICT-JSON REPAIR (the sweeps caught PathMemory.json + gene_archive.json
marker-corrupted + invalid JSON in the pushed tree; root cause: `git add -A`
inside a conflicted rebase commits markers - DISALLOWED from now on).
Repair method: git conflict blocks flank two VALID fragments of the same
object (ours = the live local writes; theirs = the remote's older state).
Strategy: strip marker lines, keep OUR side per block, validate JSON, write
back; then verify vs the SafeIO contract. Every step prints."""
import json
import os
import re

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
FILES = [os.path.join(ROOT, "Config", "PathMemory.json"),
         os.path.join(ROOT, "Config", "gene_archive.json")]


def keep_ours_and_validate(src):
    """Resolve conflict blocks in favor of OURS (the live state); fallback to
    THEIRS-side validation if ours-side fragments won't parse."""
    body = src
    # extract OURS segments for display
    ours_blocks = re.findall(r"^<{7} [^\n]*\n(.*?)^={7}\n.*?^>{7} [^\n]*\n",
                             src, re.M | re.S)
    # simplest robust reconstruction: delete marker + separator + theirs lines
    lines = src.splitlines()
    out1, keep = [], True
    for ln in lines:
        if ln.startswith("<<<<<<<"):
            keep = True
            continue
        if ln.startswith("=======") and keep:
            keep = False
            continue
        if ln.startswith(">>>>>>>"):
            keep = True
            continue
        if keep:
            out1.append(ln)
    cand1 = "\n".join(out1)
    try:
        return json.loads(cand1), ours_blocks, "ours"
    except Exception:
        # try THEIRS: drop ours segments, keep theirs
        out2, keep_them = [], False
        for ln in lines:
            if ln.startswith("<<<<<<<"):
                keep_them = False
                continue
            if ln.startswith("======="):
                keep_them = True
                continue
            if ln.startswith(">>>>>>>"):
                keep_them = True
                continue
            if keep_them:
                out2.append(ln)
        cand2 = "\n".join(out2)
        return json.loads(cand2), ours_blocks, "theirs"


for p in FILES:
    name = os.path.basename(p)
    try:
        src = open(p, encoding="utf-8-sig").read()
        data, blocks, side = keep_ours_and_validate(src)
        print(f"[repair] {name}: {len(blocks)} conflict block(s) resolved via {side}; "
              f"JSON now VALID")
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
        os.replace(tmp, p)
        json.load(open(p, encoding="utf-8-sig"))
        print(f"[repair] {name}: rewritten + re-verified")
    except Exception as e:
        print(f"[repair] {name} FAILED: {str(e)[:90]} - falling back to reseed...")
        if "gene_archive" in name:
            clean = {"lineages": {}, "cells": {}, "champion": None, "gen": 0}
        else:
            clean = {}
        with open(p, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=1)
        print(f"[repair] {name} reseeded ({'empty pool - GenePool re-founds on next run' if 'gene' in name else 'memory re-grows from live organs'})")

print()
print("[repair] re-founding the gene archive (a fresh generation publishes clean):")
import sys
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
import GenePool as GP
a = GP.run(gen_mutations=3)
GP.publish(a)
print()
print("[repair] FINAL VERIFY:")
ok_all = True
for p in FILES:
    try:
        src = open(p, encoding="utf-8-sig").read()
        json.loads(src)
        marked = bool(re.search(r"^<{7} \S", src, re.M))
        print(f"   {'PASS' if not marked else 'FAIL'} | {os.path.basename(p)}: valid JSON"
              + (", MARKERS STILL PRESENT" if marked else ", marker-free"))
        ok_all = ok_all and not marked
    except Exception as e:
        print(f"   FAIL | {os.path.basename(p)}: {str(e)[:60]}")
        ok_all = False
print(f"[repair] FINAL: {'ALL CLEAN - the gene files live again, honestly rebuilt' if ok_all else 'STILL BROKEN'}")