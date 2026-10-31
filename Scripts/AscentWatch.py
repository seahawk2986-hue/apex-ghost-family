"""THE ASCENT WATCH: the whole system trends UP or says so out loud.

1. Round-telemetry ledger: every round's fitness printed into a rolling log
2. Trend check: if the last-K average yield dips >15pct below the prior-K,
   an ALARM pulse fires (not silent decay - the family says when it's sick)
3. Store self-heal: library count vs the high-water mark; a shrink triggers
   automatic restore from the newest HEALTHY backup (unique-sha verified)
"""
import glob
import hashlib
import json
import os
import shutil
import time
import zipfile
from pathlib import Path

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
ASCENT = os.path.join(ROOT, "Config", "AscentLedger.jsonl")
STORE = os.path.join(ROOT, "Config", "SkillLibrary.json")
HIGH = os.path.join(ROOT, "Config", "store_highwater.json")


def log_round(fitness, findings, backlog, points):
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "fitness": round(fitness, 4),
           "findings": findings, "backlog": backlog, "points": points}
    with open(ASCENT, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return trend_check(row)


def trend_check(row, k=5, drop_pct=0.15):
    try:
        rows = [json.loads(x) for x in open(ASCENT, encoding="utf-8-sig") if x.strip()][-2 * k:]
    except Exception:
        return {"alarm": False}
    if len(rows) < 2 * k:
        return {"alarm": False, "watching": len(rows)}
    prev = [r["fitness"] for r in rows[-2 * k:-k]]
    cur = [r["fitness"] for r in rows[-k:]]
    a, b = sum(prev) / len(prev), sum(cur) / len(cur)
    dropped = a > 0 and (a - b) / a > drop_pct
    out = {"alarm": dropped, "avg_prior": round(a, 3), "avg_now": round(b, 3)}
    if dropped:
        out["pulse"] = ("ASCENT ALARM: family yield dropped >"
                        f"{drop_pct*100:.0f}pct - self-correction engaged "
                        "(rotate deeper corners, spawn explorers, mine backlog)")
        try:
            with open(os.path.join(AD, "family_seed_packet.json"),
                      "r+", encoding="utf-8-sig") as f:
                pkt = json.load(f)
                pkt.setdefault("directives", []).append(
                    {"ts": row["ts"], "dir": "self_correct", "reason": out["pulse"]})
                f.seek(0)
                f.write(json.dumps(pkt, indent=1))
        except Exception:
            pass
    return out


def store_watch():
    """Store high-water + AUTO-RESTORE on shrink (the family heals ITSELF)."""
    try:
        lib = json.load(open(STORE, encoding="utf-8-sig"))["skills"]
        n = len(lib)
        uniq = len({s.get("sha256", "")[:16] for s in lib})
    except Exception:
        return {"state": "unreadable"}
    try:
        hw = json.load(open(HIGH, encoding="utf-8-sig"))
    except Exception:
        hw = {}
    best = hw.get("rows", 0)
    if n >= best:
        json.dump({"rows": n, "uniq": uniq, "ts": time.strftime("%Y-%m-%d %H:%M:%S")},
                  open(HIGH, "w", encoding="utf-8"), indent=1)
        return {"state": "healthy", "rows": n, "uniq_shas": uniq}
    # SHRINK DETECTED: the family heals itself from its newest healthy backup
    restored = None
    for zpath in sorted(Path(os.path.join(ROOT, "Config", "backups")).glob("*.zip"),
                        reverse=True):
        try:
            with zipfile.ZipFile(zpath) as z:
                nm = [x for x in z.namelist() if x.endswith("SkillLibrary.json")][0]
                lib2 = json.loads(z.read(nm).decode("utf-8-sig"))
                if len(lib2.get("skills", [])) >= best and len(
                        {s.get("sha256", "")[:16] for s in lib2["skills"]}) >= uniq:
                    json.dump(lib2, open(STORE, "w", encoding="utf-8"), indent=1)
                    restored = zpath.name
                    break
        except Exception:
            continue
    return {"state": "shrink-healed", "was": n, "restored_from": restored,
            "rows_now": len(json.load(open(STORE, encoding="utf-8-sig"))["skills"])}


if __name__ == "__main__":
    print("store watch:", store_watch())
    print("trend:", log_round(3.2, 135, 1091, 2956.0))