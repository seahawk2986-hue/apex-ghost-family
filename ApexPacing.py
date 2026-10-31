"""
ApexPacing - Built-in breaks against taxing the host hardware.

Policy (user directive: one restraint = protect the machine):
  * Every Apex work cycle first checks host telemetry (same thresholds as the
    installer governor: free RAM >= 2GB, CPU <= 85%, disk >= 5GB on project drive).
  * Healthy host: normal cycle pacing (default 15s between cycles).
  * Strained host: escalating cooldown ladder 60s -> 180s -> 300s -> 600s until
    telemetry recovers. The break is LOGGED and RECORDED to memory (rate-limited)
    so the planner can see its own physiotherapy in recall.
  * Anything that would destabilize the host (reboot/shutdown/killing user apps)
    stays forever human-only (see ApexInstaller.FORBIDDEN_COMMANDS).

Also exposes can_use_local_models(): the room adapter consults this before
touching LM Studio, so local inference is skipped entirely when the host is
under strain - preventing the RAM-spill death spiral at the source.

Note: ApexInstaller.py is a thin wrapper with no complex logic to optimize.
Focus remains on ApexPacing for stability and pacing efficiency.
"""

import json
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(ROOT, "Logs", "pacing.log")

BASE_CYCLE_S = 15
STRESS_LADDER = (60, 180, 300, 600)   # escalating breaks

try:
    from ApexInstaller import hardware_ok, load_guard
    from ApexInstaller import FORBIDDEN_COMMANDS  # noqa: F401 (policy reference)
except Exception:
    hardware_ok = load_guard = None
    FORBIDDEN_COMMANDS = ("shutdown", "restart-computer", "stop-computer", "logoff")

try:
    sys_path = os.path.join(ROOT)
    import sys as _sys
    if sys_path not in _sys.path:
        _sys.path.insert(0, sys_path)
    from ApexMemory import ApexMemory
except Exception:
    ApexMemory = None


def _log(msg):
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {msg}"
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
    print(line)


class Pace:
    def __init__(self):
        self.stress_streak = 0
        self.healthy_streak = 0
        self._last_mem_event = 0.0

    def _memory_note(self, text):
        # Rate-limit: at most one memory note per 10 minutes per stress episode.
        now = time.time()
        if now - self._last_mem_event < 600:
            return
        self._last_mem_event = now
        try:
            if ApexMemory:
                ApexMemory().record_event("error", f"Hardware pacing: {text}")
                ApexMemory().remember(f"Built-in break taken: {text}", kind="lesson")
        except Exception:
            pass

    def next_delay(self, base=BASE_CYCLE_S):
        """Seconds to wait before the next work cycle (no sleeping)."""
        if hardware_ok is None:
            return base
        ok, reason = hardware_ok(load_guard())
        _ = json  # guard import retained for config future use
        if not ok:
            self.stress_streak += 1
            self.healthy_streak = 0
            idx = min(self.stress_streak - 1, len(STRESS_LADDER) - 1)
            wait = STRESS_LADDER[idx]
            _log(f"BREAK {wait}s (stress #{self.stress_streak}): {reason}")
            if self.stress_streak == 1:
                self._memory_note(f"host under strain ({reason}); Apex is pacing itself down.")
            return wait
        if self.stress_streak:
            _log(f"recovered after {self.stress_streak} paced cycle(s): {reason}")
        self.stress_streak = 0
        self.healthy_streak += 1
        return base

    def sleep_between_cycles(self, base=BASE_CYCLE_S):
        wait = self.next_delay(base)
        time.sleep(wait)
        return wait


def can_use_local_models():
    """True when the host has headroom for local LM inference."""
    if hardware_ok is None:
        return True, "governor unavailable - assuming OK"
    return hardware_ok(load_guard())


PACER = Pace()

if __name__ == "__main__":
    ok, reason = can_use_local_models()
    print(f"local models allowed now: {ok} ({reason})")
    print(f"next cycle delay would be: {PACER.next_delay()}s")
