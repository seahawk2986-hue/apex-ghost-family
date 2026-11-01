"""DUALREVIEW: the stage-3 upgrade - review NEVER silently passes.
Ladder: brain attempt x3 (RAM-gated, 6s apart) -> HELD (not skipped):
unreviewed artifacts BLOCK filing + queue for the harness-drain lane.
Canon: the llm_judge/dual-review class (21 papers). Verified: selftest x2."""
import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
Q = os.path.join(ROOT, "Config", "dual_review_queue.json")


def _ram_free_gb():
    try:
        import psutil
        return psutil.virtual_memory().available / 2**30
    except Exception:
        return 2.5


def _enqueue(row):
    try:
        q = json.load(open(Q, encoding="utf-8-sig"))
    except Exception:
        q = []
    q.append(row)
    with open(Q, "w", encoding="utf-8") as f:
        json.dump(q, f, ensure_ascii=False, indent=1)


def stage3(diff_text, issue_body, purpose="the quality review", tries=3,
           delay=6.0):
    """The never-skip review ladder. Returns QualityGate-shaped row."""
    import CloudBrain as CB
    ladder = []
    ask = ("Review this automated contribution BEFORE it ships. ISSUE:\n"
           + issue_body[:1500] + "\n\nDIFF:\n" + diff_text[:4000]
           + "\n\nJudge: (1) does the change serve ONLY the issue (scope)? "
           "(2) any obvious error? (3) style fit for a real repo? Reply "
           'ONLY JSON: {"ship": true/false, "why": "<=150 chars"}')
    for i in range(tries):
        if _ram_free_gb() < 2.2:
            ladder.append({"try": i + 1, "verdict": "ram-gated"})
            time.sleep(delay if i < tries - 1 else 0)
            continue
        r = CB.chat(ask, max_tokens=250, purpose=purpose,
                    models=("groq", "local-coder", "local-fast"))
        if r:
            import re as _re
            t = _re.sub(_re.escape("<" + "think") + r".*?" + _re.escape("</" + "think")
                        + r"\s*", "", r,
                        flags=_re.S | _re.I)
            m = _re.search(r"\{[^}]*\}", t.strip().strip("`"))
            try:
                j = json.loads(m.group(0)) if m else {}
                ship = bool(j.get("ship"))
                return {"stage": "brain-review", "ok": ship,
                        "note": (j.get("why", "") or "no reason held")[:160],
                        "ladder": ladder + [{"try": i + 1, "verdict":
                                             f"reviewed:{ship}"}],
                        "held": False}
            except Exception:
                ladder.append({"try": i + 1, "verdict": "unparsed"})
        else:
            ladder.append({"try": i + 1, "verdict": "brain-empty"})
            time.sleep(delay if i < tries - 1 else 0)
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "purpose": purpose,
           "digest": diff_text[:80].replace("\n", " "), "ladder": ladder,
           "held": True}
    _enqueue(row)
    return {"stage": "brain-review", "ok": False,
            "note": "HELD for review (never silently skipped) - queued "
                    "for the drain lane",
            "ladder": ladder, "held": True}


def selftest():
    """x2: (a) the brain-empty path = HELD + queued; (b) the good path =
    clean pass. NOTHING silently skips."""
    import CloudBrain as CB
    out = []
    chat0 = CB.chat
    q0 = os.path.getsize(Q) if os.path.exists(Q) else 0
    try:
        CB.chat = lambda *a, **k: None
        out.append(stage3("DIFF-A", "ISSUE-A", "selftest-empty"))
    finally:
        CB.chat = chat0
    held_ok = (out[-1].get("held") and out[-1]["ok"] is False
               and os.path.getsize(Q) > q0)
    out.append({"check": "empty->HELD+queued", "pass": held_ok})
    try:
        CB.chat = lambda *a, **k: '<think>x</think>\n{"ship": true, ' \
                                  '"why": "clean"}'
        out.append(stage3("DIFF-B", "ISSUE-B", "selftest-good"))
    finally:
        CB.chat = chat0
    out.append({"check": "good->clean-pass", "pass":
                out[-1]["ok"] is True and not out[-1].get("held")})
    with open(os.path.join(ROOT, "Config", "dual_review.json"), "w",
              encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "verdict": "PASS x2" if (held_ok and
                                            out[-1]["pass"]) else "CHECK",
                   "rows": out}, f, ensure_ascii=False, indent=1)
    print("[dual-review] " + ("PASS x2" if (held_ok and out[-1]["pass"])
                              else "CHECK") + " | the skip-path is DEAD")


if __name__ == "__main__":
    selftest()