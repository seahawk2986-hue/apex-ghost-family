"""HorizonLadder - THE AUTONOMY-HORIZON ORGAN (2026-11-04, the GI round).

THE DEFINING GAP (the verified frontier scorecard): the world's standard
autonomy metric is METR's 50%-task-completion TIME HORIZON
(arXiv:2503.14499, NeurIPS 2025; frontier ~50min and doubling every ~7
months; the primary driver = RELIABILITY - adapting to mistakes). Apex
could not even STATE its own horizon: uptime was infinite, but nothing
measured how long a goal's work-chains actually run before they break.

THE METRIC (Apex's honest analog, computed from ITS OWN ledgers only):
  - reconstrue the episodic ledger as autonomous CHAINS: consecutive rows
    (any kind except gym_miss/no-lane) joined by gaps <= 10 minutes;
  - a step = VERIFIED-SUCCESS (evolution_pass/HIT/201-filed/CERTIFIED/
    pass receipt), FAILURE (error/MISS/refused), or NEUTRAL (bookkeeping);
  - chain completion = verified-successes / (successes + failures);
  - THE HORIZON = the longest chain with completion >= 50%: its span in
    minutes + its step count is Apex's honest time-horizon analog;
  - THE DRIVER REPORT (the METR insight applied): the failure-kind
    histogram over chain-breaking rows = where reliability leaks.
Published to Config/horizon.json + episodic + a /receipts line; the
trend compares against the previous receipt (is the horizon growing?)
$0; stdlib; one pass; never invents a number it could not compute."""
import io
import json
import os
import sys
import time
from datetime import datetime

if getattr(sys.stdout, "apex_wrapped", False) is False:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.stdout.apex_wrapped = True

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
OUT = os.path.join(REPO, "Config", "horizon.json")
GAP_S = 10 * 60

SUCCESS_KINDS = {"evolution_pass", "success", "certification", "filing_bridge",
                 "local_mind", "court", "gym_pass", "warm_brain"}
FAILURE_KINDS = {"error", "gym_miss", "REGRESSION"}
NEUTRAL_KINDS = {"conversation", "lesson", "insight", "calibration", "planning_vote"}


def _cls(e):
    k = e.get("kind", "")
    t = e.get("text", "")
    if k in SUCCESS_KINDS:
        return "S"
    if k in FAILURE_KINDS:
        return "(no lane answered)" in t and "N" or "F"
    if k in NEUTRAL_KINDS:
        if "MISS" in t and "GI gym" in t:
            return "F"
        return "N"
    if "error" in k.lower() or "fail" in k.lower():
        return "F"
    if "201" in t or "200-verified" in t or "HIT (" in t:
        return "S"
    return "N"


def measure():
    rows = []
    try:
        for ln in (
            open(os.path.join(REPO, "memory_episodic.jsonl"), encoding="utf-8")):
            if not ln.strip():
                continue
            try:
                rows.append(json.loads(ln))
            except Exception:
                continue
    except FileNotFoundError:
        print("[ladder]: no episodic ledger - nothing to measure (honest)")
        return None
    chains = []
    cur = []
    last_ts = None
    for e in rows:
        try:
            ts = datetime.strptime(e["ts"][:19], "%Y-%m-%d %H:%M:%S").timestamp()
        except Exception:
            continue
        if last_ts is None or ts - last_ts <= GAP_S:
            cur.append(e)
        else:
            chains.append(cur)
            cur = [e]
        last_ts = ts
        last = e
    if cur:
        chains.append(cur)
    # per-chain completion
    best = None
    fails_hist = {}
    for ch in chains:
        s = sum(1 for e in ch if _cls(e) == "S")
        f = sum(1 for e in ch if _cls(e) == "F")
        tot = s + f
        comp = s / tot if tot else 0.0
        span = 0.0
        try:
            t0 = datetime.strptime(ch[0]["ts"][:19], "%Y-%m-%d %H:%M:%S")
            t1 = datetime.strptime(ch[-1]["ts"][:19], "%Y-%m-%d %H:%M:%S")
            span = (t1 - t0).total_seconds() / 60.0
        except Exception:
            pass
        for e in ch:
            if _cls(e) == "F":
                kind = e.get("kind", "?")
                fails_hist[kind] = fails_hist.get(kind, 0) + 1
        if comp >= 0.5 and (best is None or (len(ch), comp) > (best["steps"], best["completion"])):
            best = {"steps": len(ch), "minutes": round(span, 1),
                    "completion": round(comp, 3),
                    "verified_successes": s, "failures": f,
                    "started": ch[0].get("ts", "")}
    prev = None
    try:
        prev = json.load(open(OUT, encoding="utf-8-sig"))
    except Exception:
        pass
    doc = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metric": ("Apex's analog of METR's 50%-completion time horizon "
                   "(arXiv:2503.14499): the longest ledger chain whose "
                   "verified-success/completion >= 50%"),
        "steps": (best or {}).get("steps", 0),
        "minutes": (best or {}).get("minutes", 0.0),
        "completion": (best or {}).get("completion", 0.0),
        "previous": {"minutes": (prev or {}).get("minutes", 0.0),
                     "steps": (prev or {}).get("steps", 0)},
        "trend": ("growing" if prev and (best or {}).get("minutes", 0) > prev.get("minutes", 0)
                  else "first-receipt" if not prev else "flat"),
        "chain_failures": fails_hist,
        "the_driver_law": ("METR's finding: time horizon grows first through "
                           "RELIABILITY (adapting to mistakes) - the "
                           "failure histogram is the climb map"),
        "chains_analyzed": len(chains),
    }
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    os.replace(tmp, OUT)
    try:
        with open(os.path.join(REPO, "memory_episodic.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps({"id": os.urandom(6).hex(), "ts": doc["ts"],
                                "kind": "horizon",
                                "text": f"HORIZON: {doc['steps']} steps / "
                                f"{doc['minutes']} min at {doc['completion']:.0%} "
                                f"completion ({doc['trend']}); failures: "
                                f"{fails_hist}"[:220], "meta": {}, "imp": 0.9},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass
    print(f"[ladder]: horizon = {doc['steps']} steps / {doc['minutes']} min "
          f"@ {doc['completion']:.0%} ({doc['trend']}) | failure map: {fails_hist}")
    return doc


if __name__ == "__main__":
    measure()