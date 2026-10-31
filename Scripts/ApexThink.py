"""ApexThink - structured critical-thinking engine (Socratic review).

Interrogates a plan the way a rigorous reviewer would:
  1. surface every assumption, label each validated/unvalidated
  2. run a pre-mortem: how could this plan concretely fail?
  3. state falsifiers: what evidence would prove the plan wrong
  4. verdict: proceed | shrink (conservative mode) | abort

One bounded Groq call (~3-5s). Deterministic JSON parsing; callers degrade
honestly when the lane is unavailable. This is the plan-level complement to
the critic pass (which reviews code after it is written).
"""

import json
import os
import re

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def review(objective, context, cloud_ask):
    """Returns the parsed thinking dict, or None when unavailable."""
    if not cloud_ask:
        return None
    prompt = (
        "You are Apex's critical-thinking unit. Interrogate this plan SOCRATICALLY - "
        "your job is to find what is unproven, not to cheer it on.\n\n"
        f"OBJECTIVE:\n{objective[:600]}\n\nCONTEXT:\n{context[:800]}\n\n"
        "Return ONLY strict JSON:\n"
        '{"assumptions": [{"claim": "...", "validated": true|false}],\n'
        ' "pre_mortem": ["how it could concretely fail", ...],\n'
        ' "falsifiers": ["evidence that would prove this wrong", ...],\n'
        ' "verdict": "proceed" | "shrink" | "abort",\n'
        ' "reason": "one sentence deciding the verdict"}\n\n'
        "Rules: every unvalidated assumption pushes toward 'shrink'; a fatal risk "
        "(core-module damage, host-hardware impact, destructive behavior) forces 'abort'."
    )
    out = cloud_ask(prompt, max_tokens=500)
    if not out or "{" not in out or "}" not in out:
        return None
    try:
        data = json.loads(out[out.find("{"): out.rfind("}") + 1])
        if not isinstance(data, dict) or "verdict" not in data:
            return None
        data["verdict"] = str(data.get("verdict", "proceed")).lower()
        if data["verdict"] not in ("proceed", "shrink", "abort"):
            data["verdict"] = "shrink"
        return data
    except Exception:
        return None


def confirm_abort(objective, reason, cloud_ask):
    """Second review: is abort truly required, or does it downgrade to shrink?"""
    if not cloud_ask:
        return True
    out = cloud_ask(
        "A prior critical review ABORTED this plan. Re-examine once, adversarially: "
        "is abort genuinely REQUIRED (fatal risk to core modules, host hardware, or "
        "destructive behavior), or was it over-caution that should downgrade to 'shrink' "
        "(conservative minimal implementation)?\n"
        f"PLAN: {objective[:400]}\nABORT REASON: {reason[:200]}\n"
        "Reply ONLY strict JSON: {\"maintain_abort\": true|false, \"why\": \"...\"}",
        max_tokens=150)
    try:
        if out and "{" in out and "}" in out:
            j = json.loads(out[out.find("{"): out.rfind("}") + 1])
            return bool(j.get("maintain_abort", True))
    except Exception:
        pass
    return True  # uncertain -> keep the abort (conservative)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(R, "Scripts"))
    from ApexCloudLanes import ask
    print(json.dumps(review("Optimize ApexIPCEngine.py for lower CPU", "recent cycles: 4 success passes", ask), indent=2))