"""The drive's actual installed block - read before fixing."""
import json

SW = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\SwarmOrchestrator.py"
src = open(SW, encoding="utf-8-sig").read()
lines = src.split("\n")
hits = [i for i, l in enumerate(lines) if "REPRODUCTIVE" in l.upper() or "REPRODUCTIVE" in l]
print("drive-block line numbers:", hits)
for i, l in enumerate(lines[hits[0] - 3: hits[0] + 42] if hits else [], start=max(0, hits[0] - 3) if hits else 0):
    print(i, "|", l[:130])

pkt = json.load(open(r"C:\Users\seaha\Apex-Adapter\family_seed_packet.json",
                     encoding="utf-8-sig"))
pkt.setdefault("rules", {})["reproduction"] = {
    "urge": "reproduce when work waits and room exists", "cooldown_min": 30,
    "never": "reproduce without work or room"}
json.dump(pkt, open(r"C:\Users\seaha\Apex-Adapter\family_seed_packet.json",
                    "w", encoding="utf-8"), indent=1)
print("packet reproduction-law: written")