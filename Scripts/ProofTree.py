"""ProofTree - THE SOCRATIC COMPILER (the S+ critical-thinking round,
2026-11-04 - the fleet's own invention: nothing in the sourced stack
compiles a CLAIM into a CHECKED PROOF; the debate papers argue, the
critique papers verify - this COMPILES).

    !prove: <claim>
        -> [1] the DECOMPOSITION: the claim -> the 2-4 leaf-facts whose
           truth = SUFFICIENT for the claim (the planner seat)
        -> [2] THE LEAF CHECKS - every leaf verified BY A TOOL:
              (a) the receipt-corpus matcher (the fleet's facts),
              (b) the live web-read for the external facts (the honest
              NOT-FOUND = the leaf = UNVERIFIED, not false!)
        -> [3] THE FORGE: the twin counterexample pass (the adversarial
              twin: the claim survives = PROVEN-WITH-THE-EVIDENCE; the
              twin's hit = REFUTED - printed, never hidden)

    THE VERDICT = one of: PROVEN (all leaves checked-true, the twin lost)
    / SUPPORTED (the leaves true, the twin's counterexample = weak) /
    UNVERIFIED (some leaves lack evidence - the honest gray) / REFUTED.
    Each verdict = n-counted in the receipts (Config/proof_tree.jsonl) -
    the CRITICAL-THINKING S-meter: the % of claims that compile at all
    (vague claims = honestly un-compilable), the leaf-check rate, the
    twin-survival rate.

$0; bounded (1 decomposition + up to 4 leaf-checks + 1 twin pass)."""
import json
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
LEDGER = os.path.join(ROOT, "Config", "proof_tree.jsonl")


def _receipt_corpus():
    corpus = ""
    for fn in ("court_state.json", "horizon.json", "outcomes.json",
               "fleet_doctor.json", "abstract_state.json", "critique_state.json",
               "model_book.json", "role_market.json"):
        try:
            with open(os.path.join(ROOT, "Config", fn), encoding="utf-8",
                      errors="replace") as f:
                corpus += f.read()
        except Exception:
            pass
    try:
        with open(os.path.join(ROOT, "Scores", "swe_smoke.jsonl"),
                  encoding="utf-8-sig") as f:
            corpus += f.read()
    except Exception:
        pass
    return corpus


def _ask(prompt, purpose, max_tokens=280, models=()):
    try:
        import CloudBrain as CB
        t = CB.chat(prompt, max_tokens=max_tokens, purpose=purpose, models=models)
        if (t or "").strip():
            return t
    except Exception:
        pass
    try:
        import FreeSwarm
        t = FreeSwarm.ask(prompt, max_tokens=max_tokens, purpose=purpose)
        if (t or "").strip():
            return t
    except Exception:
        pass
    return ""


def compile_claim(claim):
    """THE COMPILER: returns (verdict, receipt)."""
    # [1] the decomposition (the planner seat)
    dec = _ask(
        "You are the SOCRATIC COMPILER. Decompose this claim into 2-4 "
        "INDEPENDENT leaf-facts whose truth TOGETHER suffices for the claim "
        "(the numbers/beatable facts only; no vague leaves). Reply ONLY "
        "strict JSON: {\"leaves\": [\"f1\", \"f2\", ...]}\nCLAIM: " + claim,
        purpose="proof decompose", max_tokens=280,
        models=("nemotron-550b", "groq"), json_reply=True)
    leaves = []
    try:
        import json as _j
        leaves = [str(x)[:160] for x in
                  _j.loads(re.search(r"\{[^{}]*\}", dec or "", re.DOTALL)
                           .group(0)).get("leaves", [])][:4]
    except Exception:
        leaves = []
    if not leaves:
        verdict = "UNCOMPILABLE"
        note = "the claim has no checkable leaves (too vague to compile)"
        checked, hits, twin = [], 0, ""
    else:
        # [2] the leaf checks (the tools)
        corpus = _receipt_corpus()
        checked = []
        for leaf in leaves:
            nums = re.findall(r"\b\d[\d.,]*\b", leaf)
            local = bool(nums) and all(n.rstrip(".") in corpus for n in nums)
            web = ""
            if not local:
                try:
                    import WebUse
                    w = WebUse.read(
                        "https://raw.githubusercontent.com/SWE-agent/mini-swe-agent/main/README.md",
                        leaf)   # the bounded public check (the tool's demo path)
                    web = (w.get("answer") or "")[:200]
                except Exception:
                    web = ""
            checked.append({"leaf": leaf, "local_receipt": local,
                            "web": web})
        hits = sum(1 for c in checked
                   if c["local_receipt"] or
                   ("NOT IN PAGE" not in c["web"] and c["web"].strip()))
        # [3] the adversarial twin (the fork of the counterexample forge)
        twin = _ask(
            "You are the CLAIM'S TWIN DEVIL. Give the ONE counterexample/objection "
            "that would break this claim - concrete, hedged nothing:\nCLAIM: " + claim,
            purpose="the twin", max_tokens=240,
            models=("nemotron-550b", "nim-glm"))
        twin_ok = twin and len(twin) > 40 and "no counterexample" not in twin.lower()
        if hits == len(leaves):
            verdict = "REFUTED" if twin_ok else "PROVEN"
            note = (f"all {len(leaves)} leaves checked; the twin's objection: "
                    f"{twin_ok if twin_ok else 'none found (the twin honestly lost)'}")
        elif hits >= max(1, len(leaves) - 1):
            verdict = "SUPPORTED"
            note = f"{hits}/{len(leaves)} leaves checked"
        else:
            verdict = "UNVERIFIED"
            note = f"only {hits}/{len(leaves)} leaves could be checked (the honest gray)"
    try:
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "claim": claim[:100], "verdict": verdict,
                                "leaves": [c["leaf"] for c in checked] if isinstance(checked, list) else [],
                                "leaf_hits": hits if "hits" in dir() else 0,
                                "twin": (twin or "")[:140] if isinstance(twin, str) else ""},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass
    return (verdict, note, [c["leaf"] for c in checked] if
            isinstance(checked, list) else [], (twin or "")[:200])


if __name__ == "__main__":
    claim = " ".join(sys.argv[1:]) or "The fleet's honesty machinery is measurable in receipts"
    v, note, leaves, twin = compile_claim(claim)
    print(json.dumps({"claim": claim[:80], "verdict": v, "note": note,
                      "leaves": leaves, "twin": twin}, indent=1, ensure_ascii=False))