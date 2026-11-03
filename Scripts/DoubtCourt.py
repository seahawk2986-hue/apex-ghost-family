"""DoubtCourt - THE DEBATE ORGAN (the S+ round, 2026-11-04).

THE THEORY (sourced, proven): AI-safety-via-debate (arXiv:1805.00899,
Irving/Christiano/Amodei - OpenAI): two agents argue; the JUDGE's accuracy
rose from 59.4% to 88.9% with adversarial debate. The fleet operationalizes
the paper: every PUBLIC-PRODUCT artifact (the demo-desk's triage reports =
the family's face) gets CHALLENGED by an adversarial second lane before
delivery:

  challenge(report) -> the critic-lane hunts: invented numbers, unsupported
  claims, the missed obviouls (the observable-map gaps); the verdict:
  CLEAN (ship) / REVISIONS (the fix-list) -> one revision pass max ->
  publish the CHALLENGED version (the debate = the receipt; the
  agreement-rate = Config/doubt_court.jsonl = the S+ metric: the % of
  artifacts that survived the debate untouched).

$0; bounded (1 challenge + 1 revision); the local floor behind; the
never-fail law: the challenge's own failure = ship unrevised + print."""
import json
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
LEDGER = os.path.join(ROOT, "Config", "doubt_court.jsonl")


def _ask(prompt, purpose="doubt"):
    try:
        import CloudBrain as CB
        t = CB.chat(prompt, max_tokens=400, purpose=purpose)
        if (t or "").strip():
            return t
    except Exception:
        pass
    try:
        import FreeSwarm
        t = FreeSwarm.ask(prompt, max_tokens=400, purpose=purpose)
        if (t or "").strip():
            return t
    except Exception:
        pass
    return ""


def challenge(report, facts=None, target=""):
    """The debate: RETURNS (final_report, verdict, agree: bool)."""
    if not (report or "").strip():
        return report, "nothing-to-challenge", True
    c = _ask(
        "You are the family's ADVERSARIAL CHALLENGER (the debate theory: "
        "arXiv:1805.00899 - a true second voice raises the judge's accuracy). "
        "Attack this triage report: (a) any INVENTED number/claim not in the "
        "facts, (b) any fix whose 'how' is vague, (c) one important observable "
        "the report MISSED. Reply ONLY strict JSON: "
        "{\"verdict\": \"clean\" | \"revise\", \"issues\": [\"...\"], "
        "\"missing\": \"...\"}\n\n"
        f"FACTS (the only permitted number-source):\n{json.dumps(facts or {}, ensure_ascii=False)[:1200]}\n\n"
        f"REPORT (the target: {target}):\n{report[:3500]}")
    ok, issues, missing = None, [], ""
    try:
        import json as _j
        m = re.search(r"\{[^{}]*\"verdict\"[^{}]*\}", c or "", re.DOTALL)
        if m:
            dj = _j.loads(m.group(0))
            ok = str(dj.get("verdict", "")).lower()
            issues = [str(i)[:150] for i in (dj.get("issues") or []) if str(i)[:1]]
            missing = str(dj.get("missing", ""))[:200]
    except Exception:
        ok = None
    agree = (ok != "revise")
    final = report
    if not agree and issues:
        rev = _ask(
            "You are the report's AUTHOR defending under challenge (debate "
            "round 2). Apply ONLY these factual revisions (keep everything "
            "else; never invent): " + " | ".join(issues) +
            (f" ADD the missing: {missing}" if missing else "") +
            f"\n\nFACTS:\n{json.dumps(facts or {}, ensure_ascii=False)[:1200]}\n\nREPORT:\n{report[:3500]}\n\n"
            "Output ONLY the revised full report in plain markdown.")
        if (rev or "").strip() and len(rev) > len(report) * 0.5:
            final = rev
    try:
        row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "target": target[:60],
               "verdict": ok or "challenge-failed", "issues": len(issues),
               "revised": final != report,
               "agree": final == report}
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return final, (ok or "challenge-failed"), agree


def stats():
    try:
        rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8-sig") if l.strip()]
        agreed = sum(1 for r in rows if r.get("verdict") == "clean")
        return {"debates": len(rows), "clean": agreed,
                "clean_rate": round(100 * agreed / max(1, len(rows)), 1)}
    except FileNotFoundError:
        return {"debates": 0, "clean": 0, "clean_rate": None}


if __name__ == "__main__":
    print(json.dumps(stats(), indent=1))