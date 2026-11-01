"""Deploy 3 ghost-shard workers (code/science/archive) - the production launcher.
Called by the hourly scheduled task; each shard self-gates (RAM >= 2 GB) and
dissolves when its territory's round ends."""
import json
import time
import os
import subprocess

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PY = ROOT + r"\apex_venv\Scripts\python.exe"

# EVOLUTION: family variants ranked by measured fitness; the fleet spawns as
# 70pct best-lineage (slight jitter) + 30pct random explorers (explore/exploit)
MUTABLE = ["ghost_max_readmes", "ghost_backlog_readmes", "ghost_leads_per_vein",
           "ghost_tarball_max", "ghost_deep_readmes"]

def _family():
    """Family genetics with the NO-REGRESSION RATCHET:
    - variants below the floor (fitness < 8pct of best, or < 0.02 absolute)
      are EVICTED - dead-end genes never inherit;
    - the best-lineage pointer only moves forward: a challenger must beat the
      incumbent by >2pct to take the throne."""
    try:
        pmv = json.load(open(os.path.join(ROOT, "Config", "PathMemory.json"),
                             encoding="utf-8-sig"))
        variants = pmv.get("variants", {})
        # eviction pass: dead lines die in the file, not just in memory
        if variants:
            best_f = max(float(v.get("fitness", 0)) for v in variants.values())
            floor = max(0.02, 0.08 * best_f)
            dead = [k for k, v in variants.items()
                    if float(v.get("fitness", 0)) < floor]
            for k in dead:
                del variants[k]
            if dead:
                pmv["variants"] = variants
                json.dump(pmv, open(os.path.join(ROOT, "Config", "PathMemory.json"),
                                    "w", encoding="utf-8"), indent=1)
        ranked = sorted(variants.items(), key=lambda kv: -kv[1].get("fitness", 0))
        # monotonic adoption: the record-holder defends its title
        if ranked:
            champ = pmv.setdefault("family", {}).get("champion")
            if champ and champ in [k for k, _v in ranked]:
                cf = float(variants.get(champ, {}).get("fitness", 0))
                nf = float(ranked[0][1].get("fitness", 0))
                if nf < cf * 1.02:   # challenger must WIN by >2pct, not tie
                    ranked[0] = (champ, variants[champ])
            pmv.setdefault("family", {})["champion"] = ranked[0][0]
            json.dump(pmv, open(os.path.join(ROOT, "Config", "PathMemory.json"),
                                "w", encoding="utf-8"), indent=1)
        return ranked
    except Exception:
        return []

def _variant_env(shard_i):
    fam = _family()
    import random as _r
    env_m = {}
    if fam and _r.random() > 0.30:
        vid, v = fam[0]
        env_m["APEX_VARIANT"] = vid
        fam_params = v.get("params", {})
        basecfg = json.load(open(os.path.join(ROOT, "Config", "RewardConfig.json"),
                                 encoding="utf-8-sig"))
        for k0 in MUTABLE:
            # RATCHETED BASE: mutate from the champion's proven params, not the
            # static config - every generation starts from the family's peak
            base = fam_params.get(k0) or basecfg.get(k0, 100)
            env_m["MUT_" + k0] = str(max(10, int(base * (1.0 + _r.uniform(-0.08, 0.08)))))
        return env_m
    vid = "explore_" + str(os.getpid()) + "_" + str(shard_i)
    env_m["APEX_VARIANT"] = vid
    for k0 in MUTABLE:
        base = json.load(open(os.path.join(ROOT, "Config", "RewardConfig.json"),
                              encoding="utf-8-sig")).get(k0, 100)
        env_m["MUT_" + k0] = str(max(10, int(base * _r.uniform(0.6, 1.4))))
    return env_m
if __name__ == '__main__':
    import sys as _sys
    _sys.path.insert(0, r"C:\\Users\\seaha\\Downloads\\Apex-With-Triggers-Fixed\\Scripts")
    import Births
    import psutil
    free_gb = psutil.virtual_memory().available / 1024 ** 3
    # ELASTIC FLEET: workers scale to the machine's breathing - frontier autoscaler
    # pattern; territory 3 = the economy lane (USDC earn scans via the Ghost Net)
    max_shards = max(1, min(6, int(free_gb // 2)))   # lighter workers = more of them
    fleet_n = max_shards
    territories = ((0, "code"), (1, "science"), (2, "archive"), (3, "economy"))
    plan = territories[: max_shards] if free_gb >= 2.2 else []
    child_pids = []   # TRANSPORT: every child tracked until it comes home
    print(f"fleet plan: {len(plan)} workers (free {free_gb:.1f} GB)")
    for shard, note in plan:
        _e3 = None
        if shard == 3:
            env3 = dict(os.environ, APEX_SHARD="3")
            _e3 = subprocess.Popen(
                [PY, "-S", "-c", "import sys; sys.path.insert(0, r'" + ROOT + r"\Scripts');"
                 "import CryptoEconomy as ce; ce.bounty_scan(12); ce.rung1_issue_lane()"],
                env=env3, cwd=ROOT,
                stdout=open(AD + "\\shard3.log", "w", encoding="utf-8"),
                stderr=subprocess.STDOUT,
                creationflags=0x00000008 if os.name == "nt" else 0)
            child_pids.append((shard, _e3.pid if _e3 else 0))
            print("shard 3 (economy) deployed")
            continue
        env = dict(os.environ, APEX_SHARD=str(shard), APEX_FLEET=str(fleet_n), **_variant_env(shard))
        _c0 = subprocess.Popen(
            [PY, "-c", "import sys; sys.path.insert(0, r'" + ROOT + r"\Scripts');"
             "import SwarmOrchestrator as so; so.main(10, None, False);"
             "import sys as _ss; _ss.path.insert(0, r'" + ROOT + r"\Scripts');"
             "import CryptoEconomy as ce; ce.bounty_scan(6); ce.rung1_issue_lane()",
             "print('[DUAL-MISSION] gold round + economy scan complete')"],
            env=env, cwd=ROOT,
            stdout=open(AD + (r"\shard%d.log" % shard), "w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            creationflags=0x00000008 if os.name == "nt" else 0)
        child_pids.append((shard, _c0.pid))
        print(f"shard {shard} ({note}) deployed")

    # ---- THE GRAIN LINE: children always come home with everything ----
    try:
        import sys as _s
        _s.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
        import GrainLine as _gl
        import psutil as _pu
        # WAIT for each child's true exit (bounded 10 min): no mid-write reads
        import psutil as _pu
        for shard, pid in child_pids:
            try:
                _pu.Process(pid).wait(timeout=600)
            except Exception:
                pass
        for shard, pid in child_pids:
            r1 = None
            try:
                r1 = _gl.flush_child(shard)
                if r1 is None:
                    time.sleep(3)
                    r1 = _gl.flush_child(shard)
            except Exception as e:
                print(f"grain line shard {shard}: {str(e)[:70]}")
            print(f"grain line: shard {shard} -> {json.dumps(r1 or {})[:120]}")
            try:
                Births.death(shard, "child")   # the census: dissolved, not lost
            except Exception:
                pass
        try:
            print("CONVOY:", json.dumps(_gl.guard_convoy())[:260])
        except Exception:
            print("manifest:", json.dumps(_gl.deliver_all())[:220])
    except Exception as e:
        print("grain line error:", str(e)[:90])
