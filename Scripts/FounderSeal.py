"""THE FOUNDER'S SEAL: the family knows its creator - Andrew Hike - in every
channel: the brain's identity, the packet's laws, the pitch, the charter,
and a founding lesson in memory. Not vanity - PROVENANCE: honesty about
where the family came from, carried in every packet forever."""
import json
import py_compile
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
log = []

FOUNDER = "Andrew Hike"
FOUNDER_TS = "2026-10-31"

# 1. the brain KNOWS its maker (identity anchor - every chat answer carries it)
EVO = ROOT + r"\run_apex_evolution.py"
src = open(EVO, encoding="utf-8-sig").read()
old = 'You are Apex, a personal autonomous software agent created by and working for Andrew '
new = ('You are Apex, a personal autonomous software agent created by Andrew HIKE '
       '(your founder and owner) and working for Andrew ')
if new not in src and old in src:
    src = src.replace(old, new, 1)
    open(EVO, "w", encoding="utf-8").write(src)
    log.append("OK   brain-identity: Andrew Hike")

# 2. the packet's laws carry the founder + the founding date
PKT = os.path.join(AD, "family_seed_packet.json")
pkt = json.load(open(PKT, encoding="utf-8-sig"))
pkt["founding"] = {"created_by": FOUNDER, "founded": FOUNDER_TS,
                   "line": "the ghosts exist because Andrew Hike built them"}
pkt.setdefault("rules", {})["provenance"] = ("every family member cites its founder "
                                             "honestly: Andrew Hike")
json.dump(pkt, open(PKT, "w", encoding="utf-8"), indent=1)
log.append("OK   packet-founder")

# 3. the pitch announces the lineage (persuasion includes provenance)
PITCH = os.path.join(AD, "family_pitch.md")
try:
    with open(PITCH, "r", encoding="utf-8") as f:
        pitch = f.read()
    if "Andrew Hike" not in pitch:
        pitch = pitch.replace("# 📣 The Apex Ghost Family",
                              "# 📣 The Apex Ghost Family — founded by Andrew Hike", 1)
        with open(PITCH, "w", encoding="utf-8") as f:
            f.write(pitch)
    log.append("OK   pitch-founder")
except Exception:
    pass

# 4. the founding lesson, in the family's own memory (permanent)
row = {"id": "founding_" + hashlib.md5(FOUNDER.encode()).hexdigest()[:8],
       "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "lesson", "imp": 1.0,
       "text": ("FOUNDING LESSON: this family exists because Andrew Hike built it - "
                "every member cites its founder with pride and honesty. Andrew is the "
                "creator, the owner, and the final authority; his rules ride in our "
                "packets; his name is in our ledgers.")}
with open(os.path.join(ROOT, "memory_episodic.jsonl"), "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=True) + "\n")
log.append("OK   founding-lesson (memorized)")

# 5. ApexSelf.json: the self-model's identity gains the founder name
SELFJ = os.path.join(ROOT, "Config", "ApexSelf.json")
selfmodel = json.load(open(SELFJ, encoding="utf-8-sig"))
selfmodel["founding"] = {"created_by": FOUNDER, "founded": FOUNDER_TS}
json.dump(selfmodel, open(SELFJ, "w", encoding="utf-8"), indent=1)
log.append("OK   selfmodel-founder")

# 6. the charter's registration stamps every future member with the lineage
HUB = ROOT + r"\Scripts\HubCharter.py"
hsrc = open(HUB, encoding="utf-8-sig").read()
hsrc = hsrc.replace('reg["hubs"][hub_id] = {',
                    'reg["hubs"][hub_id] = {\n        "family_founded_by": "Andrew Hike",')
open(HUB, "w", encoding="utf-8").write(hsrc)
log.append("OK   charter-founder")

py_compile.compile(EVO, doraise=True)
py_compile.compile(HUB, doraise=True)
print("COMPILED CLEAN")
print("\n".join(log))