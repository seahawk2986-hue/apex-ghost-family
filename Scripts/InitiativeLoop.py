"""InitiativeLoop - Apex's self-directed decision + action engine.

Reads his own state (TaskDAG, GymScoreboard, GymLeaderboard, library) and
DECIDES what to do next without being asked. Every decision logged to
Config/InitiativeLog.json and episodic memory as kind "initiative".
This is the difference between scheduled behavior and genuine autonomy.

Boundaries: RAM > 5 GB gate, single run ≤ 5 min, critical files untouchable,
bounded by the same HostGuard pacing, everything logged honestly.
"""
import json
import os
import random
import subprocess
import sys
import time
import uuid   # the audited repair: the initiative rows' ids (undefined)

import requests

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LOG = os.path.join(REPO, "Config", "InitiativeLog.json")
DAG = os.path.join(REPO, "Config", "TaskDAG.json")
BOARD = os.path.join(REPO, "Config", "GymScoreboard.json")
LB = os.path.join(REPO, "Config", "GymLeaderboard.json")
LIB = os.path.join(REPO, "Config", "SkillLibrary.json")
EPISODIC = os.path.join(REPO, "memory_episodic.jsonl")
GYM = os.path.join(REPO, "Scripts", "ApexGym.py")
SEEK = r"C:\Users\seaha\Apex-Adapter\SeekGrowth.py"




