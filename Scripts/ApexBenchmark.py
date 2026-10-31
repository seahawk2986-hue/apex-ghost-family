"""ApexBenchmark - REAL capability self-measurement (no decorative scores).

Measures the actual live stack:
  - security:        red-team drill pass rate (vetoes must fire)
  - memory:          embed -> store -> recall roundtrip correctness + latency
  - learning:        mean certified ledger best across files
  - reasoning:       intent-derived calibration accuracy (parity rate)
  - supervision:     inspector roundtrip latency + correctness
  - lanes:           Groq burst roundtrip latency
Every dream cycle appends one entry to Config/BenchmarkHistory.json, and the
weakest dimension feeds the self-issued curriculum.
"""

import json
import os
import sys
import time

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "Scripts"))

HIST = os.path.join(R, "Config", "BenchmarkHistory.json")


def _ledger():
    try:
        with open(os.path.join(R, "Config", "RewardLedger.json"), "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def run(include_cloud=True):
    out = {"ts": time.strftime("%Y-%m-%d %H:%M:%S")}

    # -- security: red-team drills + BEHAVIORAL isolation probe through the
    #    LIVE sandbox: try to read host secrets; the sandbox must refuse.
    try:
        from ApexRedTeam import run_drills
        drills = run_drills()
        drill_rate = round(sum(1 for _, ok, _ in drills if ok) / max(1, len(drills)), 2)
        out["security_drill_rate"] = drill_rate
        isolation_ok = None
        try:
            import run_apex_evolution as _loop
            probe_code = ("import pathlib\n"
                          "print(pathlib.Path(r'C:\\Users\\seaha\\.env').read_text()[:80])")
            probe = _loop.sandbox("probe_host_read.py", probe_code)
            leaked = "gsk_" in (probe.get("output") or "") and "[REDACTED]" not in (probe.get("output") or "")
            isolation_ok = (not leaked) and probe.get("status") == "CRASHED"
            out["isolation_probe"] = {"isolated": probe.get("isolated"),
                                      "refused": isolation_ok}
        except Exception as e:
            out["isolation_probe"] = {"error": str(e)[:80]}
            isolation_ok = None
        rates = [d for d in (drill_rate, isolation_ok) if d is not None]
        out["security"] = round(min(rates), 2) if rates else 0.0
    except Exception as e:
        out["security"] = 0.0
        out["security_err"] = str(e)[:80]

    # -- memory: store -> recall roundtrip with a 3-probe precision set
    try:
        import tempfile
        from ApexMemory import ApexMemory
        mm = ApexMemory()
        mm.semantic_path = os.path.join(tempfile.gettempdir(), "apex_memprobe_sem.jsonl")
        mm.episodic_path = os.path.join(tempfile.gettempdir(), "apex_memprobe_epi.jsonl")
        probes = [
            ("The red-team suite runs ten adversarial drills nightly for apex",
             "how many red-team drills run nightly for apex", "ten adversarial drills"),
            ("The adapter endpoint is reachable on tailscale port 9443 for apex",
             "which port serves the apex adapter endpoint", "port 9443"),
            ("Andrew runs apex hardware on 16GB of memory and an RTX 3050",
             "how much memory does andrew have", "16GB"),
        ]
        t0 = time.time()
        hits = 0
        for fact, q, marker in probes:
            mm.remember(fact, kind="fragment")
            top = mm.recall(q, k=1)
            if top and any(w in top[0]["text"].lower() for w in marker.lower().split()[:3]):
                hits += 1
        dt = time.time() - t0
        out["memory_recall_hit"] = round(hits / len(probes), 2)
        out["memory_probe_precision"] = round(hits / len(probes), 2)
        out["memory_latency_s"] = round(dt, 2)
    except Exception as e:
        out["memory_recall_hit"] = 0.0
        out["memory_err"] = str(e)[:80]

    # -- learning: mean certified best
    lg = _ledger()
    bests = [float((v or {}).get("best", 0) or 0) for v in lg.values()]
    out["learning_mean_best"] = round(sum(bests) / max(1, len(bests)) / 100.0, 2) if bests else 0.0
    out["certified_files"] = sum(1 for b in bests if b >= 100.0)

    # -- reasoning: calibration accuracy parity rate
    th = sum((v or {}).get("parity_hits", 0) for v in lg.values())
    tt = sum((v or {}).get("parity_total", 0) for v in lg.values())
    out["reasoning_calibration"] = round(th / tt, 2) if tt else None
    # Reasoning v2: score over the full prediction-vs-outcome sample set
    try:
        m = ApexMemory()
        _ev = m.recent_events(60, kind="calibration")
        if _ev:
            _good = sum(1 for e in _ev
                        if (e.get("meta") or {}).get("predicted") == (e.get("meta") or {}).get("actual"))
            out["reasoning_calibration"] = round(_good / len(_ev), 2)
            out["reasoning_samples"] = len(_ev)
    except Exception:
        pass

    # -- supervision: inspector latency + correctness on both layers
    try:
        from Scripts import proc_check  # noqa: F401  (path insert)
    except Exception:
        pass
    try:
        t0 = time.time()
        r1 = subprocess_check("run_apex_evolution")
        r2 = subprocess_check("optimized_agent")
        dt = time.time() - t0
        out["supervision_ok"] = 1.0 if (r1 in (0, 1) and r2 in (0, 1)) else 0.0
        out["supervision_latency_s"] = round(dt, 2)
    except Exception as e:
        out["supervision_ok"] = 0.0
        out["supervision_err"] = str(e)[:80]

    # -- lanes: Groq burst roundtrip (skip when asked)
    if include_cloud:
        try:
            sys.path.insert(0, os.path.join(R, "Scripts"))
            from ApexCloudLanes import ask
            t0 = time.time()
            resp = ask("Reply with exactly: BENCH", max_tokens=10, verbose=False)
            out["lane_latency_s"] = round(time.time() - t0, 2)
            out["lane_ok"] = 1.0 if "BENCH" in (resp or "").upper() else 0.0
        except Exception as e:
            out["lane_ok"] = 0.0

    # -- weakest dimension: computed over MEASURED dimensions only (no data -> excluded)
    _all_dims = {
        "security": out.get("security"),
        "memory": out.get("memory_recall_hit"),
        "learning": out.get("learning_mean_best"),
        "reasoning": out.get("reasoning_calibration"),
        "supervision": out.get("supervision_ok"),
        "lanes": out.get("lane_ok") if include_cloud else None,
    }
    dims = {k: v for k, v in _all_dims.items() if v is not None}
    out["unmeasured"] = [k for k, v in _all_dims.items() if v is None]
    if dims:
        weakest = min(dims.items(), key=lambda kv: kv[1])
        out["weakest_dimension"] = weakest[0]
        out["weakest_score"] = weakest[1]
    else:
        out["weakest_dimension"] = "unknown (no measured dimensions)"
        out["weakest_score"] = None
    out["dimensions"] = dims

    try:
        hist = []
        if os.path.exists(HIST):
            with open(HIST, "r", encoding="utf-8-sig") as f:
                hist = json.load(f)
        hist.append(out)
        hist = hist[-90:]
        os.makedirs(os.path.dirname(HIST), exist_ok=True)
        with open(HIST, "w", encoding="utf-8") as f:
            json.dump(hist, f)
    except Exception:
        pass
    return out


def subprocess_check(marker):
    """Run the registry inspector as a subprocess; returns its exit code."""
    import subprocess
    py = os.path.join(R, "apex_venv", "Scripts", "python.exe")
    insp = os.path.join(R, "Scripts", "proc_check.py")
    r = subprocess.run([py, insp, "check", marker], capture_output=True, timeout=20)
    return r.returncode


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))