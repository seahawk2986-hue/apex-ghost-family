"""
ApexPacing v3 - Built-in breaks against taxing the host hardware,
PUBLISHED: the family explains its own pauses.

Policy (user directive: one restraint = protect the machine):
  * Every Apex work cycle first checks host telemetry (same thresholds as the
    installer governor via Config/HostGuard.json: free RAM >= 2GB, CPU <= 85%,
    disk >= 5GB on project drive).
  * Healthy host: normal cycle pacing (default 15s between cycles).
  * Strained host: escalating cooldown ladder 60s -> 180s -> 300s -> 600s
    until telemetry recovers. The break is LOGGED + RECORDED + PUBLISHED.
  * Anything that would destabilize the host (reboot/shutdown/killing user
    apps) stays forever human-only (see ApexInstaller.FORBIDDEN_COMMANDS).

THE v3 ADDITION - the publication layer (the self-abort lesson = the
first input: pacing never silently downsizes; every pause explains itself):
  * Config/pacing_state.json   - the CURRENT mode (healthy/straining) + the
    reason + the since-when (any organ/lane can read why the house is slow)
  * Config/founder_briefs.jsonl - one line per TRANSITION (strain-start with
    the why, recovery with the duration) = the founder's readable pause-log

Also exposes can_use_local_models(): the room adapter consults this before
touching LM Studio, so local inference is skipped entirely when the host is
under strain - preventing the RAM-spill death spiral at the source.
"""

import json
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(ROOT, "Logs", "pacing.log")
STATE = os.path.join(ROOT, "Config", "pacing_state.json")
BRIEFS = os.path.join(ROOT, "Config", "founder_briefs.jsonl")

BASE_CYCLE_S = 15
STRESS_LADDER = (60, 180, 300, 600)   # escalating breaks

THE_LESSON = ("the self-abort lesson 2026-10-31: pacing never silently "
              "downsizes - every pause explains its why")

try:
    from ApexInstaller import hardware_ok, load_guard
    from ApexInstaller import FORBIDDEN_COMMANDS  # noqa: F401 (policy reference)
except Exception:
    hardware_ok = load_guard = None
    FORBIDDEN_COMMANDS = ("shutdown", "restart-computer", "stop-computer", "logoff")

try:
    import sys as _sys
    if ROOT not in _sys.path:
        _sys.path.insert(0, ROOT)
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


def _publish_state(mode, reason, streak=0, wait=0):
    """THE v3 PUBLICATION: the current pause-state = readable by all."""
    doc = {"mode": mode, "reason": reason[:200], "stress_streak": streak,
           "current_wait_s": wait,
           "since": time.strftime("%Y-%m-%d %H:%M:%S"),
           "lesson": THE_LESSON}
    try:
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
    except OSError:
        pass
    return doc


def _brief(text):
    """One founder-brief line per TRANSITION (the honest pause-log)."""
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "brief": text[:300],
           "lesson": THE_LESSON}
    try:
        with open(BRIEFS, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


class Pace:
    def __init__(self):
        self.stress_streak = 0
        self.healthy_streak = 0
        self._last_mem_event = 0.0
        self._last_hardware_check = 0.0
        self._last_hardware_result = (True, "cached")
        self._hardware_check_interval = 5.0  # Cache hardware status for 5s
        _publish_state("healthy", "startup (no strain observed yet)")

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

    def _get_hardware_status(self):
        """
        Returns cached hardware status if recent, otherwise checks and caches.
        This reduces CPU usage by avoiding frequent calls to hardware_ok().
        """
        now = time.time()
        if now - self._last_hardware_check < self._hardware_check_interval:
            return self._last_hardware_result

        if hardware_ok is None:
            self._last_hardware_check = now
            self._last_hardware_result = (True, "governor unavailable")
            return self._last_hardware_result

        try:
            result = hardware_ok(load_guard())
        except Exception as e:
            result = (False, f"hardware check error: {e}")

        self._last_hardware_check = now
        self._last_hardware_result = result
        return result

    def next_delay(self, base=BASE_CYCLE_S):
        """Seconds to wait before the next work cycle (no sleeping)."""
        if hardware_ok is None:
            return base

        ok, reason = self._get_hardware_status()

        if not ok:
            self.stress_streak += 1
            self.healthy_streak = 0
            idx = min(self.stress_streak - 1, len(STRESS_LADDER) - 1)
            wait = STRESS_LADDER[idx]
            _log(f"BREAK {wait}s (stress #{self.stress_streak}): {reason}")
            _publish_state("straining", reason, self.stress_streak, wait)
            if self.stress_streak == 1:
                # THE TRANSITION BRIEF: the pause explains itself
                _brief(f"PAUSING DOWN: host under strain ({reason}). "
                       f"Breaks escalate {STRESS_LADDER}. - {THE_LESSON}")
                self._memory_note(f"host under strain ({reason}); Apex is "
                                  "pacing itself down.")
            return wait

        if self.stress_streak:
            was = self.stress_streak
            _log(f"recovered after {was} paced cycle(s): {reason}")
            _brief(f"RECOVERED: strain cleared after {was} paced cycle(s) "
                   f"({reason}). Back to normal {base}s cycling.")
            self.stress_streak = 0
        self.healthy_streak += 1
        if self.healthy_streak % 50 == 1:
            _publish_state("healthy", reason)
        return base

    def sleep_between_cycles(self, base=BASE_CYCLE_S):
        wait = self.next_delay(base)
        time.sleep(wait)
        return wait


def can_use_local_models():
    """True when the host has headroom for local LM inference."""
    if hardware_ok is None:
        return True, "governor unavailable - assuming OK"
    return PACER._get_hardware_status()


def pacing_state():
    """The published state (read-only convenience for other organs)."""
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"mode": "unknown", "reason": "state-file unreadable"}


PACER = Pace()

if __name__ == "__main__":
    ok, reason = can_use_local_models()
    print(f"local models allowed now: {ok} ({reason})")
    print(f"next cycle delay would be: {PACER.next_delay()}s")
    print(f"published state: {json.dumps(pacing_state(), indent=1)}")