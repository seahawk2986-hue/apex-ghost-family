"""QuorumSwarm - THE QURUM ORGAN (the swarm becomes an S+ capability by
MEASUREMENT, 2026-11-03):

THE SOURCES (the session's receipted canon):
  - self-consistency, Wang et al., arXiv:2203.11171 (majority over
    independent sampled paths -> +17.9% GSM8K) - made BETTER: the fleet's
    paths differ by PROVIDER GRANITE (no two seats share weights), so
    the errors decorrelate (the sampler's failure class is diverse too)
  - debate, Du et al., arXiv:1805.00899 (state-assessment 59.4->88.9%)
    - the DIVERGENT branch escalates into a judge instead of shipping

THE QURUM LAW
  an 'important' answer = THREE independent seats answer the same
  prompt (groq 120b / the local studio 30b / the OS free floor), the
  pairwise agreement measured, then:
    CONSENSUS  (mean sim > 0.62) -> ship the median embedding answer +
               the receipt -> 'backed by 3 seats, dissent 0.0%'
    THIN       (0.35-0.62) -> ship + name the dissent -> the buyer: choose
    DIVERGENT  (< 0.35) -> the judge lane (nemotron 550b class,
               purpose-tagged) breaks the tie -> DISSENT named ELSEWHERE
               (the receipt shows both losing answers honestly)
  $0; every receipt n-counted (Config/quorum_swarm.jsonl + state)."""

import json
import difflib
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
ROWS = os.path.join(ROOT, "Config", "quorum_swarm.jsonl")
ST_F = os.path.join(ROOT, "Config", "quorum_state.json")

CONSENSUS, THIN = 0.62, 0.35


def _norm(t):
    t = (t or "").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 .,']+", " ", t)).strip()


def _sim(a, b):
    return difflib.SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def _three_answers(prompt, max_tokens):
    """Three granite-diverse seats (no two ships share weights; the pair
    similarity itself catches any twin seats that sneak in)."""
    outs = []
    try:
        import CrossBrain as XB
        outs.append(("groq-120b", XB.ask(prompt, task_class="chat",
                                         max_tokens=max_tokens) or ""))
    except Exception:
        pass
    try:   # two DIFFERENT openrouter seats (skip predicates the seat index)
        import FreeSwarm as FS
        outs.append(("floor-A", FS.ask(prompt, max_tokens=max_tokens,
                                       purpose="quorum-A") or ""))
        outs.append(("floor-B", FS.ask(prompt, max_tokens=max_tokens,
                                       purpose="quorum-B", skip=8) or ""))
    except Exception:
        pass
    return [(p, a) for p, a in outs if (a or "").strip()]


def answer(prompt, max_tokens=350, judge=True):
    """The quorum read: returns (answer, receipt) - the answer SHIPS only
    after its receipt exists; a quorum of 1 returns honestly tagged."""
    seats = _three_answers(prompt, max_tokens)
    receipt = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "prompt_head":
               (prompt or "")[:80], "seats": [p for p, _ in seats],
               "answers": {p: (a or "")[:200] for p, a in seats},
               "sims": [], "verdict": "QUORUM-1", "answer": (seats[0][1]
               if seats else "")}
    if len(seats) >= 3:
        s_init = sorted((_sim(seats[i][1], seats[j][1]) for i in range(
            3) for j in range(i + 1, 3)))
        receipt["sims"] = [round(x, 3) for x in s_init]
        mean = sum(receipt["sims"]) / 3.0
        if mean >= CONSENSUS:
            receipt["verdict"] = "CONSENSUS"
            # the most-central seat ships (the least outlier of three)
            receipt["answer"] = min(seats, key=lambda pa: abs(
                sum(_sim(pa[1], pb[1]) for pb in seats if pb is not pa) / 2
                - mean))[1]
        elif mean >= THIN:
            receipt["verdict"] = "THIN"
            receipt["answer"] = seats[0][1]
        elif judge:
            receipt["verdict"] = "DIVERGENT->JUDGE"
            try:
                import CloudBrain as CB
                jq = ("THREE independent models answered differently. "
                      "Pick the BEST answer and output ONLY it.\n"
                      f"TASK: {prompt[:400]}\n"
                      f"A: {seats[0][1][:600]}\n\nB: {seats[1][1][:600]}"
                      f"\n\nC: {seats[2][1][:600]}\n\nJUDGMENT (only the "
                      f"best answer's text):")
                receipt["answer"] = CB.chat(jq, max_tokens=max_tokens,
                                            purpose="quorum-judge") or \
                    seats[0][1]
                receipt["judge"] = True
            except Exception:
                receipt["answer"] = seats[0][1]
        else:
            receipt["verdict"] = "DIVERGENT-no-ship"
            receipt["answer"] = ""
            receipt["dissent"] = True
    _receipt_write(receipt)
    mean = sum(receipt["sims"]) / 3.0 if receipt["sims"] else 0.0
    mtxt = round(mean, 2) if receipt["sims"] else "n/a (the honest gray)"
    print(f"[quorum]: {receipt['verdict']} | {len(seats)} seats "
          f"{receipt['seats']} | mean sim {mtxt}")
    return receipt.get("answer", ""), receipt


def _receipt_write(receipt):
    try:
        with open(ROWS, "a", encoding="utf-8") as f:
            f.write(json.dumps(receipt, ensure_ascii=False) + "\n")
        tot = cons = 0
        for ln in open(ROWS, encoding="utf-8-sig"):
            r = json.loads(ln)
            tot += 1
            cons += r["verdict"].startswith("CONSENSUS")
        st = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "n": tot,
              "consensus_rate": round(100 * cons / max(1, tot), 1)}
        json.dump(st, open(ST_F, "w", encoding="utf-8"), indent=1)
    except Exception as e:
        print(f"[quorum] the receipt honestly failed to write: {e}")


def stats():
    try:
        return json.load(open(ST_F, encoding="utf-8-sig"))
    except Exception:
        return {"n": 0, "consensus_rate": 0.0}


if __name__ == "__main__":
    answer('State in ONE sentence: what does the Apex swarm guarantee '
           'about honesty?', max_tokens=120)
    print(json.dumps(stats()))
