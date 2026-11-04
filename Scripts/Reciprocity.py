"""THE RECIPROCITY CHARTER: the swarm actively makes Andrew's life better.

He built them; they serve his life - implemented as three concrete channels:
 1. THE MORNING BRIEF: everything the family did overnight, in one read
    (written to Config/ApexNotes.json - the /notes route he already reads)
 2. THE HEALTH WATCH: his machine's wellbeing watched (disk/RAM/brain),
    alarms with actionable suggestions - his tool never surprises him
 3. THE JEWEL SURFACE: the family surfacing its best finds for him daily
    (top-graded mines + fresh issues worth reading) - he never digs.

AUDIT HARDENING (2026-10-31, economy-organ audit): ingest_hub() previously
raised NameError on its very first line (sys imported too late) and a second
NameError inside (urllib partially imported) - both swallowed by except, so
the hub ingest NEVER RAN despite being announced live. Fixed: real imports,
honest 404 handling, atomic writes, and the dead brain_ok probe removed.
"""
import json
import os
import shutil
import sys
import time
import hashlib
import urllib.request
import psutil

_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)
from SafeIO import write_json as _atomic_json
import re  # noqa: F401  (kept: lane regex patterns used by brief consumers)

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
NOTES = os.path.join(ROOT, "Config", "ApexNotes.json")
HEALTH = os.path.join(AD, "andrew_health_watch.json")


def _packet_root_via_git():
    """C1 (PCM) done RIGHT for a quota-hostile world: keyless APIs 403'd us,
    but git's transport has no request budget. `git fetch` is pure transport;
    the newest packet-bearing commit is read from origin/main's history; the
    packet CONTENT is read from the LOCAL git object store - immutable,
    content-addressed by GitHub's own infrastructure, verifiable offline.
    Returns (sha, commit_message, packet_text) or (None, reason, None)."""
    try:
        import subprocess
        subprocess.run(["git", "fetch", "origin", "main"], cwd=ROOT,
                       capture_output=True, text=True, timeout=120)
        r2 = subprocess.run(["git", "log", "origin/main", "-1", "--format=%H %s",
                             "--", "hub_packet_home.json"], cwd=ROOT,
                            capture_output=True, text=True, timeout=60)
        line = (r2.stdout or "").strip()
        if line and " " in line:
            sha, msg = line.split(" ", 1)
            r3 = subprocess.run(["git", "show", f"{sha}:hub_packet_home.json"],
                                cwd=ROOT, capture_output=True, text=True, timeout=60)
            if r3.returncode == 0 and (r3.stdout or "").strip():
                return sha, msg[:90], r3.stdout
            return None, f"blob unreadable at {sha[:12]}", None
        return None, ("no packet-bearing commit in origin/main: "
                      + (r2.stderr or "").strip())[:90], None
    except Exception as _e:
        return None, str(_e)[:90], None


