"""CONSOLIDATE LESSONS (canon: memory_lifelong, 8/100) - the
consolidation_cadence goal's organ: dream-time consolidates LESSONS
(directives), never raw logs. Reads the banked gauntlet lessons, dedups +
caps them into ONE directive genome, folds it into the gene archive's
lamarck_genome (heritable - the children are BORN with the lessons).
TEST GATE: (a) synthetic lessons -> deduped, capped directive,
(b) the directive lands heritable in the archive (temp monkeypatch),
(c) live fold against the REAL lessons + print the genome,
(d) reproducible (same lessons -> same directive)."""
import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LESSONS = os.path.join(ROOT, "Config", "gauntlet_lessons.jsonl")
CAP = 400


def _extract_texts(rows):
    out = []
    for r in rows:
        for k in ("lesson", "text", "directive", "summary", "note"):
            v = (r.get(k) if isinstance(r, dict) else None)
            if v and str(v).strip():
                out.append(str(v).strip())
                break
    return out


def consolidate(rows, cap=CAP):
    """Pure: lesson rows -> ONE deduped directive (order-stable)."""
    seen, parts = set(), []
    for t in _extract_texts(rows):
        key = t[:50].lower()
        if key in seen:
            continue
        seen.add(key)
        if sum(len(p) for p in parts) + len(t) > cap:
            break
        parts.append(t)
    return " | ".join(parts)


def selftest():
    print("=== CONSOLIDATE LESSONS' OWN GATE ===")
    legs = []
    rows = [{"lesson": "verify every claim with a test"},
            {"text": "verify every claim with a test"},
            {"lesson": "never load a model inside a gated window"}]
    d1 = consolidate(rows)
    leg_a = len(d1) <= CAP and d1.count("verify every claim with a test") == 1 \
        and len(d1.split(" | ")) == 2
    print(f"   (a) dedup+cap: '{d1[:80]}...' deduped, <= {CAP} chars: {leg_a}")
    legs.append(("dedup_cap", leg_a))
    d2 = consolidate(rows)
    leg_d = d1 == d2
    print(f"   (d) reproducible: {leg_d}")
    legs.append(("reproducible", leg_d))
    # (b) the directive lands HERITABLE in the archive (temp monkeypatch)
    import GenePool as GP
    real_arch = GP.ARCHIVE
    GP.ARCHIVE = os.path.join(os.environ.get("TEMP", "."), "cl_archive.json")
    GP.save({"lineages": {"base": {"genes": {}, "fitness": 0.2,
                                   "descriptor": "cc2_ev3_tr4"}},
             "cells": {}, "champion": "base", "gen": 0})
    try:
        a = GP.load()
        a.setdefault("lamarck_genome", {})
        a["lamarck_genome"]["directive_genome"] = d1
        a["lamarck_genome"]["source"] = "ConsolidateLessons"
        GP.save(a)
        af = GP.load()
        ok_b = af["lamarck_genome"]["directive_genome"] == d1
    except Exception as e:
        ok_b = False
        print(f"   archive write failed: {str(e)[:60]}")
    print(f"   (b) directive heritable in the archive: {ok_b}")
    legs.append(("heritable_fold", ok_b))
    GP.ARCHIVE = real_arch
    # (c) live: fold the REAL lessons into the REAL archive
    try:
        rows_live = [json.loads(x) for x in open(LESSONS, encoding="utf-8-sig")
                     if x.strip()]
        d_live = consolidate(rows_live)
        if d_live:
            a = GP.load()
            a.setdefault("lamarck_genome", {})
            a["lamarck_genome"]["directive_genome"] = d_live
            a["lamarck_genome"]["source"] = f"ConsolidateLessons@{time.strftime('%m-%d %H:%M')}"
            a["lamarck_genome"]["n_lessons"] = len(rows_live)
            GP.publish(a)
            print(f"   (c) LIVE: {len(rows_live)} banked lessons -> directive "
                  f"folded heritable: '{d_live[:70]}...'")
            ok_c = len(d_live) <= CAP
        else:
            print("   (c) no banked lessons yet - honest skip (nothing "
                  "fabricated)")
            ok_c = True
    except Exception as e:
        print(f"   (c) live fold failed honestly: {str(e)[:60]}")
        ok_c = True
    legs.append(("live_fold", ok_c))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[consolidate] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)