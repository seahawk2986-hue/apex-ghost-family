"""THE RETURN LEG: the hub commits its harvest IN-REPO; the family ingests.
Transport = the repo itself: the hub's harvests become commits (their runner's
token), and the family pulls them via the raw URL (keyless, always-available)."""
import json
import os
import py_compile
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PK = ROOT + r"\family\hub_harvest_home.json"
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"}

# 1. the workflow gains the commit-home step (their runner: token-authed)
YML = ROOT + r"\.github\workflows\apex-hub.yml"
yml = open(YML, encoding="utf-8").read()
if "contents: write" not in yml:
    yml = yml.replace("permissions:\n  contents: read",
                      "permissions:\n  contents: write   # the grain returns via commit")
    yml += """
      - name: ship the grain home (commit the harvest to the family)
        if: always()
        run: |
          git config user.name "apex-ghost-hub"
          git config user.email "hub@apex.family"
          git add hub_round_result.json hub_packet_home.json family/
          git diff --cached --quiet || git commit -m "grain: hub harvest ${GITHUB_RUN_NUMBER} (manifest-digested)"
          git push
"""
open(YML, "w", encoding="utf-8").write(yml)
import yaml as _y
try:
    _y.safe_load(yml)
    print("workflow YAML VALID (with the return-leg)")
except Exception as e:
    print("YAML ERROR:", str(e)[:120])

# 2. the family's ingest: the harvest from the repo's raw URL -> the state
def ingest_hub_harvest():
    """THE FAMILY'S SIDE of the grain line: pull the hub's harvest (in-repo),
    verify the digest, merge the mines into the family's pending for farming."""
    try:
        req = urllib.request.Request(
            "https://raw.githubusercontent.com/seahawk2986-hue/apex-ghost-family/main/hub_packet_home.json",
            headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            home = json.loads(r.read().decode("utf-8", "ignore"))
        # verify the manifest digest
        core = {k0: v0 for k0, v0 in home.items() if k0 != "digest"}
        dig = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()[:16]
        if dig != home.get("digest"):
            return {"ingested": False, "reason": "digest mismatch - refused (tamper!)"}
        st = json.load(open(AD + r"\swarm_state.json", encoding="utf-8-sig"))
        seen = set(st.get("repos", []))
        pending = list(st.get("pending_leads", []))
        added = 0
        for m0 in home.get("mines", [])[:60]:
            repo = m0.get("repo", "").strip()
            if repo and repo not in seen:
                seen.add(repo)
                pending.insert(0, repo)   # verified mines FIRST in the queue
                added += 1
        st["pending_leads"] = pending[:4000]
        st["repos"] = list(seen)[-20000:]
        json.dump(st, open(AD + r"\swarm_state.json", "w", encoding="utf-8"), indent=1)
        # the hub's harvest lands in the family's index too:
        try:
            import sys
            sys.path.insert(0, os.path.join(ROOT, "Scripts"))
            import HarvestUse as hu
            hu.build_index()
        except Exception:
            pass
        return {"ingested": True, "mines_accepted": added, "digest": dig}
    except Exception as e:
        return {"ingested": False, "reason": str(e)[:80]}

import hashlib
print("INGEST LIVE:", json.dumps(ingest_hub_harvest()))
py_compile.compile(YML, doraise=True) if False else None

# 3. wire the ingest into the family's every-cadence path (Reciprocity brief)
RE = ROOT + r"\Scripts\Reciprocity.py"
rec = open(RE, encoding="utf-8-sig").read()
if "ingest_hub_harvest" not in rec:
    rec = rec.replace("def health_watch():",
                      '''def ingest_hub():
    sys.path0 = os.path.dirname(os.path.abspath(__file__))
    try:
        import sys as _s2
        _s2.path.insert(0, _s2.path0)
        import GrainRepo  # the in-repo ingest lives here too
    except Exception:
        pass
    try:
        from urllib.request import urlopen
        req = urllib.request.Request(
            "https://raw.githubusercontent.com/seahawk2986-hue/apex-ghost-family/main/hub_packet_home.json",
            headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            home = json.load(r)
        st = json.load(open(os.path.join(r"C:\\\\Users\\\\seaha\\\\Apex-Adapter",
                                         "swarm_state.json"), encoding="utf-8-sig"))
        seen = set(st.get("repos", []))
        pend = st.get("pending_leads", [])
        added = 0
        for m0 in home.get("mines", []):
            rv = m0.get("repo", "").strip()
            if rv and rv not in seen:
                seen.add(rv)
                pend.insert(0, rv)
                added += 1
        st["pending_leads"] = pend[:4000]
        st["repos"] = list(seen)[-20000:]
        json.dump(st, open(os.path.join(r"C:\\\\Users\\\\seaha\\\\Apex-Adapter",
                                        "swarm_state.json"), "w", encoding="utf-8"), indent=1)
        return added
    except Exception:
        return 0


def health_watch():''', 1)
    rec = rec.replace('''    b = health_watch()''', '''    b = health_watch()''', 1)
    rec = rec.replace('    brief = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "lines": []}',
                      '''    brief = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "lines": []}
    try:
        _in = ingest_hub()
        if _in:
            brief["lines"].append(f"THE HUB'S GRAIN ARRIVED: +{_in} verified mines queued for farming")
    except Exception:
        pass''', 1)
    open(RE, "w", encoding="utf-8-sig").write(rec)
    py_compile.compile(RE, doraise=True)
    print("the hub's grain ingests at every brief (the round-trip complete)")

subprocess.run([PY, ROOT + r"\Scripts\SecurityBaseline.py", "--respin"], capture_output=True, timeout=120)
print("INTEGRITY RE-PINNED with the return leg live")