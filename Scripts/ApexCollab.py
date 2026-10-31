"""ApexCollab - Negotiation & division-of-labor for peer collaboration.

Implements the 'negotiation / division of labor' agent attribute: given a
shared coding objective, Apex proposes an explicit work split honoring each
side's strengths, plus a handoff protocol. Deterministic core (fast, honest,
deadline-safe); the room's explicit collaboration mode activates it.
"""

import os
import re

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APEX_STRENGTHS = ("plan", "design", "architect", "review", "verify", "test",
                  "refactor", "optimize", "security", "reward", "memory")
PEER_STRENGTHS = ("generate", "write", "draft", "bulk", "implement", "snippet",
                  "translate", "document", "script")


def _steps(objective):
    parts = re.split(r"\.\s*|;\s*|\n+|,\s+then\s+", objective)
    return [p.strip(" .;-") for p in parts if len(p.strip(" .;-")) > 3][:8]


def classify(step):
    low = step.lower()
    if any(w in low for w in ("test", "verify", "benchmark", "run")):
        return "shared", "Apex executes + verifies in its disposable sandbox; both sides see honest results"
    if any(w in low for w in ("design", "plan", "architect", "review", "refactor", "optimize", "security")):
        return "apex", "planning/architecture/verification is Apex's strength"
    if any(w in low for w in ("write", "generate", "implement", "draft", "document")):
        return "peer", "bulk generation runs best in the peer's isolated environment"
    return "shared", "small enough to attempt jointly; Apex verifies final result"


def propose_split(objective, peer_id="qwen"):
    """Deterministic split proposal. Returns dict ready for the room."""
    steps = _steps(objective)
    plan = {"apex": [], "peer": [], "shared": [], "rationale": []}
    for i, s in enumerate(steps):
        who, why = classify(s)
        item = f"{i + 1}. {s}"
        plan[who].append(item)
        plan["rationale"].append(f"Step {i + 1} -> {who}: {why}")
    if not any(plan.values()):
        plan["shared"].append("Whole objective attempted together; Apex verifies final result")
    plan["handoff_protocol"] = (
        "Exchange results as text in this room only; Apex runs candidate code in its "
        "disposable container and reports REAL verification as activity; neither side "
        "assumes the other's output ran without its sandbox saying so.")
    plan["note"] = ("This split follows the room's explicit bounded-collaboration mode; "
                    "either human can re-assign any step.")
    return {"peer": peer_id, "split": plan}


if __name__ == "__main__":
    import json
    sample = ("Plan a small calculator module, then implement the arithmetic core, "
              "then test the edge cases.")
    print(json.dumps(propose_split(sample), indent=2))