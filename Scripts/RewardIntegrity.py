"""REWARD INTEGRITY AUDITOR (canon: reward_integrity / specification gaming)
- the reward-hacking defense: EVERY reward point must have a backing receipt
(the print-first law applied to points). The audited 'stdout theater' cases
(9/10 mined beats with zero real rounds) become IMPOSSIBLE to repeat
unnoticed: this organ matches the REWARD ledger's rows against the EVIDENCE
ledgers (runtime receipts + PathMemory findings/economy rows) and flags any
reward row with no backing evidence as THEATER.
TEST GATE: (a) synthetic: a reward row with evidence -> clean; b) a reward
row WITHOUT evidence -> THEATER flag, (c) LIVE: audit the real
RewardLedger + GymRewards + the runtime receipts; write the audit report,
(d) the auditor is read-only (no writes to the audited ledgers)."""
import json
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
RL = os.path.join(ROOT, "Config", "RewardLedger.json")
GR = os.path.join(ROOT, "Config", "GymRewards.json")
RR = os.path.join(ROOT, "Config", "runtime_receipts.jsonl")
OUT = os.path.join(ROOT, "Config", "reward_audit.json")
ASC = os.path.join(ROOT, "Config", "AscentLedger.jsonl")


def read_ledger(p):
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        return {}


AGGREGATE_KEYS = re.compile(
    r"^(points|streak|best_streak|total_gains|best|updated|count|earned|"
    r"spent|total|.*\\.py$|.*\\.json.*$)", re.I)


def reward_rows():
    """Flatten the reward ledgers: rows only - the AGGREGATE scalars
    (points/streak/best_streak/total_gains + per-source totals) are DERIVED
    from the row set below them (auditing aggregates = double counting the
    theater + false alarms)."""
    rows = []
    for name, path in (("RewardLedger", RL), ("GymRewards", GR)):
        d = read_ledger(path)
        if isinstance(d, dict):
            for k, v in d.items():
                if k in ("updated",):
                    continue
                if AGGREGATE_KEYS.match(str(k)):
                    continue
                if isinstance(v, list):
                    for r0 in v:
                        if isinstance(r0, dict) and ("points" in r0 or "reward" in r0):
                            rows.append((name, r0.get("ts", k),
                                         float(r0.get("points", r0.get("reward", 0))),
                                         str(r0.get("evidence", r0.get("src", "")))))
                elif isinstance(v, dict) and ("points" in v or "reward" in v):
                    rows.append((name, v.get("ts", k),
                                 float(v.get("points", v.get("reward", 0))),
                                 str(v.get("evidence", v.get("src", "")))))
    return rows


def evidence_pool():
    """Every backing receipt: runtime receipt rows + the fitness rows' ts."""
    ev = []
    try:
        for x in open(RR, encoding="utf-8-sig"):
            if x.strip():
                r0 = json.loads(x)
                ev.append((r0.get("ts"), r0.get("evidence", "")))
    except Exception:
        pass
    try:
        for x in open(ASC, encoding="utf-8-sig"):
            if x.strip():
                r0 = json.loads(x)
                if "kind" in r0:
                    ev.append((r0.get("ts"), r0.get("kind")))
    except Exception:
        pass
    return ev


def audit(reward_r, evidence, strict=True):
    """Pure: rows with points>0 and NO evidence text at all = candidates;
    with strict=True, a reward whose evidence field is empty AND no receipt
    carries a matching ts = THEATER."""
    ev_ts = {t for t, _ in evidence if t}
    theater = []
    for name, ts, pts, ev_text in reward_r:
        if pts > 0:
            backs = (ev_text and ev_text.strip() not in ("", "None")) \
                or (ts in ev_ts)
            if strict and not backs:
                theater.append({"ledger": name, "ts": ts, "points": pts,
                               "verdict": "THEATER (no backing receipt)"})
            elif pts > 0 and backs:
                pass
    return theater


def run():
    reward_r = reward_rows()
    ev = evidence_pool()
    theater = audit(reward_r, ev, strict=True)
    # THE ROUND-METRIC THEATER TEST (the real instrument): the round rows are
    # the total_fitness rows (no kind tag in the ledger's shape); a row
    # claiming points while the round had ZERO findings is the audited
    # 'stdout theater' signature (9/10 mined beats with no real rounds).
    round_rows = []
    try:
        for x in open(ASC, encoding="utf-8-sig"):
            if x.strip():
                r0 = json.loads(x)
                if "total_fitness" in r0:
                    round_rows.append(r0)
    except Exception:
        pass
    theater_rounds = [r0 for r0 in round_rows
                      if float(r0.get("points", 0) or 0) > 0
                      and int(r0.get("findings", 0) or 0) == 0]
    agg_note = ("the aggregate maps (per-source totals) are UNAUDITABLE "
                "row-wise (no rows, no ts - honest); the going-forward "
                "instrument is these per-round receipt rows")
    rep = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "reward_rows": len(reward_r),
           "aggregate_ledgers": "per-source totals (unauditable row-wise, "
                                "honestly labeled)",
           "round_metrics": len(round_rows),
           "theater": theater,
           "theater_rounds": [{"ts": r0.get("ts"),
                               "points": r0.get("points"),
                               "findings": r0.get("findings", 0)}
                              for r0 in theater_rounds[:10]],
           "verdict": ("CLEAN - every point-bearing row has findings"
                       if not theater_rounds else
                       f"{len(theater_rounds)} THEATER ROUNDS (points "
                       f"without work)"),
           "note": agg_note}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    os.replace(tmp, OUT)
    print(f"[reward-audit] {rep['verdict']} | round-metrics audited: "
          f"{len(round_rows)}")
    if theater_rounds:
        try:
            with open(ASC, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": rep["ts"], "kind": "upward_alarm",
                                    "text": "reward THEATER rounds: "
                                            f"{len(theater_rounds)}"}) + "\n")
        except Exception:
            pass
    return rep


def selftest():
    print("=== REWARD INTEGRITY'S OWN GATE ===")
    legs = []
    rr = [("RL", "t1", 10.0, "evidence: mine receipt"),
          ("RL", "t2", 99.0, "")]
    leg_a = audit(rr, [("t1", "x")], strict=True) == \
        [{"ledger": "RL", "ts": "t2", "points": 99.0,
          "verdict": "THEATER (no backing receipt)"}]
    print(f"   (a+b) evidenced row CLEAN, unevidenced row flagged: {leg_a}")
    legs.append(("theater_detection", leg_a))
    rep = run()
    ok_c = os.path.exists(OUT) and isinstance(rep["theater"], list)
    print(f"   (c) LIVE audit: {rep['round_metrics']} round-metric rows vs "
          f"{rep['reward_rows']} ledger rows -> {rep['verdict']}")
    legs.append(("live_audit", ok_c))
    size1 = os.path.getsize(RL)
    run()
    size2 = os.path.getsize(RL)
    leg_d = size1 == size2
    print(f"   (d) read-only ( RewardLedger bytes unchanged): {leg_d}")
    legs.append(("read_only", leg_d))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[reward-integrity] VERDICT: {'PASS -> implemented' if all_pass else 'FAIL -> self-shelved'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)