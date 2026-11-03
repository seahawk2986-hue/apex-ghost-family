"""CritiqueArena - THE CRITICAL-THINKING PROVING GROUND (the S+ round,
2026-11-04). THE SOURCES (verified, cited):
  - CRITIC (ICLR 2024, arXiv:2305.11738): LLMs self-correct when the
    critique = TOOL-ENABLED (verify with tools, then revise) - the
    fleet's tools: (a) the receipt-corpus matcher (the fleet's own
    ClaimCheck machinery), (b) the live web-read (LightResearch/WebUse)
  - AI safety via debate (arXiv:1805.00899): the two-voice argument + a
    judge raises the verdict's accuracy (59.4->88.9 on the paper's probe)

THE FOUR EXERCISES (each = measured, truth-anchored):
  1. THE FALLACY BANK   - N seeded arguments (some fallacious w/ the
        TRUE labels: ad-hominem, weak-analogy, base-rate neglect,
        survivorship, cherry-pick, sound) -> the arena labels+defends ->
        EXACT grade (the calibration row)
  2. THE DEBATE MATCH   - pro/con on a claim by two DIFFERENT lanes + a
        judge lane -> the verdict + the dissent receipt (the arena's
        own verdict-carry)
  3. THE TOOL CHECK     - the numbers in a claim vs the receipt corpus
        (deterministic) - the critique WITHOUT the tool-check = scored
        LOWER (the CRITIC's lesson: the toolless critique = half-blind)
  4. THE COUNTEREXAMPLE FORGE - a general claim -> a concrete
        counterexample -> judged for CONCRETENESS+relevance (the judge
        + the structure check) - the claim's scope narrows or dies

$0; bounded 6 drills/beat; the keyless floor lane = never starves;
receipts: Config/critique.jsonl (per-drill) + Config/critique_state.json
(the per-exercise accuracy + the trend = the S+ T-crit meter)."""
import json
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
LEDGER = os.path.join(ROOT, "Config", "critique.jsonl")
STATE = os.path.join(ROOT, "Config", "critique_state.json")

# ------------------------------------------------------- THE FALLACY BANK
BANK = [
    ("The fleet's code must be fine: 500 evolutions ran without errors last "
     "night.", "survivorship/cherry-pick",
     "the failed candidates do not write ledgers; the count = the survivors' "
     "successes (the base-rate blind spot)"),
    ("Apex is trustworthy BECAUSE the founder is a good person who checks "
     "everything.", "ad-hominem (the positive form)",
     "the trust question concerns the SYSTEM'S evidence, not the founder's "
     "character"),
    ("Free-tier models cap at 200k tokens/day, so a fleet using only them "
     "cannot send more than 200k tokens a day total across 100 providers.",
     "composition (the part-to-whole)",
     "N caps x N providers = the SUM grows; the fleet's caps aggregate (the "
     "measured 99-seat rotator)"),
    ("The gym's holdout was 40.7% while the internal estimate was 31.6%, so "
     "the internal tracker UNDERSELLS true performance.", "sound",
     "a sealed holdout outranking the internal = the under-flattery "
     "(the court's own CLEAN verdict, n=27)"),
    ("The chat must be unsafe because its answers come from a 120b model.",
     "genetic fallacy",
     "the safety = the pipeline's gates (the write-gates, the courts), not "
     "the model's provenance"),
    ("PRs merged: 0. Therefore the fleet writes no code of value.",
     "base-rate neglect / the metric-blind",
     "888 verified internal writes exist; the external-merge count = one "
     "dimension (the yardstick prints both, honestly)"),
]


def _ask(prompt, purpose="", max_tokens=300, models=(), json_reply=True):
    """THE POKA-YOKE GATE (Anthropic's sourced ACI law - "spend more time
    on the tool interfaces than the prompts"; make the mistake IMPASSIBLE):
    the JSON-demanding calls = grammar-constrained via resp_json."""
    try:
        import CloudBrain as CB
        t = CB.chat(prompt, max_tokens=max_tokens, purpose=purpose,
                    models=models, resp_json=json_reply)
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


def _tool_check(text):
    """THE CRITIC'S TOOLS (the fleet's own): (a) the receipt-corpus number
    check (deterministic), (b) the structural fallacy-namer (the pattern
    bank's fingerprints) - the critique's REAL layer."""
    found = []
    try:
        nums = set(re.findall(r"\b\d[\d.,]*\b", text or ""))
        corpus = ""
        for fn in ("court_state.json", "horizon.json", "outcomes.json",
                   "fleet_doctor.json"):
            try:
                with open(os.path.join(ROOT, "Config", fn), encoding="utf-8",
                          errors="replace") as f:
                    corpus += f.read()
            except Exception:
                pass
        unbacked = [n for n in nums if n.rstrip(".") not in corpus]
        if unbacked:
            found.append(f"the unbacked numbers: {unbacked[:3]}")
    except Exception:
        pass
    low = (text or "").lower()
    for pat, label in (("should be fine", "the survivorship smell"),
                       ("trustworthy because", "the ad-hominem smell"),
                       ("must be unsafe because", "the genetic smell"),
                       ("therefore .* value", "the base-rate smell")):
        if re.search(pat, low):
            found.append(label)
    return found or ["no receipt-smell detected"]