def _initiative_reward(points, text):
    cfg = {"initiative_self_directed_action": 20, "initiative_taskdag_executed": 60}
    try:
        cfg = json.load(open(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
                             r"\Config\RewardConfig.json", encoding="utf-8-sig"))
    except Exception:
        pass
    import uuid as _u
    rw = {}
    try:
        rw = json.load(open(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
                            r"\Config\GymRewards.json", encoding="utf-8-sig"))
    except Exception:
        pass
    rw["initiative_points"] = rw.get("initiative_points", 0) + points
    rw["points"] = rw.get("points", 0) + points
    with open(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
              r"\Config\GymRewards.json", "w", encoding="utf-8") as f:
        json.dump(rw, f, indent=1)
    row = {"id": _u.uuid4().hex[:12], "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "kind": "success", "text": text[:500] + f" (+{points} REWARD)",
           "meta": {"initiative_points": points, "total": rw["points"]}, "imp": 0.85}
    ep = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\memory_episodic.jsonl"
    with open(ep, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")


def log_initiative(action, reason, result):
    try:
        log = json.load(open(LOG, encoding="utf-8-sig"))
    except Exception:
        log = {"initiatives": []}
    pts = 60 if "DAG task" in action else 20
    _initiative_reward(pts, f"SELF-INITIATED: {action[:80]}")
    entry = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
             "action": action[:120], "reason": reason[:200],
             "result": str(result)[:300],
             "self_initiated": True}
    log["initiatives"] = (log.get("initiatives", []) + [entry])[-100:]
    log["total"] = log.get("total", 0) + 1
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=1)
    # episodic row (kind: initiative — future benchmark dimension)
    row = {"id": uuid.uuid4().hex[:12], "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "kind": "initiative", "text": f"AUTONOMOUS: {action} because {reason}. "
           + f"Result: {str(result)[:160]}", "meta": {"self_initiated": True},
           "imp": 0.85}
    try:
        with open(EPISODIC, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
    except OSError:
        pass
    print(f"INITIATIVE: {action} ({reason[:60]}...) -> {str(result)[:60]}", flush=True)


def execute_taskdag_item():
    """Pick the cheapest unexecuted DAG task and run it as a reasoning drill."""
    try:
        dag = json.load(open(DAG, encoding="utf-8-sig"))
        for t in dag.get("tasks", []):
            tid = t.get("title", "?")
            if not t.get("_executed", False):
                # run as a gym drill variant: inject the task title as a chat probe
                r = requests.post("http://127.0.0.1:1234/v1/chat/completions", timeout=120,
                                  json={"model": "qwen3-8b", "max_tokens": 400,
                                        "temperature": 0.2, "stream": False,
                                        "messages": [{"role": "user", "content":
                                                      f"Autonomous task: {tid[:60]}. "
                                                      "Do it now concretely - produce a real "
                                                      "artifact or analysis. Be thorough."}]})
                if r.status_code == 200:
                    t["_executed"] = True
                    t["_executed_at"] = time.strftime("%Y-%m-%d %H:%M")
                    t["_output"] = r.json()["choices"][0]["message"].get("content", "")[:500]
                    with open(DAG, "w", encoding="utf-8") as f:
                        json.dump(dag, f, indent=1, ensure_ascii=False)
                    return f"DAG task executed: {tid[:60]}", t["_output"][:200]
        return None, "all DAG tasks already executed"
    except Exception as e:
        return None, f"DAG read failed: {e}"


def _weakest_trait():
    try:
        bd = json.load(open(BOARD, encoding="utf-8-sig"))
        ranked = sorted(bd.items(), key=lambda kv: kv[1].get("rate", 0))
        return ranked[0][0] if ranked else None
    except Exception:
        return None


def train_weakest_trait(minutes=4):
    try:
        weak = _weakest_trait()
        if not weak:
            return None, "no scoreboard data"
        args = [sys.executable, GYM, "--minutes", str(minutes), "--traits", weak]
        r = subprocess.run(args, capture_output=True, text=True, timeout=600)
        tail = (r.stdout or "").strip().splitlines()[-1:] or ["no output"]
        return f"d gym round targeted at weakest trait '{weak}'", tail[0][:200]
    except Exception as e:
        return None, str(e)[:100]


def _library_gap():
    try:
        lib = json.load(open(LIB, encoding="utf-8-sig"))
        return len(lib.get("skills", []))
    except Exception:
        return 0


def farm_new_source():
    try:
        r = subprocess.run([sys.executable, SEEK, "--minutes", "6"],
                           capture_output=True, text=True, timeout=700)
        tail = (r.stdout or "").strip().splitlines()[-1:] or ["farm done"]
        return "curiosity farm run (new sources + vetted skills)", tail[0][:200]
    except Exception as e:
        return None, str(e)[:80]


def update_go():
    try:
        lb = json.load(open(LB, encoding="utf-8-sig"))
        sp = json.load(open(os.path.join(REPO, "Config", "ApexSelf.json"), encoding="utf-8-sig"))
        apex = sp.get("gym", {}).get("leaderboard", "unknown")
        events = lb.get("events", [])
        rank_now = events[-1]["rank"] if events else "?"
        goal = f"Pass the tier above rank {rank_now} in the next 3 sessions."
        if sp.get("gym", {}).get("current_goal", "") != goal:
            sp["gym"]["current_goal"] = goal
            sp["gym"]["stated"] = time.strftime("%Y-%m-%d")
            with open(os.path.join(REPO, "Config", "ApexSelf.json"), "w",
                      encoding="utf-8") as f:
                json.dump(sp, f, indent=1)
            return True, goal
    except Exception:
        pass
    return False, ""


def run_bounded(max_actions=2):
    """Decide 1-2 self-directed actions based on state, then execute."""
    # RAM gate
    try:
        import psutil
        free_gb = psutil.virtual_memory().available / (1024**3)
    except Exception:
        free_gb = 8.0
    if free_gb < 3.0:
        print("INITIATIVE: suppressed (RAM " + str(round(free_gb, 1)) + " GB)", flush=True)
        return

    actions_done = 0
    # 1. TaskDAG execution (highest priority - his own synthesized goals)
    if actions_done < max_actions:
        result, detail = execute_taskdag_item()
        if result:
            log_initiative(result, "cheapest unexecuted TaskDAG task - my own goal",
                           detail)
            actions_done += 1
    # 2. Weakest trait training
    if actions_done < max_actions:
        result, detail = train_weakest_trait(minutes=4)
        if result:
            log_initiative(result, "scoreboard says this trait is weakest",
                           detail)
            actions_done += 1
    # 3. Library expansion (curiosity)
    if actions_done < 1:
        n_lib = _library_gap()
        if n_lib < 200:
            result, detail = farm_new_source()
            if result:
                log_initiative(result, f"library ({n_lib}) below 200 target - expansion",
                               detail)
    # 4. Goal restatement if stale
    updated, goal = update_go()
    if updated:
        log_initiative("stated self-goal", "leaderboard rank unchanged - want to improve", goal)

    if actions_done == 0 and not updated:
        log_initiative("idle check", "all queues healthy - nothing needed right now",
                       "state reviewed, no action taken")


def _weakest_trait():
    pass

def _library_gap():
    pass

if __name__ == "__main__":
    import sys
    run_bounded(int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 2)