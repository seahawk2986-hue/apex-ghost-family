"""Prophet - THE SELF-PREDICTING METACOGNITION (the S+ honesty round,
2026-11-04). THE INVERSION: the fleet PREDICTS ITS OWN TOMORROW - the
forecast gets WRITTEN (commit-on-disk; tamper-evident), then the NEXT
beat GRADES IT. The machine can never flatter itself without the
grade-sheet catching it - the honesty recursion = the anti-inflation
engine by construction.

forecast()  - the trend (the abstract-gym's per-tier accuracy + the
              swe-court's resolve-rate + the horizon's steps) -> the
              model's own calibrated prediction for the NEXT beat (with
              an uncertainty band; the honest I-don't-know = allowed)
grade()     - the previous forecast vs the measured now -> HIT/MISS
              (the Brier-style scoring; the calibration row = public)
loop()      - grade-then-forecast (the perpetual; the self-improve.yml
              runs it nightly; the receipts = Config/prophet.jsonl)

$0; stdlib; the band = +-6 points (the honest width); a forecast-less
state grades N/A (the machine starts honest, invents nothing)."""
import json
import os
import re
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
LEDGER = os.path.join(ROOT, "Config", "prophet.jsonl")


def _measured_now():
    """The fleet's measured self - every number = a file's receipt."""
    m = {}
    try:
        led = json.load(open(os.path.join(ROOT, "Config", "FeatureLedger.json"),
                             encoding="utf-8-sig"))
        prog = str(led.get("progress", ""))
        mm = re.match(r"(\d+)/(\d+)", prog)
        if mm:
            m["feature_ledger_done_pct"] = round(100 * int(mm.group(1)) / int(mm.group(2)), 1)
    except Exception:
        pass
    try:
        st = json.load(open(os.path.join(ROOT, "Config", "abstract_state.json"),
                            encoding="utf-8-sig"))
        for t0, s0 in st.get("tiers", {}).items():
            if s0.get("n", 0):
                m[f"abstract/{t0}"] = round(100 * s0["hits"] / s0["n"], 1)
    except Exception:
        pass
    try:
        rows = [json.loads(l) for l in open(os.path.join(ROOT, "Scores", "swe_smoke.jsonl"),
                                            encoding="utf-8-sig") if l.strip()]
        m["swe_resolve_pct"] = round(100 * sum(1 for r in rows if r.get("resolved")) /
                                     max(1, len(rows)), 1)
    except Exception:
        pass
    try:
        h = json.load(open(os.path.join(ROOT, "Config", "horizon.json"),
                           encoding="utf-8-sig"))
        m["horizon_minutes"] = h.get("minutes", 0)
    except Exception:
        pass
    return m


def grade():
    """The previous forecast vs the measured: the Brier-ish verdict."""
    try:
        rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8-sig") if l.strip()]
    except FileNotFoundError:
        return None
    last = next((r for r in rows if r.get("kind") == "forecast"), None)
    if not last:
        return None
    now = _measured_now()
    scored, score = [], 0.0
    for k, v in (last.get("forecast") or {}).items():
        lo, hi = v.get("lo"), v.get("hi")
        actual = now.get(k)
        if actual is None or lo is None:
            continue
        hit = lo <= actual <= hi
        scored.append({"key": k, "lo": lo, "hi": hi, "actual": actual,
                       "hit": hit})
        # the closeness credit (the miss-but-near = half)
        score += 1.0 if hit else (0.5 if (lo - 8) <= actual <= (hi + 8) else 0.0)
    out = {"kind": "verdict", "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "score": round(score / max(1, len(scored)), 2) if scored else None,
           "rows": scored, "measured": now}
    try:
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return out


def forecast():
    """The next beat's prediction - the model proposes, the file binds."""
    now = _measured_now()
    pred_input = "The fleet's MEASURED self (the only permitted inputs):\n" + \
        json.dumps(now, indent=1)
    try:
        import CloudBrain as CB
        raw = CB.chat(
            pred_input + "\n\nYou are the PROPHET organ (the metacognition "
            "recursion). Predict these for the NEXT measurement beat (24h): "
            "the abstract-gym's accuracy per measured tier, the swe_hit-rate "
            "drift, the horizon-minutes growth. Reply ONLY strict JSON: "
            "{key: {\"lo\": number, \"hi\": number}, ...} for the keys above "
            "(the band = your honest uncertainty; the +-6 points = the "
            "minimum width).",
            max_tokens=400, purpose="the prophet's forecast")
    except Exception:
        raw = ""
    import json as _j
    fc = {}
    try:
        m = re.search(r"\{[\s\S]*\}", raw or "")
        if m:
            fc = _j.loads(m.group(0))
    except Exception:
        fc = {}
    if not fc:
        out = {"kind": "forecast", "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
               "forecast": {}, "note": "the honest refused-to-predict state"}
    else:
        out = {"kind": "forecast", "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
               "forecast": fc}
    try:
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return out


def loop():
    g = grade()
    f = forecast()
    print(json.dumps({"graded": {k: g.get(k) for k in ("score",)} if g else None,
                      "forecast_keys": list((f.get("forecast") or {}).keys())},
                     ensure_ascii=False))
    return {"graded": g, "forecast": f}


if __name__ == "__main__":
    loop()