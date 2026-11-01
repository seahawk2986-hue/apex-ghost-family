"""SCAN THE FRESH 100: which mechanisms does the field have that our organs
lack? Every paper's abstract tagged against a mechanism dictionary; the
ALREADY-IMPLEMENTED ones marked; the NEW levers ranked for the upgrade."""
import json

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
rows = [json.loads(l) for l in open(ROOT + r"\Config\papers_2026.jsonl", encoding="utf-8-sig")]
MECH = {
    "epistemic/theory-of-mind": ["epistemic", "theory of mind", "belief state", "what others know"],
    "calibrated-confidence": ["calibrat"],
    "self-play/competitions": ["self-play", "tournament", "competition"],
    "consensus-breakdown/herding": ["breakdown", "consensus", "herding", "mislead"],
    "credit-assignment": ["credit assignment", "credit"],
    "world-models": ["world model"],
    "novelty-search/open-ended": ["novelty", "open-ended"],
    "opponent-modeling/deception": ["decept", "opponent", "collusion"],
    "curiosity": ["curiosity"],
    "regret": ["regret", "minimax"],
    "memory-consolidation": ["consolidat"],
    "speculative": ["speculative"],
    "inference-scaling": ["test-time", "inference-time scal", "test-time scal"],
    "population/genetic": ["population", "genetic", "evolutionary"],
    "human-in-the-loop": ["human", "oversight"],
    "multi-objective": ["multi-object", "pareto", "compromise"],
}
found = {}
for r0 in rows:
    txt = (r0["title"] + " " + r0["abstract"]).lower()
    for mech, kws in MECH.items():
        if any(k in txt for k in kws):
            found.setdefault(mech, []).append(r0["id"] + "  " + r0["title"][:64])

HAVE = {"speculative", "human-in-the-loop", "multi-objective", "self-play/competitions"}
print("=== MECHANISM SCAN OF THE FRESH 100 ===")
for mech, hits in sorted(found.items(), key=lambda kv: -len(kv[1])):
    tag = " [HAVE/STAGED]" if mech in HAVE else " [NEW LEVER]"
    print(f"  {len(hits):3d}  {mech}{tag}")
    for h0 in hits[:2]:
        print("        -", h0[:100])
print()
top = sorted(found.keys(), key=lambda m: -len(found[m]))
print("top NEW levers by paper-count:", [m for m in top if m not in HAVE][:5])