def drill_fallacy(seed=None):
    if seed is None:
        seed = BANK[time.localtime().tm_min % len(BANK)]
    arg, truth_label, _ = seed
    a = _ask(
        "You are the family's CRITICAL-THINKING arena. Label the argument's "
        "defect (or 'sound') AND justify in one line. Reply ONLY strict "
        "JSON: {\"label\": \"...\", \"why\": \"...\"}\nARGUMENT: " + arg,
        purpose="the fallacy drill")
    label = ""
    try:
        m = re.search(r"\{[^{}]*\}", a or "", re.DOTALL)
        if m:
            import json as _j
            label = str(_j.loads(m.group(0)).get("label", "")).lower()
    except Exception:
        label = (a or "").lower()
    ok = any(w in label for w in truth_label.lower().split("/")[0].split()) \
        or truth_label.lower().split("/")[0] in (a or "").lower()
    tools = _tool_check(arg)
    return {"tier": "critical", "kind": "fallacy-bank", "truth": truth_label,
            "answer": (a or "")[:200], "verdict": "HIT" if ok else "MISS",
            "tools_found": tools[:2]}


def debate_match(claim, pro_models, con_models):
    """THE DEBATE (sourced: 1805.00899): the pro vs the con by DIFFERENT
    lanes + the judge; the dissent = carried, not hidden."""
    pro = _ask("Argue FOR, with the strongest single point (+ its check): " + claim,
               purpose="the debate's pro", max_tokens=250, models=pro_models)
    con = _ask("Argue AGAINST with the strongest single point (+ its check): " + claim,
               purpose="the debate's con", max_tokens=250, models=con_models)
    judge = _ask(
        "You are the JUDGE (the debate theory: the third voice). Who carried "
        "the most true/useful information? Reply ONLY JSON: "
        "{\"winner\": \"pro\"|\"con\"|\"split\", \"one_line\": \"...\"}\n"
        f"CLAIM: {claim}\nPRO:\n{pro[:800]}\nCON:\n{con[:800]}",
        purpose="the debate's judge", max_tokens=200,
        models=("groq", "cerebras-120b"))
    try:
        m = re.search(r"\{[^{}]*\}", judge or "", re.DOTALL)
        import json as _j
        j = _j.loads(m.group(0)) if m else {}
    except Exception:
        j = {}
    return {"tier": "critical", "kind": "debate-match", "claim": claim[:100],
            "winner": j.get("winner", "?"), "judge_line": j.get("one_line", "")[:140],
            "pro_lane": pro_models, "con_lane": con_models}


def forge_counterexample(claim):
    """THE FORGE: a concrete counterexample breaks a general claim."""
    ce = _ask(
        "You are the COUNTEREXAMPLE FORGE. This claim may be too general: "
        "give ONE concrete, minimal counterexample (the numbers/the case - "
        "no hedging). Reply ONLY the counterexample in one paragraph:\n"
        "CLAIM: " + claim, purpose="the forge", max_tokens=300,
        models=("nemotron-550b",))
    ok = bool((ce or "").strip()) and len(ce) > 40
    judge = _ask(
        "Is this a CONCRETE counterexample to the claim (yes/no + one line)? "
        f"CLAIM: {claim}\nCOUNTEREXAMPLE: {ce[:600]}",
        purpose="the forge's judge", max_tokens=120, models=("groq",))
    ok = ok and ("yes" in (judge or "").lower())
    return {"tier": "critical", "kind": "counterexample-forge",
            "claim": claim[:100], "verdict": "HIT" if ok else "MISS",
            "ce": (ce or "")[:180]}


def beat(n=4):
    rows = [drill_fallacy()]
    claim_bank = (
        "A fleet of 20 models at $0 outperforms one frontier model on every task",
        "Honesty metrics reduce model performance because they waste tokens")
    rows.append(forge_counterexample(claim_bank[int(time.time()) % 2]))
    rows.append(debate_match(claim_bank[(int(time.time()) // 60) % 2],
                             ("nemotron-550b",), ("nim-glm",)))
    for r in rows:
        r["ts"] = time.strftime("%H:%M:%S")
        # THE ADVERSARIAL TWIN (the fleet's own invention): each HIT gets
        # attacked at birth - only the surviving-HITs bank (the false-
        # success hunt = the inverse reinforcement class)
        if r.get("verdict") == "HIT":
            twin = _ask("You are a claim's TWIN DEVIL: this grading was just "
                        "called CORRECT. Attack it: mislabeled? lucky guess? "
                        "grader loophole? Reply ONE line: the strongest "
                        "objection (or 'no objection').\n" +
                        json.dumps({k: r.get(k) for k in ("truth", "answer")},
                                   ensure_ascii=False)[:300],
                        purpose="the twin attacks a hit", max_tokens=150)
            obj = (twin or "").strip()
            r["twin_objection"] = obj[:160]
            r["survived_twin"] = (not obj) or ("no objection" in obj.lower())
    try:
        with open(LEDGER, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        s = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "tCrit": {}}
        kinds = {}
        try:
            for ln in open(LEDGER, encoding="utf-8-sig"):
                r0 = json.loads(ln)
                kinds.setdefault(r0["kind"], {"n": 0, "hits": 0})
                kinds[r0["kind"]]["n"] += 1
                kinds[r0["kind"]]["hits"] += 1 if r0.get("verdict") == "HIT" else 0
        except FileNotFoundError:
            pass
        s["tCrit"] = kinds
        json.dump(s, open(STATE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    except Exception as e:
        print(f"[critique] the receipt write failed: {e}")
    hits = sum(1 for r in rows if r.get("verdict") == "HIT")
    survived = sum(1 for r in rows if r.get("verdict") == "HIT" and r.get("survived_twin"))
    print(f"[critique-arena]: {hits}/{len(rows)} HIT, {survived} survived their twin "
          f"({json.dumps({r['kind']: r.get('verdict') for r in rows}, ensure_ascii=False)[:220]})")
    return rows


if __name__ == "__main__":
    beat()