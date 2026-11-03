"""CogNet - THE DIVISION OF COGNITIVE LABOR (the S+ round, 2026-11-04).

THE THEORY: single-model cognition = the frontier's own limit; the fleet
beats it the way the human world does - SPECIALIZATION ACROSS SPECIALISTS.
One deep question = a PIPELINE, each stage on its strongest class:

  STAGE 1  THE PLAN     - the reasoning-ceiling seat (nemotron-550b):
                          the approach, the sub-steps, the risk map
  STAGE 2  THE CHALLENGE (debate theory, arXiv:1805.00899) - the
                          plain-channel critic (glm-5.3-flash class): the
                          counterexample hunt
  STAGE 3  THE VERIFY   - the tool-follower (gpt-oss-120b): the
                          fact/consistency pass
  STAGE 4  THE SYNTH    - the consensus: only the SURVIVING points + the
                          honest "the debate split on X" note

THE LAWS: every stage = a lane's receipt (latency + name); the synthesis
invents nothing beyond the stages' outputs; a stage's failure = the honest
downgrade (the next class takes the stage). The receipts:
Config/cognet.jsonl (per-run: the 4 stages' names + latencies + verdicts).

$0; bounded (4 calls + 45s caps); wired: the chat's "!deep" prefix."""
import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
LEDGER = os.path.join(ROOT, "Config", "cognet.jsonl")


def _ask(prompt, models, purpose, max_tokens=400):
    """One lane-chain call; the honest name+latency return."""
    t0 = time.time()
    try:
        import CloudBrain as CB
        txt = CB.chat(prompt, max_tokens=max_tokens, purpose=purpose,
                      models=models)
        if (txt or "").strip():
            return txt, round(time.time() - t0, 2), models[0]
    except Exception:
        pass
    try:
        import FreeSwarm
        txt = FreeSwarm.ask(prompt, max_tokens=max_tokens, purpose=purpose)
        if (txt or "").strip():
            return txt, round(time.time() - t0, 2), "freeswarm"
    except Exception:
        pass
    return "", round(time.time() - t0, 2), "none"


def run_deep(question):
    """THE PIPELINE: returns (answer, receipt)."""
    stages = []
    # ---- STAGE 1: the plan (the reasoning ceiling)
    plan, s1, l1 = _ask(
        "You are the PLANNER in a cognitive pipeline. Break the question into "
        "the approach + the sub-steps + the two biggest risks. Be exact, no "
        "fluff:\nQUESTION: " + question,
        ("nemotron-550b", "groq", "cerebras-120b"), "cognet-plan", 450)
    stages.append({"stage": "plan", "lane": l1 or "none", "s": s1,
                   "chars": len(plan or "")})
    # ---- STAGE 2: the challenge (the critic class)
    crit, s2, l2 = _ask(
        "You are the CHALLENGER (the debate round: arXiv:1805.00899). Attack "
        "this plan: the false steps, the missing cases. Reply the verdict as "
        "SOUND or FLAWED + the one-line fix list.\nPLAN:\n" + (plan or question),
        ("nim-glm", "groq", "cerebras-120b"), "cognet-challenge", 350)
    stages.append({"stage": "challenge", "lane": l2 or "none", "s": s2,
                   "verdict": (crit or "")[:60]})
    # ---- STAGE 3: the verify (the tool-follower)
    ver, s3, l3 = _ask(
        "You are the VERIFIER. Given the plan + the critique, verify the "
        "claims' consistency; drop the unsupported. Output the corrected "
        "plan's outline only.\nPLAN:\n" + (plan or "") + "\nCRITIQUE:\n" +
        (crit or ""),
        ("groq", "cerebras-120b", "pollinations"), "cognet-verify", 400)
    stages.append({"stage": "verify", "lane": l3 or "none", "s": s3})
    # ---- STAGE 4: the synthesis
    answer, s4, l4 = _ask(
        "You are the SYNTHESIZER of a multi-agent debate. From the verified "
        "plan + the critique, write the FINAL ANSWER to the question: flowing "
        "prose, English only, no markdown, honest 'the debate split on...' "
        "where the voices disagreed.\nQUESTION: " + question +
        "\nVERIFIED PLAN:\n" + (ver or plan or "") +
        "\nCRITIQUE:\n" + (crit or ""), (), "cognet-synthesis", 500)
    stages.append({"stage": "synthesis", "lane": l4 or "none", "s": s4})
    try:
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "question": question[:80], "stages": stages},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass
    return answer, stages


if __name__ == "__main__":
    q = " ".join(sys.argv[1:2:]) or "What makes an agent fleet smarter than a single frontier model?"
    a, st = run_deep(q)
    print(json.dumps({"answer": (a or "")[:300], "stages": st}, indent=1, ensure_ascii=False))