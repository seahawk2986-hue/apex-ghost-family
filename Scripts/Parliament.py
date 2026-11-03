"""Parliament - THE EPISTEMIC-HEALTH METER (the S+ round's newest organ,
2026-11-04; the fleet's own design - the sourced debate papers judge ONE
answer; this measures the FLEET'S MIND ITSELF):

  vote(claim) - SIX model-diverse seats (nemotron/cerebras/groq/glm/poll-
                inations/the local floor) each vote AGREE/DISAGREE with
                ONE independent reason - no seat sees the others' votes
                (the independence = the anti-echo design)
  meter()     - THE S+ NUMbers: the split-rate (the epistemic diversity:
                0% = the echo chamber = the ALARM; the healthy = the
                dissent carries), the unanimous-rate, the per-seat
                independence receipts

THE USE: the family's BIG decisions (the routes, the claims, the
self-grades) = put to the parliament; the ECHO-ALARM (0 splits over 10
votes) = printed LOUD (the machine that thinks only in one voice = the
enemy of the critical-thinking S+).

$0; bounded 6 votes; receipts: Config/parliament.jsonl + the state."""
import json
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
LEDGER = os.path.join(ROOT, "Config", "parliament.jsonl")
SEATS = (("nemotron-550b",), ("cerebras-120b",), ("groq",),
         ("nim-glm",), ("pollinations",), ("local-phi4",))


def vote(claim):
    """Six independent seats, one claim; the tally + the reasons."""
    votes = []
    for i, models in enumerate(SEATS):
        a = ""
        try:
            import CloudBrain as CB
            a = CB.chat(
                "Vote on this claim with ONE word (AGREE or DISAGREE) + a "
                "10-word reason. No seat sees any other vote (the "
                "independence law). Reply ONLY strict JSON: "
                "{\"vote\": \"agree\"|\"disagree\", \"reason\": \"...\"}\n"
                "CLAIM: " + claim,
                max_tokens=140, purpose=f"the parliament seat {i+1}",
                models=models, resp_json=True)
        except Exception:
            pass
        try:
            import FreeSwarm
            if not (a or "").strip() and models[0] not in ("local-phi4",):
                a = FreeSwarm.ask(
                    "Vote AGREE/DISAGREE + a 10-word reason. Reply ONLY strict "
                    "JSON: {\"vote\": \"agree\"|\"disagree\", \"reason\": \"...\"}\n"
                    "CLAIM: " + claim, max_tokens=140, purpose="the seat's floor")
        except Exception:
            pass
        v, r = "", ""
        try:
            import json as _j
            m = re.search(r"\{[^{}]*\}", a or "", re.DOTALL)
            if m:
                dj = _j.loads(m.group(0))
                v = str(dj.get("vote", "")).lower()
                r = str(dj.get("reason", ""))[:90]
        except Exception:
            v = (a or "").lower()
        seat = models[0]
        votes.append({"seat": seat, "vote": v, "reason": r})
    tallies = sum(1 for v in votes if "agree" in v["vote"] and
                  "disagree" not in v["vote"])
    split_rate = round(100 * min(tallies, len(votes) - tallies) / max(1, len(votes)), 1)
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "claim": claim[:100],
           "votes": votes, "agree_n": tallies, "disagree_n": len(votes) - tallies,
           "split_rate": split_rate,
           "echo_alarm": (len(votes) - tallies in (0, len(votes)))}
    try:
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass
    print(f"[parliament]: {tallies}/{len(votes)} agree | split-rate {split_rate}% "
          f"| {'*** THE ECHO ALARM: NO DISSENT IN THE MIND ***' if row['echo_alarm'] else 'the voices carry'}")
    return row


def meter():
    try:
        rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8-sig") if l.strip()]
        sr = [r.get("split_rate", 0) for r in rows[-10:]]
        mean = round(sum(sr) / max(1, len(sr)), 1)
        return {"votes": len(rows), "mean_split_rate": mean,
                "verdict": (echo if (echo := "the echo-chamber risk: the mind's voices "
                                     "agree too often") else "healthy dissent")
                if mean < 5 else "healthy dissent",
                "law": "the healthy fleet's mind = the split-rate 15-50% (the "
                       "independent seats think differently; the dissent = the "
                       "evidence of real thinking)"}
    except FileNotFoundError:
        return {"votes": 0, "verdict": "the parliament has never voted"}


if __name__ == "__main__":
    claim = " ".join(sys.argv[1:]) or "The fleet's routing should prefer diversity of models over raw size"
    vote(claim)
    print(json.dumps(meter(), indent=1, ensure_ascii=False))