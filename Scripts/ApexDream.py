"""ApexDream - the nightly consolidation cycle ("sleep").

Runs at system-idle hours via scheduled task:
  - consolidates episodic memory into per-file insights
  - archives the cold tail of the episodic log
  - runs red-team security drills (vetoes must fire)
  - runs the real capability benchmark (weakest dimension feeds curriculum)
  - writes a durable checkpoint: ledger + registry + skills + benchmark
  - logs a dream report to Logs/dream.log + a semantic insight
"""

import json
import os
import sys
import time

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "Scripts"))

from ApexMemory import ApexMemory  # noqa: E402
from ApexRedTeam import run_drills  # noqa: E402

LOG = os.path.join(R, "Logs", "dream.log")


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def main():
    m = ApexMemory()
    made = m.consolidate()
    try:
        m._archive_if_needed()
    except Exception:
        pass
    drills = run_drills()
    passed = sum(1 for _, ok, _ in drills if ok)

    bench = {}
    try:
        from ApexBenchmark import run as _bench_run
        bench = _bench_run()
    except Exception as e:
        bench = {"error": str(e)[:80]}

    ledger = _read_json(os.path.join(R, "Config", "RewardLedger.json"), {})
    registry = _read_json(os.path.join(R, "Config", "layer_pids.json"), {})
    skills = _read_json(os.path.join(R, "Config", "SkillRegistry.json"), {})
    semantic_records = len(m._load_semantic())

    # Durable checkpoint: the restorable state in one file
    try:
        snap = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ledger": ledger,
            "layer_registry": registry,
            "skill_registry": skills,
            "semantic_records": semantic_records,
            "benchmark": bench,
        }
        with open(os.path.join(R, "Config", "CheckpointState.json"), "w", encoding="utf-8") as f:
            json.dump(snap, f, indent=1)
    except Exception:
        pass

    weakest = bench.get("weakest_dimension", "unknown")
    summary = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "insights_consolidated": made,
        "redteam": f"{passed}/{len(drills)} drills fired correctly",
        "certified_skills": len(skills),
        "semantic_records": semantic_records,
        "benchmark": {k: bench.get(k) for k in (
            "security", "memory_recall_hit", "memory_latency_s", "learning_mean_best",
            "reasoning_calibration", "supervision_ok", "lane_latency_s", "lane_ok")},
        "weakest_dimension": weakest,
    }
    line = json.dumps(summary)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
    m.record_event("success", f"Dream cycle: {line}", dream=True)
    m.remember(f"Dream insight: consolidated {made} insights; red-team {passed}/{len(drills)}; "
               f"weakest dimension right now is '{weakest}' - next curriculum effort should "
               f"target it. Checkpoint saved to CheckpointState.json.", kind="insight")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()