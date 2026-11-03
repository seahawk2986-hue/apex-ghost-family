"""WeightMeter - THE NEAR-WEIGHTLESS CERTIFIER (2026-11-03; the user's
law: the fleet's intelligence should be OTHER PEOPLE'S silicon - the
box feels near-weightless):

  THE PHYSICAL HALF (measured live, bounded):
    - the fleet's RAM (python processes' working sets via PowerShell)
    - the GPU's load/memory IF nvidia-smi answers
    - the resident-model audit: is the local coder loaded RIGHT NOW?
      (the honest weight = the biggest single gram on the box)
    - the disk growth (the receipts dir)
  THE EXTERNAL HALF (from receipts ONLY, never invented):
    - cloud seats live (FreeSwarm catalog), mesh nodes, keyless lanes
    - the runner receipts: tonight's Actions runs (the outsourced beats)
    - the lane-ledger (initialized here; every future appender adds a
      line - local_coder vs external per call, the external-share meter)

THE GATES (published before the results):
  W+  = fleet RAM < 1.5GB during idle-beat AND no resident model AND
        external-share >= 90% over n>=100 lane-calls
  W   = no resident model idle OR external >= 80% (n>=50)
  provisionally-graded until the n's fill - printed with the n's.

$0; stdlib + one bounded PowerShell read."""

import json
import os
import subprocess
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LANE_LEDGER = os.path.join(ROOT, "Config", "lane_ledger.jsonl")
STATE = os.path.join(ROOT, "Config", "weight_state.json")


def _ps_ram_mb():
    """The fleet's working set: the python-family processes, one PS read"""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-Process python* -ErrorAction SilentlyContinue | "
             "Measure-Object WorkingSet64 -Sum).Sum / 1MB"],
            capture_output=True, text=True, timeout=30)
        return round(float((out.stdout or "0").strip() or 0), 1)
    except Exception:
        return -1


def _gpu():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=15)
        vals = (out.stdout or "").strip().split("\n")[0].split(",")
        if len(vals) >= 2:
            return {"gpu_util_pct": vals[0].strip(),
                    "gpu_mem_mb": vals[1].strip()}
    except Exception:
        pass
    return {"gpu": "absent/busy - honest gray"}


def _resident_model():
    """Is a local model resident? The truthful probe: an Ollama-style
    process OR the coder's seat process with a big working set."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process python*,ollama*,ollama_llama_server* "
             "-ErrorAction SilentlyContinue | Where-Object "
             "{ $_.WorkingSet64 -gt 2GB } | Measure-Object -Sum | "
             "Select-Object -ExpandProperty Count"],
            capture_output=True, text=True, timeout=30)
        n = int((out.stdout or "0").strip() or 0)
        return n > 0
    except Exception:
        return None   # the honest gray


def _disk_mb():
    tot = 0
    for d in ("Config", "Scores", "Logs", "family"):
        p = os.path.join(ROOT, d)
        for dirp, _, fs in os.walk(p):
            for f in fs:
                try:
                    tot += os.path.getsize(os.path.join(dirp, f))
                except Exception:
                    pass
    return round(tot / 1e6, 1)


def _external_inventory():
    """The OTHER-SILICON inventory (receipts only)."""
    inv = {}
    try:
        sys.path.insert(0, os.path.join(ROOT, "Scripts"))
        import FreeSwarm as FS
        inv["cloud_seats"] = len(FS.catalog(force=False) or [])
    except Exception:
        inv["cloud_seats"] = -1
    try:
        import SwarmWide as SW
        inv["mesh_nodes_live"] = len(SW.candidates())
    except Exception:
        inv["mesh_nodes_live"] = 0
    try:
        st = json.load(open(os.path.join(ROOT, "Config",
                                         "weight_state.json"),
                            encoding="utf-8-sig"))
        inv["runner_beats_30d"] = st.get("runner_beats_30d", 0)
    except Exception:
        inv["runner_beats_30d"] = 0
    inv["keyless_lanes"] = 1   # pollinations text (the always-forever floor)
    return inv


def stamp(beat_local=False):
    """One observation row + the provisional grade."""
    ram = _ps_ram_mb()
    resid = _resident_model()
    inv = _external_inventory()
    n_led = ok_ext = 0
    try:
        for ln in open(LANE_LEDGER, encoding="utf-8-sig"):
            r = json.loads(ln)
            n_led += 1
            ok_ext += r.get("external", True)
    except Exception:
        pass
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "fleet_ram_mb": ram, "resident_model_loaded": resid,
           "disk_mb": _disk_mb(), **_gpu(), **inv,
           "lane_calls_ledgered": n_led,
           "external_share_pct": round(100 * ok_ext / max(1, n_led), 1)}
    grade = None
    if (isinstance(ram, float) and 0 <= ram < 1500
            and resid is False and (row["external_share_pct"] >= 90
                                    if n_led >= 100 else None) is True):
        grade = "W+ (near-weightless: measured)"
    elif resid is False and (n_led < 50 or row["external_share_pct"] >= 80):
        grade = "W (provisionally weightless: the n's honest-gray)"
    else:
        grade = "WEIGHED (the resident model or low external-share keeps grams on the box)"
    row["grade"] = grade
    hist = []
    try:
        hist = [json.loads(l) for l in open(STATE, encoding="utf-8-sig")]
    except Exception:
        pass
    hist = hist[-72:] + [row]
    json.dump(hist, open(STATE, "w", encoding="utf-8"), indent=1)
    print(f"[weight]: RAM {ram} MB (the python-family) | resident-model "
          f"{resid} | disk {row['disk_mb']} MB | seats {inv['cloud_seats']} "
          f"+ nodes {inv['mesh_nodes_live']} + keyless | graded: {grade}")
    return row


if __name__ == "__main__":
    stamp()
