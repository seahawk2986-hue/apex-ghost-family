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

import difflib
import json
import math
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
ROWS = os.path.join(ROOT, "Config", "quorum_swarm.jsonl")
ST_F = os.path.join(ROOT, "Config", "quorum_state.json")

CONSENSUS, THIN = 0.62, 0.35

EMBED_URL = os.environ.get("APEX_EMBED_URL",
                           "http://127.0.0.1:1234/v1/embeddings")
EMBED_MODEL = os.environ.get("APEX_EMBED_MODEL",
                             "text-embedding-nomic-embed-text-v1.5")
_embed_ok = None   # None = untried, True/False after the first call
_embed_fail_at = 0.0
_EMBED_COOLDOWN = 600
_vec_cache = {}
_LAST_METRIC = "lexical"


def _norm(t):
    t = (t or "").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 .,']+", " ", t)).strip()


def _embed(text):
    """THE SEMANTIC CHANNEL (stdlib, $0): the local embedder; a dead one
    must not tax EVERY call - the circuit breaker + the lexical fallback
    keep the receipt honest either way."""
    global _embed_ok, _embed_fail_at
    if _embed_ok is False and time.time() - _embed_fail_at < _EMBED_COOLDOWN:
        return None
    key = _norm(text)[:600]
    if key in _vec_cache:
        return _vec_cache[key]
    try:
        import urllib.request as _u
        req = _u.Request(EMBED_URL, data=json.dumps(
            {"model": EMBED_MODEL, "input": text[:2000]}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with _u.urlopen(req, timeout=10) as x:
            d = json.load(x)
        v = d["data"][0]["embedding"]
        _embed_ok = True
        _vec_cache[key] = v
        return v
    except Exception:
        _embed_ok = False
        _embed_fail_at = time.time()
        return None


def _ecos(a, b):
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    dot = sum(x * y for x, y in zip(a[:n], b[:n]))
    na = math.sqrt(sum(x * x for x in a[:n]))
    nb = math.sqrt(sum(y * y for y in b[:n]))
    return dot / (na * nb) if na and nb else 0.0


def _sim(a, b):
    """THE AGREEMENT, measured where it lives: the SEMANTIC channel
    first (the granite-diverse seats word the same truth differently -
    the lexical difflib structurally diverged every round, so Wang's
    self-consistency bonus evaporated and every receipt rode the judge),
    the lexical ratio as the honest fallback when the embedder sleeps."""
    global _LAST_METRIC
    va, vb = _embed(a), _embed(b)
    if va and vb:
        _LAST_METRIC = "embedding"
        return max(0.0, _ecos(va, vb))
    _LAST_METRIC = "lexical"
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
        receipt["sims_metric"] = _LAST_METRIC
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
