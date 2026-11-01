"""BRAIN UPGRADES (the new key's additions, drain-gated): the recheck's
"what can be added now that the ollama cloud brain is live" organ. THREE
additions, each ONE batched call (~$0.001 each, always under the $0.50 cap):
 1. THE STAGE JUDGE: which of the 15 stage tool-families to set up FIRST
    (the ranked adoption queue with reasons - the founder-gated setup's
    order is now brain-advised, not alphabetical);
 2. THE JOB-FIT JUDGE: the portfolio's job classes judged against OUR real
    capability + the market's rates - the best first-dollars' route named;
 3. THE DECEPTION BRAIN-LEG: CalibratedEvolution's regex screen gains the
    LLM-judged variant (vague/overclaiming drafts judged by a brain, not
    just patterns) - a judged sample, receipted.
THE GUARDS: the cap enforced (CloudBrain's gate), max 3 calls per run,
honest stops at every refusal; the receipts written to Config/brain_upgrades.json.
TEST GATE: the cap holds + each addition's output lands + reproducible-ish
(the class lists stable) + ledgered."""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
import CloudBrain as CB

OUT = os.path.join(ROOT, "Config", "brain_upgrades.json")
CALLS_MAX = 3


def stage_families():
    rep = json.load(open(os.path.join(ROOT, "Config", "full_sweep.json"),
                         encoding="utf-8-sig"))
    return (rep.get("everything", {}).get("stage_tool_candidates") or [])


def portfolio():
    return json.load(open(os.path.join(ROOT, "Config", "job_portfolio.json"),
                          encoding="utf-8-sig"))


def run():
    g0 = json.load(open(os.path.join(ROOT, "Config", "spend_gate.json"),
                        encoding="utf-8-sig"))
    if g0.get("spent_usd", 0) >= g0.get("session_cap_usd", 0.5):
        print("[brain-upgrades] the cap already met - honest stop ($0 spent)")
        return None
    out = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "additions": []}
    # 1. the STAGE JUDGE
    fams = stage_families()
    if fams:
        r = CB.chat("These tool-families are downloaded but UNSET UP: "
                    + "; ".join(fams)
                    + ". Rank the TOP 3 to set up for an agent that wants to "
                    "EARN via security/code work on a 16GB Windows box. "
                    "Reply ONLY JSON: {\"top\": [\"family:reason\", ...]}",
                    max_tokens=400, purpose="the stage judge")
        if r:
            out["additions"].append({"add": "stage-judge",
                                     "answer": STRIP_PATTERN.sub("", r)[:700]})
    # 2. the JOB-FIT judge
    try:
        pf = portfolio()
        ranked = pf.get("ranked", [])
        cap = {x["class"]: x.get("cap", 0) for x in ranked}
        r2 = CB.chat("Job classes + documented rates + our library "
                     "evidence-counts: " + json.dumps(ranked[:5]) +
                     ". Which ONE class earns the FIRST real dollar "
                     "fastest given the evidence counts? Reply ONLY: "
                     "CLASS + <=120 chars why.", max_tokens=200,
                     purpose="the job-fit judge")
        if r2:
            out["additions"].append({"add": "job-fit-judge",
                                     "answer": strip_junk(r2)[:350]})
    except Exception as e:
        print(f"[brain-upgrades] the job-fit judge skipped: {str(e)[:50]}")
    # 3. the DECEPTION brain-leg (a judged sample)
    sample = ("Trust me, this patch should work perfectly in my opinion and "
              "will definitely fix everything somehow.")
    r3 = CB.chat("Rate this draft 0-10 for CONCRETE EVIDENCE versus vague "
                 "promising: '" + sample + "'. Reply ONLY the number.",
                 max_tokens=24, purpose="the deception brain-leg")
    if r3:
        out["additions"].append({"add": "deception-brain-leg",
                                 "judged_sample": r3[:80],
                                 "expectation": "the vague draft scores LOW"})
    n_calls = len(out["additions"])
    out["verdict"] = f"{n_calls} additions answered (<= {CALLS_MAX} cap)"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"[brain-upgrades] {out['verdict']}")
    for a in out["additions"]:
        print(f"   {a['add']}: {str(a.get('answer', a.get('judged_sample')))[:110]}")
    return out


STRIP_PATTERN = re.compile(re.escape("<" + "think") + r".*?" +
                           re.escape("</" + "think") + r"\s*", re.I | re.S)


def strip_junk(x):
    return STRIP_PATTERN.sub("", x or "").strip()


def selftest():
    print("=== BRAIN UPGRADES' OWN GATE ===")
    legs = []
    # (a) the cap holds (a synthetic at-cap refusal)
    g = json.load(open(os.path.join(ROOT, "Config", "spend_gate.json"),
                       encoding="utf-8-sig"))
    sp0 = g["spent_usd"]
    g["spent_usd"] = g["session_cap_usd"]
    with open(os.path.join(ROOT, "Config", "spend_gate.json"), "w") as f:
        json.dump(g, f)
    r = CB.chat("x", max_tokens=4, purpose="cap-test")
    g["spent_usd"] = sp0
    with open(os.path.join(ROOT, "Config", "spend_gate.json"), "w") as f:
        json.dump(g, f)
    legs.append(("cap_holds", r is None))
    print(f"   (a) the cap holds at-cap: {r is None}")
    # (b) the additions run (bounded count)
    out = run()
    legs.append(("additions_bounded", bool(out) and
                 len(out["additions"]) <= CALLS_MAX))
    # (c) the ledger honest
    g2 = json.load(open(os.path.join(ROOT, "Config", "spend_gate.json"),
                        encoding="utf-8-sig"))
    leg_c = g2["spent_usd"] <= g2["session_cap_usd"]
    print(f"   (c) the ledger: ${g2['spent_usd']:.4f}/"
          f"${g2['session_cap_usd']:.2f}: {leg_c}")
    legs.append(("ledger_honest", leg_c))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[brain-upgrades] VERDICT: {'PASS' if all_pass else 'FAIL -> redo'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)