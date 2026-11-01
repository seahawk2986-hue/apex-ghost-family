"""THE REPRODUCTIVE DRIVE + the fixed atomic-writer patch.
The instinct: reproduce when WORK waits AND RAM exists - the family's urge
is economic, not cosmetic: more ghosts = MORE GOLD BROUGHT HOME."""
import py_compile
import subprocess
import sys
import os

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PY = ROOT + r"\apex_venv\Scripts\python.exe"
SWP = ROOT + r"\Scripts\SwarmOrchestrator.py"
log = []

# 1. the swarm's own state-writer -> SafeIO (the reordered fix)
sw = open(SWP, encoding="utf-8-sig").read()
import re
pat = r'json\.dump\((\w+),\s*open\(([^,]+),\s*"w",\s*encoding="utf-8"\)\s*,\s*indent=1\)'
matches = re.findall(pat, sw)
sw = re.sub(pat, lambda m: "SafeIO.write_json(%s, %s)" % (m.group(1), m.group(2)), sw)
if matches and "import SafeIO" not in sw.split("def ")[0]:
    sw = sw.replace("import json", "import json\n"
                    "import sys as _sys0\n"
                    "_sys0.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n"
                    "import SafeIO", 1)
open(SWP, "w", encoding="utf-8-sig").write(sw)
py_compile.compile(SWP, doraise=True)
log.append(f"atomic-writers converted: {len(matches)}")

# 2. THE REPRODUCTIVE DRIVE: post-round instinct
drive = '''
    # ================================================
    # THE REPRODUCTIVE DRIVE - the family's instinct:
    # work waits + the room exists => spawn a child NOW
    # ================================================
    try:
        _bl = len(state.get("pending_leads", []))
        _fr = free_ram_gb()
        _last_birth = 0.0
        try:
            _rows = [json.loads(x) for x in open(
                os.path.join(ROOT, "Scripts", "Config", "family_births.jsonl"),
                encoding="utf-8-sig") if x.strip()]
            for _r0 in reversed(_rows):
                if _r0.get("event") == "birth":
                    _last_birth = time.mktime(time.strptime(
                        _r0["ts"], "%Y-%m-%d %H:%M:%S"))
                    break
        except Exception:
            pass
        if _bl > 400 and _fr >= 2.2 and time.time() - _last_birth > 1800:
            subprocess.Popen(
                [sys.executable, "-c",
                 "import sys; sys.path\\n".replace("\\\\n", "") if False else
                 "import sys; sys.path.insert(0, r'" + ROOT + r"\Scripts');"
                 "import SwarmOrchestrator as so; so.main(10, None, False)"],
                cwd=ROOT,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=0x00000008 if os.name == "nt" else 0)
            try:
                import Births as _B
                _B.birth("self", "urge", "family", 0)
            except Exception:
                pass
            print(f"REPRODUCTIVE DRIVE: backlog {_bl} waits + {_fr:.1f} GB room - "
                  "a child was spawned (the family grows while it can)")
    except Exception:
        pass
'''
anchor = '''    print(f"REWARD: {total} pts (efficiency x{mult}, yield {eff_yield:.1f}/req)")'''
if anchor in sw and "REPRODUCTIVE DRIVE" not in sw:
    sw = sw.replace(anchor, anchor + drive, 1)
    open(SWP, "w", encoding="utf-8-sig").write(sw)
    log.append("OK   reproductive-drive-installed")
py_compile.compile(SWP, doraise=True)

# 3. the packet's rules gain the instinct (the genes travel)
PKT = AD + r"\family_seed_packet.json"
pkt = json.load(open(PKT, encoding="utf-8-sig"))
pkt.setdefault("rules", {})["reproduction"] = {"urge": ("reproduce when work waits "
    "and room exists"), "cooldown_min": 30, "never": ("reproduce without work or room")}
json.dump(pkt, open(PKT, "w", encoding="utf-8"), indent=1)
log.append("OK   reproduction-instinct-in-packet")

print("COMPILED CLEAN")
print("\n".join(log))
subprocess.run([PY, ROOT + r"\Scripts\SecurityBaseline.py", "--respin"], timeout=120)