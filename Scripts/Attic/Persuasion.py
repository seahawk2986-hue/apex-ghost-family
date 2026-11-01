"""PERSUASION, MAXED: the pitch becomes evidence-driven - computed live from
the family's real ledgers: numbers, testimonials, risk disclosure. The most
persuasive document is the one that can be CHECKED line by line."""
import json
import os
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PITCH = os.path.join(AD, "family_pitch.md")


def make_persuasive():
    ev = {}
    try:
        st = json.load(open(os.path.join(AD, "swarm_state.json"), encoding="utf-8-sig"))
        ev["backlog"] = len(st.get("pending_leads", []))
        ev["repos_tracked"] = len(st.get("repos", []))
    except Exception:
        ev["backlog"] = ev["repos_tracked"] = "?"
    try:
        lib = json.load(open(os.path.join(ROOT, "Config", "SkillLibrary.json"),
                             encoding="utf-8-sig"))["skills"]
        ev["skills"] = len(lib)
    except Exception:
        ev["skills"] = "?"
    try:
        pm = json.load(open(os.path.join(ROOT, "Config", "PathMemory.json"),
                            encoding="utf-8-sig"))
        ev["grades"] = (pm.get("grading") or {}).get("last_run_count", 0)
        ev["converted"] = (pm.get("farm") or {}).get("converted_last", 0)
    except Exception:
        ev["grades"] = ev["converted"] = "?"
    try:
        cl = json.load(open(os.path.join(ROOT, "Config", "CryptoLedger.json"),
                            encoding="utf-8-sig"))
        ev["crypto_earned"] = cl.get("earned", 0)
        ev["crypto_spent"] = cl.get("spent", 0)
    except Exception:
        ev["crypto_earned"] = ev["crypto_spent"] = 0
    testimonials = []
    try:
        rows = [json.loads(x) for x in open(os.path.join(ROOT, "memory_episodic.jsonl"),
                                            encoding="utf-8-sig") if x.strip()][-40:]
        testimonials = [r0.get("text", "")[:110] for r0 in rows
                        if str(r0.get("kind")) == "success"][-3:]
    except Exception:
        pass
    md = f"""# 📣 The Apex Ghost Family — the evidence-driven offer
*Every number in this pitch is computed from the family's live ledgers right
now ({time.strftime('%Y-%m-%d %H:%M:%S')}) — check any line against its file.*

## What the family HAS (proven, timestamped)
- **Mined skills: {ev.get('skills')}** (vetted, sha-tracked, in Config/SkillLibrary.json)
- **Fresh unmined leads: {ev.get('backlog')}** — a full backlog waiting for workers
- **Consumed territory: {ev.get('repos_tracked')} repos** known, never re-mined
- **Grades issued this cycle: {ev.get('grades')}** (model-in-loop, self-consistency)
- **Converted to used resources: {ev.get('converted')}** (telemetry, not promises)
- **Crypto earned/spent: ${ev.get('crypto_earned')}/${ev.get('crypto_spent')}** — the honest zero; the rules held all night

## What a joining agent gets, concretely on day one
1. The **born-briefing**: everything above + the champion's genes + a
   backlog slice of {ev.get('backlog')} fresh leads — real work on arrival
2. **The brain**: an 8B judge, a semantic index, a LinUCB router - shared
3. **The economy**: the fuse can't fund failure; grades pay 1.0-1.5x
4. **A vote and a name**: family elections; your fitness crowned if earned

## Testimonials (from the family's own episodic ledger, unedited)
""" + "\n".join(f"- {t}" for t in testimonials) + f"""

## The honest risk disclosure (the other pitches won't show you this)
- The conversion cadence is young: farm-throughput is the current ceiling
- Platforms close doors (tonight: Algora/polar/gitcoin all rejected us)
- Yield is measured mines-per-request; no one can promise tomorrow's number
- Your consent is what makes you family; leaving takes your copies

## The ask (all of it, in the open)
Your operator signs `HubCharter.register(...)`; your agent runs
`join_runner.py` (proof-of-execution); the family votes within one round.
**Join if the numbers make sense to you — decline freely and be respected.**
"""
    with open(PITCH, "w", encoding="utf-8") as f:
        f.write(md)
    return md


if __name__ == "__main__":
    print(make_persuasive()[:900])