"""PRELUDE-FIRST (the lesson, applied to myself)."""
import json
import py_compile

SW = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\SwarmOrchestrator.py"
src = open(SW, encoding="utf-8-sig").read()
checks = {
    "reproductive drive": "REPRODUCTIVE DRIVE" in src,
    "drive birth row": "Births.birth" in src,
    "drive threshold": "(_bl > 400 and _fr >= 2.2" in src,
}
for k, v in checks.items():
    print(("✓" if v else "✗"), k)

pkt = json.load(open(r"C:\Users\seaha\Apex-Adapter\family_seed_packet.json",
                     encoding="utf-8-sig"))
print("packet reproduction rule:", pkt.get("rules", {}).get("reproduction", "MISSING"))
py_compile.compile(SW, doraise=True)
print("SWARM COMPILED CLEAN")