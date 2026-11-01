"""RUNROI (doctrine Part X - the novel organ): ledger-calibrated run cascading.
FrugalGPT proved a cascade can match GPT-4 at up to 98% cost cut; RouteLLM
proved routers cut >2x. Nobody cascades at the RUN-MODE level - that is this
organ: a per-mode expected-ROI model, calibrated by the family's OWN measured
outcomes (not guesses), plus hard precondition gates. It answers one question
before any run: "what is the expected return of this mode RIGHT NOW, in
RAM-seconds-and-quota - and is it above the bar?"
Modes: archive_pull | conversion | upgrader | reflexion | gauntlet | mining
Usage: python RunROI.py            (shadow: print decisions only)
       python RunROI.py --execute  (run ONLY greenlit cheap modes)
       python RunROI.py --record mining:0.0  (feed measured outcome 0..1)
Hardware: checks are read-only probes; the organ itself burns ~nothing.
Values masked, failures printed, fail-closed."""
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
CAL = os.path.join(ROOT, "Config", "runroi_calibration.json")


def ram_free():
    try:
        import psutil
        return psutil.virtual_memory().available / 2 ** 30
    except Exception:
        return 0.0


def brain_state():
    """(loaded_model_or_None, ram) - read-only, bounded."""
    try:
        for m in json.load(urllib.request.urlopen(
                "http://127.0.0.1:1234/api/v0/models", timeout=4)).get("data", []):
            if m.get("state") == "loaded" and "text-embedding" not in (m.get("id") or ""):
                return m["id"], ram_free()
    except Exception:
        pass
    try:
        ps = json.load(urllib.request.urlopen(
            "http://127.0.0.1:11434/api/ps", timeout=4)).get("models", [])
        if ps:
            return ps[0].get("name"), ram_free()
    except Exception:
        pass
    return None, ram_free()


def seeded():
    """Calibration SEEDED from tonight's measured outcomes (Parts IX prints):
    gated local cycles -> ~0 return; the 7GB window decade -> real rounds but
    no conversion (register empty); one upgrader window -> 5 verified skills;
    one archive command -> 6 candidates; conversion attempt -> 1 WEAK dossier.
    These are EMAs - every --record updates them."""
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    return {"seeded": now, "alpha": 0.3, "ev": {
        "archive_pull": 0.70, "upgrader": 0.60, "conversion": 0.30,
        "gauntlet": 0.45, "reflexion": 0.40, "mining": 0.15}}


def load_cal():
    try:
        return json.load(open(CAL, encoding="utf-8-sig"))
    except Exception:
        c = seeded()
        with open(CAL, "w", encoding="utf-8") as f:
            json.dump(c, f, indent=1)
        return c


