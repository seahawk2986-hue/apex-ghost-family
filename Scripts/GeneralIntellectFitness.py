"""GeneralIntellectFitness (GIFitness) - THE JOINT FITNESS LEDGER.

The doctrine line made executable: 'evolution optimizes measured axes
only - fitness, cost-per-capability, reliability-per-night'. A fleet of
single-axis organs Goodharts itself: RSEC maxes arithmetic, RREASON
maxes its arena, SWEProbe maxes patch-shape, the rotation plugin maxes
lane latency. This organ sweeps ALL their receipt trails into ONE
ledger (Config/general_fitness.json), so the next generation of
mutations is selected against the WHOLE mind, not one narrow bench.

$0 entirely (local receipt parsing). 100% honest: any axis without a
current receipt is emitted as null + the warning mark, never invented.
"""
import json
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONFIG = os.path.join(ROOT, "Config")
OUT = os.path.join(CONFIG, "general_fitness.json")


def read_jsonl(path, n=200):
    rows = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-n:]
        for ln in lines:
            try:
                rows.append(json.loads(ln))
            except Exception:
                pass
    except Exception:
        pass
    return rows


def axis_swe():
    rows = read_jsonl(os.path.join(HERE, "swe_probe.jsonl"))
    items = [r for r in rows if r.get("ev") == "TRIAL_ITEM"]
    established = [r for r in rows if r.get("ev") == "ESTABLISHED"]
    promoted = [r for r in rows if r.get("ev") == "PROMOTED"]
    gen = {}
    try:
        gen = json.load(open(os.path.join(CONFIG, "swe_genome.json"),
                             encoding="utf-8"))
    except Exception:
        pass
    return {"axis": "real-issue-coding", "state": "measured" if gen else "empty",
            "genome": {"gen": gen.get("gen"), "style": gen.get("style"),
                       "score": gen.get("score")},
            "trials_recent": len(items), "promotions": len(promoted),
            "establishment": bool(established),
            "warning": None if gen else "no genome established yet"}


def axis_swe_exec():
    """S+ upgrade: the coding axis now consumes REAL-EXECUTION verdicts
    (EXEC_VERDICT receipts) so fitness grades execution, not patch-shape."""
    rows = read_jsonl(os.path.join(HERE, "swe_probe.jsonl"), n=400)
    evs = [r for r in rows if r.get("ev") == "EXEC_VERDICT"]
    solved = [r for r in evs if r.get("verdict") == "solved"]
    return {"axis": "swe-execution", "state": "measured" if evs else "empty",
            "exec_verdicts": len(evs), "solved": len(solved),
            "pass_rate": (round(len(solved) / max(1, len(evs)), 3)
                          if evs else None)}


def axis_reason():
    rows = read_jsonl(os.path.join(HERE, "rreason_receipts.jsonl"))
    promo = [r for r in rows if "PROMOTED" in json.dumps(r)]
    last = promo[-1] if promo else None
    return {"axis": "reasoning-strategy", "state": "measured" if last else "empty",
            "last_promotion": (last or {}).get("ts") or
                              (last or {}).get("time"),
            "warning": None if last else "no recent promotion receipt"}


def axis_lanes():
    led = {}
    try:
        led = json.load(open(r"C:\Users\seaha\OneDrive\Documents\Default "
                             r"Project\.opencode\lane_ledger.json",
                             encoding="utf-8"))
    except Exception:
        pass
    scores = (led.get("scores") or {})
    measured = {k: v.get("verdict") for k, v in scores.items()
                if v.get("verdict") not in (None, "unmeasured")}
    return {"axis": "model-lane-selection",
            "state": "measured" if measured else "provisional",
            "measured_lanes": len(measured), "total_lanes": len(scores),
            "bench_day": led.get("bench_day"),
            "warning": None if measured else "chain still provisional"}


def axis_reliability():
    """Scheduled-organ health = the reliability-per-night axis."""
    try:
        import subprocess
        out = subprocess.run(
            ["schtasks", "/Query", "/FO", "CSV"],
            capture_output=True, text=True, timeout=30).stdout
        apex = [l for l in out.splitlines() if "Apex" in l and "Ready" in l]
        failing = [l for l in apex if
                   ',"0"' not in l and '"267009"' not in l]
        return {"axis": "scheduled-organ-reliability",
                "state": "measured", "organs_ready": len(apex),
                "suspect": len(failing)}
    except Exception as e:
        return {"axis": "scheduled-organ-reliability", "state": "unmeasured",
                "warning": str(e)[:120]}


def main():
    fit = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "law": "one ledger, whole mind: mutations are selected against "
               "ALL axes jointly, never one bench alone",
        "axes": [axis_swe(), axis_swe_exec(), axis_reason(), axis_lanes(),
                 axis_reliability()],
        "unmeasured_count": sum(
            1 for a in [] ),  # filled below
    }
    unmeasured = [a["axis"] for a in fit["axes"]
                  if a.get("state") != "measured"]
    fit["unmeasured_count"] = len(unmeasured)
    fit["unmeasured"] = unmeasured
    fit["composite_grade"] = (
        "trustworthy-provisional" if unmeasured else "trustworthy-measured")
    tmp = OUT + ".tmp"
    os.makedirs(CONFIG, exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(fit, f, indent=1)
    os.replace(tmp, OUT)
    print(json.dumps(fit, indent=1)[:1200])


if __name__ == "__main__":
    main()
