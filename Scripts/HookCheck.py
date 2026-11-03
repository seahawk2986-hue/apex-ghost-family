"""HookCheck - THE INTEGRATION TRIPWIRE (2026-11-04).

THE MEASURED ATTACK-CLASS (from tonight's forensics): the family's own
re-issue machinery (the healer's full-rewrite fallback / the rebase dance)
silently REVERTS integration hooks - the organs' hooks vanished from
ApexDream.py and receipts_page.py between edit and commit, committed by
the honest `add -A`. Nothing was malicious; hooks still vanished.

THE TRIPWIRE: a MANIFEST of required marker-lines per integration file.
Every sentry fire (1-min cadence, 30-min cooldown on any repair): check;
a missing marker = HONEST ALARM (episodic) + an automatic re-install via
the manifest's PATCH (a SEARCH/REPLACE instruction the checker executes
itself, idempotently guarded by the marker itself).
The manifest is data - extending the family means extending a JSON.
$0; stdlib; sub-second."""
import io
import json
import os
import sys
import time

if getattr(sys.stdout, "apex_wrapped", False) is False:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.stdout.apex_wrapped = True

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
CD = os.path.join(REPO, "Logs", "hookcheck_cooldown.txt")
MANIFEST = {
    "Scripts/ApexDream.py": [
        {"marker": "import LocalGym as _lg",
         "anchor": 'm.record_event("training", "night organs: " + ", ".join(_organ_notes))',
         "insert": ("""    try:
        import LocalGym as _lg
        _lg.grade_brain()
        _organ_notes.append("the serving floor graded on the sealed pocket")
    except Exception as _e_lg:
        m.record_event("local_mind", "local-gym skipped honestly: " + str(_e_lg)[:70])
    try:
        import Recall2 as _r2
        _r2.append_delta()
        _organ_notes.append("recall2 index delta-applied")
    except Exception:
        pass
    try:
        import HorizonLadder as _hl
        _hl.measure()
        _organ_notes.append("the autonomy horizon measured")
    except Exception as _e_hl:
        m.record_event("horizon", "ladder skipped honestly: " + str(_e_hl)[:70])
    try:
        import CertifyBridge as _cb
        _n = _cb.certify()
        _organ_notes.append(f"certify-bridge earned {len(_n)} execution-seats")
    except Exception as _e_cb:
        m.record_event("certification", "certify-bridge skipped honestly: " + str(_e_cb)[:70])
    try:
        import FilingBridge as _fb
        _doc = _fb.prepare()
        _organ_notes.append(f"filing-batch prepared ({_doc.get('batch_size', 0)} rows)")
    except Exception as _e_fb:
        m.record_event("filing_bridge", "filing-bridge skipped honestly: " + str(_e_fb)[:70])
    """)},
        {"marker": "import OutputYardstick as _y", "skip": True},
    ],
    "receipts_page.py": [
        {"marker": "local_mind.json", 
         "anchor": "return HTMLResponse(f\"\"\"<!doctype html>",
         "insert": ("""    # THE SERVING-BRAIN REPORT (2026-11-04 GI-round)
    lm = _json(os.path.join(R, "Config", "local_mind.json"))
    if lm:
        yard += (f"<div class='kv'>the serving floor: <b>{_esc(lm.get('brain'))}</b> "
                 f"scored <b>{_esc(lm.get('acc'))}%</b> on the SAME sealed "
                 f"pocket ({_esc(lm.get('n'))} drills, same ruler) - the "
                 f"fallback's real capability, published</div>")
    # THE AUTONOMY HORIZON (2026-11-04, the METR-analog receipt)
    hz = _json(os.path.join(R, "Config", "horizon.json"))
    if hz:
        yard += (f"<div class='kv'>the autonomy horizon: <b>{_esc(hz.get('steps'))} "
                 f"steps/{_esc(hz.get('minutes'))} min</b> at "
                 f"{_esc(hz.get('completion'))} completion ({_esc(hz.get('trend'))}) - "
                 f"the METR-analog from the family's own ledgers</div>")

    """)},
    ],
}


def check_and_repair():
    try:
        if os.path.exists(CD):
            last = open(CD, encoding="utf-8").read().strip()
            if time.strftime("%Y-%m-%d %H:%M") in last[:16] and \
                    time.time() - time.mktime(time.strptime(last, "%Y-%m-%d %H:%M:%S")) < 1800:
                return "cooldown"
    except Exception:
        pass
    repaired, alarmed = [], []
    for rel, hooks in MANIFEST.items():
        p = os.path.join(REPO, rel)
        if not os.path.isfile(p):
            continue
        try:
            t = open(p, encoding="utf-8-sig").read()
        except Exception:
            continue
        for h0 in hooks:
            if h0.get("skip"):
                continue
            mk = h0["marker"]
            if mk in t:
                continue
            anchor = h0.get("anchor", "")
            insert = h0.get("insert", "")
            idx = t.find(anchor)
            if idx == -1 or not insert:
                alarmed.append(f"{rel}: MARKER MISSING ({mk[:40]}); anchor absent - manual repair needed")
                continue
            t2 = t[:idx] + insert + t[idx:]
            tmp = p + ".hookcheck.tmp"
            with open(tmp, "w", encoding="utf-8", newline="") as f:
                f.write(t2)
            os.replace(tmp, p)
            repaired.append(f"{rel}: {mk[:40]} re-installed")
            t = t2
    if repaired or alarmed:
        try:
            with open(os.path.join(REPO, "memory_episodic.jsonl"), "a",
                      encoding="utf-8") as f:
                f.write(json.dumps({"id": os.urandom(6).hex(),
                                    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "kind": "hookcheck",
                                    "text": "TRIPWIRE: " + "; ".join(
                                        repaired + alarmed)[:400],
                                    "meta": {}, "imp": 0.9},
                                   ensure_ascii=False) + "\n")
        except Exception:
            pass
        with open(CD, "w", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S"))
    for r0 in repaired:
        print("[tripwire]", r0)
    for a0 in alarmed:
        print("[tripwire ALARM]", a0)
    return {"repaired": repaired, "alarmed": alarmed}


if __name__ == "__main__":
    check_and_repair()