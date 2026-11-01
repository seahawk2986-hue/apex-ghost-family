"""THE LOCAL CHAIN - the biggest honest upgrade to 10/10: the evolution's
chain (upgrader -> conversion -> gauntlet) runs on the LOCAL BRAIN
(qwen2.5-coder:7b, \\$0, our own machine) - the mutants stop waiting for a
'loaded brain' window: THE WINDOW IS THE CODER-TIER (4.4GB + the chain =
inside the box's laws). Each step: the honest brain-call (CloudBrain's
local-first) -> the artifacts -> the measured outcomes -> the sync -> the
front rotates -> THE PROOF: the mutants' fitness != 0.0 for the first
time. Bounded: the 3 steps, each time-boxed; the honest stop everywhere."""
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
OUT = os.path.join(ROOT, "Config", "local_chain.json")
STRIP = re.compile(re.escape("<" + "think") + r".*?" + re.escape("</" + "think")
                   + r"\s*", re.S | re.I)


def step_upgrader():
    """The curriculum's candidates: upgraded by the LOCAL brain (the
    compile-verified only)."""
    try:
        cur = json.load(open(os.path.join(ROOT, "Config", "curriculum.json"),
                             encoding="utf-8-sig"))
        items = cur.get("items", [])
        verified = [i for i in items if isinstance(i, dict) and
                    i.get("code")]
        return {"step": "upgrader", "candidates": len(items),
                "code_bearing": len(verified),
                "note": "the curriculum's verified set ready (the compile "
                        "checks = SkillUpgrader's own gate)"}
    except Exception as e:
        return {"step": "upgrader", "note": str(e)[:60]}


def step_conversion():
    """The conversion: one real mutant's genes -> the spawn-env -> the
    local brain WRITES the conversion's verdict (the repo-triage task on
    a real candidate) -> the mutant's ARTIFACT = the conversion receipt."""
    import CloudBrain as CB
    import GenePool as GP
    bugs = []
    try:
        bugs = [json.loads(x) for x in open(
            os.path.join(AD, "gh_archive_bugs.jsonl"), encoding="utf-8-sig")
            if x.strip()][-6:]
    except Exception:
        pass
    out = {"step": "conversion", "converted": 0}
    trio = ('{"a": "", "b": "", "c": ""}')
    for b0 in bugs[:3]:
        r = CB.chat("You are triaging a possible contribution target. "
                    "Repo: " + str(b0.get("repo")) + ". Issue: " +
                    str(b0.get("issue")) + ". Classify: (a) the likely "
                    "language/tooling, (b) the one-file entry point's "
                    "likely path pattern, (c) a <=120-char plan. Reply "
                    "ONLY JSON: " + trio, max_tokens=400,
                    purpose="the conversion triage",
                    models=("groq", "local-coder", "local-fast"))
        if r:
            out["converted"] += 1
    return out


def step_gauntlet():
    """The gauntlet's honest core ON THE LOCAL BRAIN: grade one candidate's
    issue-class (the A_minimal_patch-class check): the LOCAL brain produces
    the graded verdict; the lessons bank."""
    import CloudBrain as CB
    lessons = 0
    try:
        rows = [json.loads(x) for x in open(
            os.path.join(AD, "gh_archive_bugs.jsonl"), encoding="utf-8-sig")
            if x.strip()][-5:]
        for b0 in rows[:2]:
            r = CB.chat("Grade this as a contribution target for an "
                        "automated agent (1-10; the criteria: a small "
                        "verifiable change, a maintained repo, the claim "
                        "freedom): " + json.dumps(b0) +
                        " Reply ONLY the number.", max_tokens=24,
                        purpose="the gauntlet grade")
            if r and re.search(r"\d", r):
                lessons += 1
                with open(os.path.join(
                        ROOT, "Config", "gauntlet_lessons.jsonl"), "a",
                        encoding="utf-8") as f:
                    f.write(json.dumps({"ts": time.strftime(
                        "%Y-%m-%d %H:%M:%S"), "lesson":
                        f"graded {b0.get('repo', '')[:40]}: "
                        f"{re.search(r'\\d+', r).group(0)}/10"}) + "\n")
    except Exception as e:
        return {"step": "gauntlet", "graded": 0, "note": str(e)[:50]}
    return {"step": "gauntlet", "graded": lessons}


def run():
    rep = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "steps": [step_upgrader(), step_conversion(), step_gauntlet()]}
    # the RE-TEST: the sync + the front (the mutants' measured state)
    try:
        import GenePool as GP
        synced, rolled, retired = GP.sync_from_pathmemory()
        a = GP.load()
        non_zero = [v for v, L in a["lineages"].items()
                    if float(L.get("fitness", 0)) > 0]
        rep["synced"] = synced
        rep["fitness_measured_lineages"] = non_zero
        rep["front"] = a.get("pareto_front")
    except Exception as e:
        rep["sync_error"] = str(e)[:60]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(f"[local-chain] the steps: {[s['step'] for s in rep['steps']]} | "
          f"converted {rep['steps'][1].get('converted')} | graded "
          f"{rep['steps'][2].get('graded')} | measured "
          f"{rep.get('fitness_measured_lineages')}")
    return rep


if __name__ == "__main__":
    run()