"""THE ASCENT WATCH: the whole system trends UP or says so out loud.

1. Round-telemetry ledger: caller metrics are tagged kind=round_metric
2. Trend check: over the ONE real instrument - TotalEvolution's
   total_fitness rows (the old version mixed two row schemas over the same
   ledger and could KeyError on the other's rows; now one formula, one key)
3. Store self-heal: library count vs the high-water mark; a shrink triggers
   automatic restore from the newest HEALTHY backup (unique-sha verified);
   an unhealed shrink is reported as shrink-UNHEALED (honest), never as
   "healed" - the alarm IS the state.
"""
import json
import os
import sys
import time
import zipfile
from pathlib import Path

_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from TotalEvolution import _tail_jsonl  # one bounded tail-read, shared
from SafeIO import write_json as _atomic_json

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
ASCENT = os.path.join(ROOT, "Config", "AscentLedger.jsonl")
STORE = os.path.join(ROOT, "Config", "SkillLibrary.json")
HIGH = os.path.join(ROOT, "Config", "store_highwater.json")


def log_round(fitness, findings, backlog, points):
    caller_metric_row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                         "kind": "round_metric", "fitness": round(fitness, 4),
                         "findings": findings, "backlog": backlog, "points": points}
    with open(ASCENT, "a", encoding="utf-8") as f:
        f.write(json.dumps(caller_metric_row) + "\n")
    return trend_check()


def trend_check(k=5, drop_pct=0.15):
    """Trend over ONLY the total_fitness rows (one instrument, one formula;
    the old version mixed schemas and could KeyError across them)."""
    try:
        rows = [r for r in _tail_jsonl(ASCENT, 40) if "total_fitness" in r][-2 * k:]
    except Exception as e:
        print(f"[trend] could not evaluate: {e}", flush=True)
        return {"alarm": False, "error": str(e)[:80]}
    if len(rows) < 2 * k:
        return {"alarm": False, "watching": len(rows)}
    vals = [float(r["total_fitness"]) for r in rows]
    prev, cur = vals[:-k], vals[-k:]
    a, b = sum(prev) / len(prev), sum(cur) / len(cur)
    dropped = a > 0 and (a - b) / a > drop_pct
    out = {"alarm": dropped, "avg_prior": round(a, 3), "avg_now": round(b, 3)}
    if dropped:
        out["pulse"] = ("ASCENT ALARM: family yield dropped >"
                        f"{drop_pct*100:.0f}pct - self-correction engaged "
                        "(rotate deeper corners, spawn explorers, mine backlog)")
        try:
            p = os.path.join(AD, "family_seed_packet.json")
            pkt = json.load(open(p, encoding="utf-8-sig"))
            pkt.setdefault("directives", []).append(
                {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "dir": "self_correct", "reason": out["pulse"]})
            if not _atomic_json(p, pkt):
                print("[trend] pulse packet-write FAILED (lock busy) - "
                      "the directive is NOT delivered, honestly", flush=True)
        except Exception as e:
            print(f"[trend pulse packet-append FAILED] {e}", flush=True)
    return out


def store_watch():
    """Store high-water + AUTO-RESTORE on shrink (the family heals ITSELF)."""
    try:
        lib = json.load(open(STORE, encoding="utf-8-sig"))["skills"]
        n = len(lib)
        uniq = len({(s.get("sha256") or "")[:16] for s in lib if s.get("sha256")})
    except Exception:
        return {"state": "unreadable"}
    try:
        hw = json.load(open(HIGH, encoding="utf-8-sig"))
    except Exception:
        hw = {}
    best = hw.get("rows", 0)
    if n >= best:
        _atomic_json(HIGH, {"rows": n, "uniq": uniq, "ts": time.strftime("%Y-%m-%d %H:%M:%S")})
        return {"state": "healthy", "rows": n, "uniq_shas": uniq}
    # SHRINK DETECTED: the family heals itself from its newest healthy backup
    restored = None
    for zpath in sorted(Path(os.path.join(ROOT, "Config", "backups")).glob("*.zip"),
                        reverse=True):
        try:
            with zipfile.ZipFile(zpath) as z:
                nm = [x for x in z.namelist() if x.endswith("SkillLibrary.json")][0]
                lib2 = json.loads(z.read(nm).decode("utf-8-sig"))
                u2 = len({(s.get("sha256") or "")[:16] for s in lib2.get("skills", [])
                          if s.get("sha256")})
                if len(lib2.get("skills", [])) >= best and u2 >= max(1, hw.get("uniq", 0)):
                    _atomic_json(STORE, lib2)
                    restored = zpath.name
                    break
        except Exception:
            continue
    if restored is not None:
        try:
            n2 = len(json.load(open(STORE, encoding="utf-8-sig"))["skills"])
        except Exception:
            n2 = -1
        return {"state": "shrink-healed", "was": n, "restored_from": restored,
                "rows_now": n2}
    return {"state": "shrink-UNHEALED", "was": n, "high_water": best,
            "note": "no healthy backup qualified - the alarm is the state"}


if __name__ == "__main__":
    print("store watch:", store_watch())
    print("trend:", trend_check())