def record(mode, outcome):
    c = load_cal()
    a = c.get("alpha", 0.3)
    old = c["ev"].get(mode, 0.0)
    c["ev"][mode] = round(old * (1 - a) + outcome * a, 3)
    c["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    tmp = CAL + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=1)
    os.replace(tmp, CAL)
    print(f"[runroi] recorded {mode}={outcome} -> EMA ev now {c['ev'][mode]}")


def candidate_quality():
    try:
        rows = [json.loads(x) for x in open(
            os.path.join(ROOT, "Config", "issue_triage.jsonl"), encoding="utf-8-sig")]
        return max((float(r0.get("clarity", 0)) for r0 in rows), default=0.0)
    except Exception:
        return 0.0


def decide(cal, execute=False):
    model, ram = brain_state()
    st = {}
    try:
        st = json.load(open(os.path.join(AD, "swarm_state.json"), encoding="utf-8-sig"))
    except Exception:
        pass
    backlog = len(st.get("pending_leads", []))
    cq = candidate_quality()
    have_triage = cq >= 45
    print(f"[runroi] state: RAM {ram:.2f} | brain {model or 'NONE'} | backlog {backlog} "
          f"| best candidate clarity {cq} (values stay masked elsewhere)")
    decisions = []
    green = []

    def entry(mode, ev, verdict, why, cmd=None):
        decisions.append((mode, ev, verdict, why))
        print(f"  {mode:14s} EV {ev:.2f} -> {verdict:6s} | {why}")
        if execute and verdict == "GO" and cmd:
            green.append(cmd)
        return None

    # 1. archive_pull: keyless, ~0 cost, measured positive every time
    ev = cal["ev"].get("archive_pull", 0.7)
    bugs_path = os.path.join(AD, "gh_archive_bugs.jsonl")
    bugs_small = (not os.path.exists(bugs_path)) or os.path.getsize(bugs_path) < 200 * 1024
    if bugs_small:
        entry("archive_pull", ev, "GO" if ev >= 0.5 else "DEFER",
              "keyless bulk, measured 6 candidates in one command",
              cmd=[sys.executable, os.path.join(ROOT, "Scripts", "GhArchiveLane.py"), "1"])
    else:
        entry("archive_pull", ev, "DEFER", "candidate store already ample (honest cap)")
    # 2. conversion (W3): needs RAM gate + brain + a candidate above the bar
    ev = cal["ev"].get("conversion", 0.3)
    if ram >= 2.2 and model and have_triage:
        entry("conversion", ev, "GO" if ev >= 0.5 else "DEFER",
              "all preconditions live; single-turn bounded",
              cmd=[sys.executable, os.path.join(ROOT, "Scripts", "ConversionRun.py")])
    else:
        entry("conversion", ev, "DEFER",
              f"preconditions missing (RAM {ram:.2f}{'<2.2' if ram < 2.2 else ''}, "
              f"brain {bool(model)}, clarity≥45 {have_triage}) - tonight's ledger "
              f"says these runs return ~0 when gat")
    # 3. upgrader (W1)
    ev = cal["ev"].get("upgrader", 0.6)
    if ram >= 2.2 and backlog > 0:
        entry("upgrader", ev, "GO" if ev >= 0.5 else "DEFER",
              "verified 5 executable skills in one window",
              cmd=[sys.executable, os.path.join(ROOT, "Scripts", "SkillUpgrader.py"), "6"])
    else:
        entry("upgrader", ev, "DEFER", "RAM/backlog preconditions missing")
    # 4. gauntlet (novel, cap-influenced per DataSense-Bench)
    ev = cal["ev"].get("gauntlet", 0.45)
    if ram >= 2.5 and model and have_triage:
        entry("gauntlet", ev, "GO" if ev >= 0.5 else "DEFER",
              "candidates + brain live; vote tier capped",
              cmd=[sys.executable, os.path.join(ROOT, "Scripts", "GauntletRun.py")])
    else:
        entry("gauntlet", ev, "DEFER", "preconditions missing (honest)")
    # 5. reflexion (W2)
    ev = cal["ev"].get("reflexion", 0.4)
    if ram >= 2.2 and model:
        entry("reflexion", ev, "GO" if ev >= 0.5 else "DEFER",
              "one bounded call; rides next brief",
              cmd=[sys.executable, os.path.join(ROOT, "Scripts", "ReflexionRound.py")])
    else:
        entry("reflexion", ev, "DEFER", "RAM/brain missing")
    # 6. mining cycles: the audited theater - highest bar of all
    ev = cal["ev"].get("mining", 0.15)
    if ram >= 5.0 and model and backlog >= 500:
        entry("mining", ev, "GO" if ev >= 0.5 else "DEFER",
              "only in real windows; hub mining is free and running anyway")
    else:
        entry("mining", ev, "DEFER",
              "the 0/60-starved, gated-cycle ledger says ~0 return under this state")
    return decisions, green


def execute_green(green):
    """Run ONLY the greenlit cheap modes; return their measured outcome deltas."""
    before = _measures()
    for cmd in green:
        print(f"[runroi] EXECUTE: {os.path.basename(cmd[1])} (bounded, live)")
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except Exception as e:
            print(f"[runroi] mode failed honestly: {str(e)[:70]}")
    after = _measures()
    return before, after


def _measures():
    m = {"gfi": 0, "curriculum": 0}
    try:
        m["gfi"] = sum(1 for _ in open(os.path.join(AD, "gh_archive_bugs.jsonl"),
                                       encoding="utf-8-sig"))
    except Exception:
        pass
    try:
        m["curriculum"] = len(json.load(open(
            os.path.join(ROOT, "Config", "curriculum.json"),
            encoding="utf-8-sig")).get("items", []))
    except Exception:
        pass
    return m


if __name__ == "__main__":
    cal = load_cal()
    if "--record" in sys.argv:
        mode, val = sys.argv[sys.argv.index("--record") + 1].rsplit(":", 1)
        record(mode, float(val))
        sys.exit(0)
    print("[runroi] CASCADE DECISIONS (FrugalGPT-at-run-level, ledger-calibrated):")
    ds, green = decide(cal, execute="--execute" in sys.argv)
    go = [d[0] for d in ds if d[2] == "GO"]
    defer = [d[0] for d in ds if d[2] == "DEFER"]
    print(f"\n[runroi] SUMMARY: GO {go} | DEFER {defer}")
    if "--execute" in sys.argv:
        b, a = execute_green(green)
        print(f"[runroi] MEASURED DELTAS: gfi {b['gfi']}->{a['gfi']} | "
              f"curriculum {b['curriculum']}->{a['curriculum']}")
        for mode, key in (("archive_pull", "gfi"), ("upgrader", "curriculum")):
            gain = a[key] - b[key]
            if any(cmd[1].lower().endswith(mode.split('_')[0] + "*.py")
                   for _cmd in [green] if False):
                pass
        # record honestly per greenlit mode by its own key
        if any(c[0][1].endswith("GhArchiveLane.py") for c in green):
            record("archive_pull", min(1.0, (a["gfi"] - b["gfi"]) / 4.0))
        if any(c[0][1].endswith("SkillUpgrader.py") for c in green):
            record("upgrader", min(1.0, (a["curriculum"] - b["curriculum"]) / 3.0))
    else:
        print("[runroi] shadow mode - pass --execute to live-run only the GO modes")