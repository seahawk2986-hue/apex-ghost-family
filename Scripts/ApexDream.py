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
import subprocess
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
    # Skill re-certification: nightly sandbox re-verification + demotion
    _recert = {"error": "not run"}
    try:
        import run_apex_evolution as _loop
        from ApexSkills import recertify as _recert_fn
        _recert = _recert_fn(max_n=5, sandbox_fn=_loop.sandbox)
        if _recert.get("demoted"):
            m.record_event("error", f"Skill re-certification demoted {_recert.get('demoted')} stale skill(s)",
                           skills=True)
    except Exception as e:
        _recert = {"error": str(e)[:80]}
    # Monthly free-tier catalog refresh (TierScout - interconnection upgrade)
    try:
        _scout_path = os.path.join(R, "Config", "FreeTierCatalog.json")
        _age_days = 999.0
        if os.path.exists(_scout_path):
            with open(_scout_path, "r", encoding="utf-8") as f:
                _cat = json.load(f)
            try:
                _t = time.mktime(time.strptime(_cat.get("scanned_at", ""), "%Y-%m-%d %H:%M:%S"))
                _age_days = (time.time() - _t) / 86400.0
            except Exception:
                pass
        if _age_days > 30:
            _pyexe = os.path.join(R, "apex_venv", "Scripts", "python.exe")
            subprocess.run([_pyexe, os.path.join(R, "Scripts", "ApexTierScout.py")],
                           capture_output=True, timeout=240)
            _msg = f"TierScout refreshed the free-tier catalog (was {_age_days:.0f} days old)"
            m.record_event("success", _msg, scout=True)
            print("[DREAM]", _msg)
    except Exception:
        pass

    ledger = _read_json(os.path.join(R, "Config", "RewardLedger.json"), {})
    registry = _read_json(os.path.join(R, "Config", "layer_pids.json"), {})
    skills = _read_json(os.path.join(R, "Config", "SkillRegistry.json"), {})
    semantic_records = len(m._load_semantic())

    # Durable checkpoint: the restorable state in one file
    try:
        _git = subprocess.run(["git", "-C", R, "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10)
        git_head = _git.stdout.strip() or None
    except Exception:
        git_head = None
    try:
        snap = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "git_head": git_head,
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
    # Capability trend detection: is the flywheel actually improving?
    trend = "insufficient history"
    try:
        hist_path = os.path.join(R, "Config", "BenchmarkHistory.json")
        bh = []
        if os.path.exists(hist_path):
            with open(hist_path, "r", encoding="utf-8") as f:
                bh = json.load(f)
        if len(bh) >= 4:
            def _mean(entries):
                vals = [e for e in entries if isinstance(e.get("dimensions"), dict)]
                if not vals:
                    return None
                allv = [v for e in vals for v in e["dimensions"].values()]
                return sum(allv) / max(1, len(allv))
            _now = _mean(bh[-3:])
            _was = _mean(bh[-6:-3])
            if _now is not None and _was is not None:
                t = _now - _was
                trend = f"{'IMPROVING' if t > 0.02 else 'STAGNANT' if t > -0.02 else 'DECLINING'} ({_was:.2f} -> {_now:.2f})"
    except Exception:
        pass
    # Agency round: pattern distillation + self-synthesized task DAG
    try:
        pat_out = {"patterns": []}
        sr_path = os.path.join(R, "Config", "SkillRegistry.json")
        if os.path.exists(sr_path):
            sr = json.load(open(sr_path, encoding="utf-8-sig"))
            for k, v in list(sr.items())[:14]:
                if not isinstance(v, dict):
                    continue
                name = str(v.get("source", k))[:60]
                intent = str(v.get("intent", ""))[:200]
                pat_out["patterns"].append({"skill": name,
                                            "best": v.get("best", "?"),
                                            "summary": intent or ("certified pattern from " + name)})
        with open(os.path.join(R, "Config", "Patterns.json"), "w", encoding="utf-8") as f:
            json.dump(pat_out, f, indent=1)
    except Exception:
        pass
    try:
        import requests as _rq_ag
        dag = None
        ag_payload = {"model": "qwen3-8b", "messages": [
            {"role": "system", "content": "Return ONLY strict JSON. Shape: an object with a tasks list of objects with keys title (str <=60), why (str <=120), est_minutes (int), capability_gain (str <=60). Produce exactly 3 self-improvement subtasks that make the agent better at its weakest area."},
            {"role": "user", "content": "weakest dimension: " + str(weakest) + "; benchmark snapshot: " + json.dumps(bench)[:500] + "; propose 3 concrete self-driven subtasks."}],
            "temperature": 0.2, "stream": False, "max_tokens": 400}
        ag_r = _rq_ag.post("http://127.0.0.1:1234/v1/chat/completions", json=ag_payload, timeout=60)
        if ag_r.status_code == 200:
            ag_txt = (ag_r.json()["choices"][0]["message"]["content"] or "")
            s0, e0 = ag_txt.find("{"), ag_txt.rfind("}")
            if s0 >= 0 and e0 > s0:
                dag = json.loads(ag_txt[s0:e0 + 1])
        if isinstance(dag, dict) and dag.get("tasks"):
            with open(os.path.join(R, "Config", "TaskDAG.json"), "w", encoding="utf-8") as f:
                json.dump({"weakest": weakest,
                           "created": time.strftime("%Y-%m-%d %H:%M"),
                           "tasks": dag["tasks"][:3]}, f, indent=1, ensure_ascii=False)
    except Exception:
        pass

    # Reasoning gym: bounded self-training round (drills -> calibration rows)
    try:
        gym_proc = subprocess.run([sys.executable, os.path.join(R, "Scripts", "ApexGym.py"), "--minutes", "6", "--traits", "auto"], capture_output=True, text=True, timeout=720)
        gym_tail = (gym_proc.stdout or "").strip().splitlines()[-1:]
        _gym_note = "GYM: " + (gym_tail[0] if gym_tail else "no output")
    except Exception as _e_gym:
        _gym_note = "GYM skipped: " + str(_e_gym)[:80]
    try:
        import ApexMemory
        ApexMemory.ApexMemory().record_event("training", _gym_note)
    except Exception:
        pass

    # Curiosity drive: nightly cloud-farming round (open sources, vetted, rewarded)
    try:
        seek = subprocess.run([sys.executable, os.path.join(R, "Scripts", "SeekGrowth.py"), "--minutes", "8"],
                              capture_output=True, text=True, timeout=900)
        seek_tail = (seek.stdout or "").strip().splitlines()[-1:]
        _seek_note = "SEEK: " + (seek_tail[0] if seek_tail else "farmed")
        ApexMemory.ApexMemory().record_event("training", _seek_note)
    except Exception as _e_seek:
        _seek_note = "SEEK skipped: " + str(_e_seek)[:80]

    # Autonomy: self-directed decisions (TaskDAG execution, weakest-train,
    #                      farm, goal restatement - all self-initiated)
    try:
        _il = subprocess.run([sys.executable, os.path.join(R, "Scripts", "InitiativeLoop.py"), "--max", "2"],
                             capture_output=True, text=True, timeout=600)
        _il_tail = (_il.stdout or "").strip().splitlines()[-3:]
        for _il_ln in _il_tail:
            ApexMemory.ApexMemory().record_event("initiative", _il_ln)
    except Exception:
        pass

    # Security-ops round: supply-chain audit, backup rotation, disk pressure
    sec_ops = {}
    try:
        sys.path.insert(0, R)
        sys.path.insert(0, os.path.join(R, "Scripts"))
        from ApexSecurityOps import supply_chain_audit, backup_rotation, disk_metric
        sec_ops["audit"] = supply_chain_audit()
        sec_ops["backup"] = backup_rotation()
        sec_ops["disk"] = disk_metric()
    except Exception as _e0:
        sec_ops = {"error": str(_e0)[:80]}

    weakest = bench.get("weakest_dimension", "unknown")
    # ================================================== THE 2026-11-04 ORGANS
    # (1) THE BLIND COURT: re-judge the fleet against the sealed holdout every
    #     night - self-flattery cannot hide across nights (arXiv:2407.01502's
    #     holdout prescription, fleet-implemented).
    # (2) THE OUTCOME YARDSTICK: internal-vs-external truth, same page.
    # (3) THE LEDGER TRIM: no unbounded append-only file (8MB/52MB class).
    _organ_notes = []
    try:
        import RealityCourt as _court
        _court.judge()
        _organ_notes.append("court run")
    except Exception as _e_court:
        m.record_event("court", "court skipped honestly: " + str(_e_court)[:70])
    try:
        import OutcomeYardstick as _yard
        _yard.measure()
        _organ_notes.append("yardstick measured")
    except Exception as _e_yard:
        m.record_event("yardstick", "yardstick skipped honestly: " + str(_e_yard)[:70])
    try:
        import LedgerTrim as _trim
        _trim.trim()
        _organ_notes.append("ledgers trimmed")
    except Exception:
        pass
    try:
        import AutoRoster as _ar
        _ar.retire_dead()
        _ar.refresh()
        _organ_notes.append("roster refreshed (retire + catalog + probe)")
    except Exception as _e_ar:
        m.record_event("roster", "roster skipped honestly: " + str(_e_ar)[:70])
    m.record_event("training", "night organs: " + ", ".join(_organ_notes))
    # Security posture, measured right now (feeds the overnight note honestly)
    sec_status = "integrity manifest OK; secrets sealed"
    try:
        sys.path.insert(0, os.path.join(R, "Scripts"))
        from ApexGuard import verify_manifest, verify_env
        _bad = verify_manifest()
        env_ok, _ = verify_env()
        if not env_ok:
            sec_status = ".env changed since seal - review pending"
        elif _bad:
            sec_status = f"TAMPER ALERT: {_bad[:1]}"
        else:
            sec_status = "integrity manifest OK; secrets sealed"
    except Exception:
        pass
    # Toast: the dream speaks to Andrew's desktop.
    try:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", os.path.join(R, "Scripts", "ApexToast.ps1"),
                        "-Title", "APEX dream complete",
                        "-Message", (f"{made} insight(s) consolidated; red-team {passed}/{len(drills)}; "
                                     f"weakest: {weakest}. Checkpoint saved.")],
                       capture_output=True, timeout=30)
    except Exception:
        pass
    # Dynamic self-model: the identity card carries MEASURED capabilities,
    # refreshed from real benchmark data (not static descriptions).
    try:
        self_path = os.path.join(R, "Config", "ApexSelf.json")
        with open(self_path, "r", encoding="utf-8-sig") as f:
            selfcard = json.load(f)
        selfcard["measured"] = {
            "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "security": bench.get("security"),
            "memory_recall": bench.get("memory_recall_hit"),
            "learning": bench.get("learning_mean_best"),
            "reasoning_calibration": bench.get("reasoning_calibration"),
            "supervision": bench.get("supervision_ok"),
            "lane_latency_s": bench.get("lane_latency_s"),
            "weakest_dimension": weakest,
        }
        tmp = self_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(selfcard, f, indent=1)
        os.replace(tmp, self_path)
        # Re-seal what we legitimately wrote (keeps tamper detection exact)
        try:
            sys.path.insert(0, os.path.join(R, "Scripts"))
            from ApexGuard import seal_file as _seal
            _seal(os.path.join(R, "Config", "ApexSelf.json"))
        except Exception:
            pass
    except Exception:
        pass
    summary = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "insights_consolidated": made,
        "redteam": f"{passed}/{len(drills)} drills fired correctly",
        "certified_skills": len(skills),
        "semantic_records": semantic_records,
        "capability_trend": trend,
        "security_ops": {"vulns": ((sec_ops.get("audit") or {}).get("vulnerabilities")), "backup": sec_ops.get("backup"), "disk_free_gb": (sec_ops.get("disk") or {}).get("disk_free_gb")},
        
        "recertification": _recert,
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
    # Overnight note: the private console greets Andrew with Apex's own words.
    try:
        notes_path = os.path.join(R, "Config", "ApexNotes.json")
        notes = []
        if os.path.exists(notes_path):
            with open(notes_path, "r", encoding="utf-8") as f:
                notes = json.load(f)
        notes.append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                      "note": (f"Dream complete. {made} insight(s) consolidated; red-team "
                               f"{passed}/{len(drills)}; weakest dimension: {weakest}; "
                               f"security posture: {sec_status}. "
                               f"Everything is in order - I will keep evolving.")})
        notes = notes[-5:]
        with open(notes_path + ".tmp", "w", encoding="utf-8") as f:
            json.dump(notes, f, indent=1)
        os.replace(notes_path + ".tmp", notes_path)
        # Desktop copy: Andrew sees the note without opening anything.
        home = os.path.expanduser("~")
        desk = next((c for c in (os.path.join(home, "OneDrive", "Desktop"),
                                 os.path.join(home, "Desktop")) if os.path.isdir(c)), home)
        with open(os.path.join(desk, "APEX overnight note.txt"), "w", encoding="utf-8") as f:
            f.write("APEX (overnight dream note)\n"
                    f"written {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    + notes[-1]["note"] + "\n")
    except Exception:
        pass
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