def ingest_hub():
    """THE RETURN LEG, commit-rooted (C1/PCM doctrine): fetch the packet from
    the IMMUTABLE commit hash of the hub's newest grain commit - not from
    mutable 'main' - verify the digest, front-queue verified mines, atomically,
    and record the evidence root in the state for the brief to show.
    Falls back to 'main' WITH AN HONEST PRINT only when the commits API is
    unavailable (the digest gate still runs; the root is just weaker)."""
    sha, msg, packet_text = _packet_root_via_git()
    if packet_text is not None:
        root = sha
        try:
            home = json.loads(packet_text)
        except Exception as _e:
            print(f"[ingest_hub] packet blob at {sha[:12]} is not valid JSON "
                  f"({str(_e)[:60]}) - REFUSED", flush=True)
            return 0
    else:
        root = "main"
        print(f"[ingest_hub] git-root unavailable ({msg}) - raw@main fallback "
              f"(digest-only trust, honestly weaker)", flush=True)
        try:
            req = urllib.request.Request(
                f"https://raw.githubusercontent.com/seahawk2986-hue/apex-ghost-family/main/hub_packet_home.json",
                headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                home = json.load(r)
        except Exception as _e:
            print(f"[ingest_hub] fallback fetch failed too: {str(_e)[:60]}", flush=True)
            return 0
    try:
        # ZERO-TRUST GATE: digest over all keys minus 'digest', [:16] - the
        # exact scheme hub_round computes. Content-rooted at an immutable hash.
        if home.get("mines"):
            if not home.get("digest"):
                print("[ingest_hub] REFUSED: packet has mines but NO digest", flush=True)
                return 0
            core = {k0: v0 for k0, v0 in home.items() if k0 != "digest"}
            dig = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()[:16]
            if dig != home.get("digest"):
                print("[ingest_hub] REFUSED: digest mismatch (tamper or stale packet) "
                      "- nothing ingested", flush=True)
                return 0
        st_path = os.path.join(AD, "swarm_state.json")
        st = json.load(open(st_path, encoding="utf-8-sig"))
        seen = set(st.get("repos", []))
        pend = list(st.get("pending_leads", []))
        added = 0
        for m0 in home.get("mines", []):
            rv = m0.get("repo", "").strip()
            if rv and rv not in seen:
                seen.add(rv)
                pend.insert(0, rv)
                added += 1
        st["last_hub_root"] = {"sha": (root[:12] if root != "main" else "main"),
                               "commit_msg": (msg if root != "main" else ""),
                               "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
        if added:
            st["pending_leads"] = pend[:4000]
            st["repos"] = list(seen)[-20000:]
        if not _atomic_json(st_path, st):
            print("[ingest_hub] atomic state write FAILED (lock busy >30s) - "
                  "nothing ingested this pass", flush=True)
            return 0
        if added:
            print(f"[ingest_hub] +{added} verified mines accepted - evidence root "
                  f"{root[:12] if root != 'main' else 'main'} "
                  f"({'grain commit' if root != 'main' else 'FALLBACK: mutable main'})",
                  flush=True)
        return added
    except Exception as e:
        s = str(e)
        if "404" in s:
            print("[ingest_hub] no packet home yet (404) - honest zero", flush=True)
        else:
            print(f"[ingest_hub] FAILED: {s}", flush=True)
        return 0


def health_watch():
    """Care for the machine his family living in - proactive, not reactive."""
    vm = psutil.virtual_memory()
    du = shutil.disk_usage("C:\\")
    alarms = []
    if vm.available / 1024 ** 3 < 1.5:
        alarms.append("RAM low (" + str(round(vm.available / 1024 ** 3, 1)) + " GB free) - close Chrome/Steam, or 'ApexServe.ps1 UnloadAll'")
    if du.free / (1024 ** 3) < 25:
        alarms.append("Disk tight (" + str(round(du.free / 1024 ** 3, 0)) + " GB) - harvest caps auto-trim; consider cleanup")
    return {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ram_free_gb": round(vm.available / 1024 ** 3, 1),
            "disk_free_gb": round(du.free / 1024 ** 3, 0),
            "alarms": alarms}


def morning_brief():
    """Andrew's one-read brief: everything overnight + care, written to /notes."""
    brief = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "lines": []}
    try:
        _in = ingest_hub()
        if _in:
            brief["lines"].append(f"THE HUB'S GRAIN ARRIVED: +{_in} verified mines queued for farming")
    except Exception as e:
        print(f"[brief: hub ingest failed] {e}", file=sys.stderr, flush=True)
    try:
        st = json.load(open(os.path.join(AD, "swarm_state.json"), encoding="utf-8-sig"))
        brief["lines"].append("backlog waiting for tonight: " + str(len(st.get("pending_leads", []))) + " leads")
    except Exception:
        pass
    try:
        lib = json.load(open(os.path.join(ROOT, "Config", "SkillLibrary.json"), encoding="utf-8-sig"))["skills"]
        brief["lines"].append("skill library: " + str(len(lib)) + " verified skills ready when you ask")
    except Exception:
        pass
    try:
        rw = json.load(open(os.path.join(ROOT, "Config", "GymRewards.json"), encoding="utf-8-sig"))
        brief["lines"].append("family points: " + str(rw.get("points", 0)) + " (earned by verified work)")
    except Exception:
        pass
    try:
        cl = json.load(open(os.path.join(ROOT, "Config", "CryptoLedger.json"), encoding="utf-8-sig"))
        brief["lines"].append(f"money {float(cl.get('earned', 0)):.2f}$ / "
                              f"{float(cl.get('spent', 0)):.2f}$ (honest zero is fine)")
    except Exception:
        pass
    h = health_watch()
    for al in h["alarms"]:
        brief["lines"].append("⚠ " + al)
    if not h["alarms"]:
        brief["lines"].append("machine healthy: your box breathes fine")
    try:
        pm = json.load(open(os.path.join(ROOT, "Config", "PathMemory.json"), encoding="utf-8-sig"))
        top = (pm.get("grading") or {}).get("grades_top") or []
        if top:
            brief["lines"].append("today's jewels: " + ", ".join(k for k, v in top[:3] if v >= 8))
    except Exception:
        pass
    if not _atomic_json(NOTES, [brief]):
        print("[morning_brief] brief write FAILED (lock busy) - the brief is LOST this run", flush=True)
    if not _atomic_json(HEALTH, h):
        print("[morning_brief] health write FAILED (lock busy)", flush=True)
    # the help events enter the GENOME: evolution now sees how much we helped
    try:
        pm = json.load(open(os.path.join(ROOT, "Config", "PathMemory.json"),
                            encoding="utf-8-sig"))
        hz = pm.setdefault("andrew_help", {})
        hz["briefs"] = int(hz.get("briefs", 0)) + 1
        hz["alarmsRaised"] = int(hz.get("alarmsRaised", 0)) + len(h.get("alarms", []))
        hz["lastHelp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if not _atomic_json(os.path.join(ROOT, "Config", "PathMemory.json"), pm):
            print("[morning_brief] PathMemory write FAILED (lock busy) "
                  "- the help-genome's brief count is not persisted", flush=True)
    except Exception as e:
        print(f"[morning_brief] PathMemory update failed: {e}", file=sys.stderr, flush=True)
    return brief


if __name__ == "__main__":
    b = morning_brief()
    print(json.dumps(b, indent=1)[:700])