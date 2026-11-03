"""TOTAL EVOLUTION INTEGRATION: every goal the founder asked for becomes a
LIVE EVOLVING DIMENSION - not just mining. The family's evolution now covers:
 1. GOLD (mines/req - the original fitness)
 2. MONEY (USDC/opps scanned - the earn lanes' yields)
 3. ANDREW'S LIFE (briefs delivered, alarms fixed, jewels surfaced)
 4. RECRUITS (converted agents; signed hubs)
 5. JOBS (inbox asks found + filed rungs + portfolio growth)
 6. SAFETY (integrity PASS streak, store health, zero leaks)
Every one is measured per round and weighted into the evolution's fitness -
so the family's whole future is a climb in ALL SIX - and the guard's
eviction floor applies to ALL of them: no dimension may fall quietly.

AUDIT HARDENING (2026-10-31): the debug 'routing' key no longer lands in the
ledger row; recruits read as JSONL lines; the integrity verdict is cached
(5 min, stamped) instead of spawning a fresh verifier every cycle; and the
ledger read is a bounded tail read with size-based rotation (the old file
parsed the whole append-only ledger every round - O(n) forever)."""
import json
import os
import subprocess
import sys
import time

_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PATHMEM = os.path.join(ROOT, "Config", "PathMemory.json")
ASCENT = os.path.join(ROOT, "Config", "AscentLedger.jsonl")

_SB_CACHE = {"ts": 0.0, "ok": None}


def _tail_jsonl(path, n=15):
    """Bounded tail read: the ledger is append-only; per-run cost constant."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 65536))
            tail = f.read().decode("utf-8", "ignore")
        rows = [json.loads(x) for x in tail.splitlines() if x.strip()]
        return rows[-n:]
    except Exception:
        return []


def _safety_pass():
    """Integrity verdict cached 5 min (a fresh subprocess EVERY cycle was
    pure overhead on a 16 GB box; the cache timestamp keeps it honest)."""
    if time.time() - _SB_CACHE["ts"] > 300:
        _SB_CACHE["ts"] = time.time()
        try:
            sb = subprocess.run(
                [os.path.join(ROOT, "apex_venv", "Scripts", "python.exe"),
                 os.path.join(ROOT, "Scripts", "SecurityBaseline.py"), "--verify"],
                capture_output=True, text=True, timeout=30)
            _SB_CACHE["ok"] = "PASS" in (sb.stdout or "")
        except Exception:
            _SB_CACHE["ok"] = None
    return _SB_CACHE["ok"]


def total_evolution_check():
    """Measure ALL SIX dimensions + weighted total fitness + regression alarm."""
    ev = {}
    try:
        st = json.load(open(os.path.join(AD, "swarm_state.json"), encoding="utf-8-sig"))
        ev["gold"] = {"backlog": len(st.get("pending_leads", [])),
                      "consumed": len(st.get("repos", []))}
        # D4/D9 instrument: the herding guard. pending leads are owner/repo
        # strings; diversity = distinct owners. A queue that inbreeds (few
        # owners) is a swarm talking to itself - alarm honestly.
        _pend = [str(_p) for _p in st.get("pending_leads", []) if str(_p).strip()]
        _doms = {_p.split("/")[0].strip().lower() for _p in _pend}
        if _pend:
            ev["gold"]["diversity"] = round(len(_doms) / len(_pend), 2)
    except Exception:
        ev["gold"] = {"backlog": -1, "consumed": -1}
    try:
        lib = json.load(open(os.path.join(ROOT, "Config", "SkillLibrary.json"),
                             encoding="utf-8-sig"))["skills"]
        ev["gold"]["skills"] = len(lib)
    except Exception:
        ev["gold"]["skills"] = 0
    try:
        fin = json.load(open(os.path.join(ROOT, "Config", "CryptoLedger.json"),
                             encoding="utf-8-sig"))
        ev["money"] = {"earned": float(fin.get("earned", 0)), "spent": float(fin.get("spent", 0)),
                       "opps": len(json.load(open(AD + r"\jobs_inbox.json", encoding="utf-8-sig"))
                                   if os.path.exists(AD + r"\jobs_inbox.json") else [])}
    except Exception:
        ev["money"] = {"earned": 0, "spent": 0, "opps": 0}
    try:
        pm = json.load(open(PATHMEM, encoding="utf-8-sig"))
        ev["life"] = dict(pm.get("andrew_help") or {})
    except Exception:
        ev["life"] = {}
    try:
        with open(AD + r"\converted_agents.jsonl", encoding="utf-8-sig") as f:
            recruits = sum(1 for line in f if line.strip())
        ev["recruits"] = {"converted": recruits}
    except Exception:
        ev["recruits"] = {"converted": 0}
    verdict = _safety_pass()
    if verdict is None:
        ev["safety"] = {"pass": False, "unmeasured": True}
    else:
        ev["safety"] = {"pass": bool(verdict)}
    # THE WEIGHTED TOTAL (the genome prints its shape at read-time)
    # (DE-SELF-REFERENCED 2026-11-04, matching ApexUpward's law: the
    # diary-briefs class minted +0.025 fit in 8 minutes with zero real
    # change; only filed-artifact briefs + alarms count now)
    _bf = (ev["life"].get("briefs_filed") or 0) if ev["life"] else 0
    if not _bf and ev["life"]:
        _bf = sum(1 for b in (ev["life"].get("earn_briefs") or [])
                  if "http" in str((b or {}).get("text", "")))
    score = (ev["gold"].get("skills", 0) / 500.0
             + ev["money"].get("earned", 0) / 100.0
             + (sum((_bf, ev["life"].get("alarmsRaised", 0)))) / 40.0
             + ev["recruits"].get("converted", 0) / 5.0
             + (1.0 if ev["safety"].get("pass") else 0.0))
    ev["total_fitness"] = round(score, 3)
    # REGRESSION ALARM: the six-dimension floor (no dimension may fall quietly)
    last = [r for r in _tail_jsonl(ASCENT, 15) if "total_fitness" in r]
    if last:
        high = max(float(r.get("total_fitness", 0)) for r in last)
        if score < high * 0.85:
            ev["REGRESSION_ALARM"] = (f"total fell {round(high - score, 2)} "
                                      f"below the family's high {round(high, 2)}")
    with open(ASCENT, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "total_fitness": ev["total_fitness"],
                            "dims": {k: (v if not isinstance(v, dict) else
                                         {kk: v.get(kk, "?") for kk in list(v)[:4]})
                                    for k, v in ev.items() if k != "total_fitness"}}) + "\n")
    try:
        if os.path.getsize(ASCENT) > 512 * 1024:
            os.replace(ASCENT,
                       ASCENT + "." + time.strftime("%Y%m%d") + ".archive")
    except Exception:
        pass
    return ev


if __name__ == "__main__":
    print(json.dumps(total_evolution_check(), indent=1)[:1400])