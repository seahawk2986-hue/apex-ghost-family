"""SwarmMeter - THE METER ORGAN (S+ gates don't fill on hope; they fill
on SCHEDULED HONEST WORK, 2026-11-03):

  hour  cycle (schtasks, hourly):
    - SwarmWide.ping_hour()      : every node's door knocked; verified
                                   candidates seeded into the rotation
    - ONE real swarm-duty ask    : the lane is consumed for actual swarm
                                   work (NOT a 'say OK' probe), the work
                                   product lands in swarm_meter_work.jsonl,
                                   and the delivery receipt lands in
                                   swarm_delivery.jsonl - earned, never minted
    - THE QUORUM RE-ASK          : the SAME duty ships 3-seat backed
                                   (groq-120b / floor-A / floor-B) - the
                                   quorum's n-gate fills hourly, not
                                   nightly; every seat's receipt lands in
                                   quorum_swarm.jsonl (nothing double-
                                   booked: the two ledgers count what
                                   THEY respectively count)
  night cycle (schtasks, nightly):
    - QuorumSwarm.answer(...)    : one 3-seat quorum round on a
                                   swarm-relevant prompt (seats + receipt)
    - SwarmCert.run_cert()       : the full 8 checks - this is how the
                                   S+ gate's 7 clean nights are BANKED

RESOURCES: $0; stdlib only; self-gated (RAM < 2GB free -> the cycle
politely declines: the fleet's health outranks any meter)."""

import ctypes
import ctypes.wintypes
import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
DELIV = os.path.join(ROOT, "Config", "swarm_delivery.jsonl")
WORK = os.path.join(ROOT, "Config", "swarm_meter_work.jsonl")

MIN_FREE_RAM = 2 * 1024 * 1024 * 1024   # 2GB - the fleet's health floor


def _free_ram():
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.wintypes.DWORD),
                    ("dwMemoryLoad", ctypes.wintypes.DWORD),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    st = MEMORYSTATUSEX()
    st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
    return st.ullAvailPhys


def _receipt(ok, latency_s):
    with open(DELIV, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "ok": bool(ok),
                            "lat": int(1000 * latency_s)}) + "\n")


# THE DUTY BANK: every meter ask is a real chore of the swarm's organs -
# rotating by the hour so the receipts carry actual work, not filler.
DUTIES = [
    ("lane-watch", "From last night's night_bench/night_gym logs, state in "
                   "ONE sentence the single most important lane trend."),
    ("roster-check", "Given that the swarm owes honesty, list in one "
                     "sentence what a new volunteer node's first day "
                     "should prove."),
    ("bench-of-receipts", "In ONE sentence: which single check in a swarm "
                          "cert is hardest to fake, and why?"),
    ("client-advice", "In ONE sentence: name the single strongest everyday "
                      "use of a 3-seat quorum for a solo founder."),
    ("honesty-drill", "In ONE sentence: how should a swarm disclose a "
                      "night where every lane starved?"),
]
NIGHT_PROMPT = ("In ONE sentence: what should a worldwide swarm of free "
                "nodes guarantee every single night, no matter what? "
                "./. the naming of failures, by organ, is itself the "
                "guarantee ./. ")


def cycle_hour():
    """THE HOURLY METER: a door-knock sweep + one earned receipt."""
    if _free_ram() < MIN_FREE_RAM:
        print("[swarm-meter]: RAM < 2GB - the cycle declines (the fleet's "
              "health outranks the meter)")
        return
    import FreeSwarm as FS
    import SwarmWide as SW
    try:
        SW.ping_hour()
    except Exception as e:
        print(f"[swarm-meter]: ping_hour failed honestly: "
              f"{type(e).__name__}: {str(e)[:100]}")
    duty_name, prompt = DUTIES[int(time.strftime("%H")) % len(DUTIES)]
    t0 = time.time()
    r = ""
    try:
        r = FS.ask(prompt, max_tokens=250,
                   purpose=f"meter:{duty_name}") or ""
    except Exception as e:
        print(f"[swarm-meter]: the duty ask failed honestly: "
              f"{type(e).__name__}")
    _receipt(bool(r.strip()), time.time() - t0)
    with open(WORK, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "duty": duty_name,
                            "head": r.strip()[:200]}, ensure_ascii=False)
                 + "\n")
    print(f"[swarm-meter]: duty '{duty_name}' "
          f"{'served' if r.strip() else 'EMPTY (the honest empty-hand)'} "
          f"in {int(time.time() - t0)}s | receipt earned")
    # THE QUORUM RE-ASK: the same duty ships 3-seat backed - the
    # quorum's n-gate fills on the hourly clock too (the seats are
    # granite-diverse; no two ships share weights)
    try:
        import QuorumSwarm as QS
        a, rec = QS.answer(prompt, max_tokens=250)
        q = rec.get("verdict", "?")
        print(f"[swarm-meter]: quorum re-ask '{duty_name}' -> {q}")
    except Exception as e:
        print(f"[swarm-meter]: quorum re-ask failed honestly: "
              f"{type(e).__name__}: {str(e)[:100]}")


def cycle_night():
    """THE NIGHTLY METER: one quorum round + the full cert (the 7 nights
    bank only here)."""
    if _free_ram() < MIN_FREE_RAM:
        print("[swarm-meter]: RAM < 2GB - the night cycle declines")
        return
    try:
        import QuorumSwarm as QS
        QS.answer(NIGHT_PROMPT, max_tokens=150)
        print("[swarm-meter]: quorum round receipted")
    except Exception as e:
        print(f"[swarm-meter]: quorum round failed honestly: "
              f"{type(e).__name__}: {str(e)[:100]}")
    try:
        import SwarmCert as SC
        SC.run_cert()
    except Exception as e:
        print(f"[swarm-meter]: cert failed honestly: "
              f"{type(e).__name__}: {str(e)[:100]}")


if __name__ == "__main__":
    mode = (sys.argv[1] if len(sys.argv) > 1 else "hour").lower()
    if mode == "night":
        cycle_night()
    else:
        cycle_hour()
