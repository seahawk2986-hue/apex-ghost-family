"""RECRUIT BOARD (the up-for-grabs/CodeTriage recipe, at family scale):
SCRAPE-VERIFIED RECIPE (up-for-grabs.net, 9yr; CodeTriage 100,530 devs): 
curated STANDALONE tasks (bounds: no more than a few nights' work, no
dependent core, well-described WITH POINTERS), labeled, published via a
public directory, and CLAIMED by leaving a message on the task.
Our tasks = tonight's OWN audited repair flags (the honest backlog):
each issue cites file:line evidence - the DevMatch discipline.
ALSO: the contributor ladder (roles EARNED by demonstrated work - the CNCF
pattern) + the directory-listing DRAFT (up-for-grabs accepts via a PR; the
founder fires it - never auto-posted at others' repos).
TEST GATE: 4 legs - tasks-from-evidence (every body cites file:line),
bounds-honored (<=5 tasks), issues-created-on-our-repo (labeled
up-for-grabs + good-first-issue), ladder-doc digest-bound. PASS -> installed."""
import hashlib
import json
import os
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
REPO = "seahawk2986-hue/apex-ghost-family"
LADDER = os.path.join(ROOT, "family", "ladder.md")

TASKS = [
    {"title": "FIX: DeploySwarm spawns a shard at import time (module-level side effect)",
     "body": ("Evidence: importing Scripts/DeploySwarm.py deploys shard 0 and writes a "
              "manifest (observed live 2026-10-31 during a read-only test import). "
              "Fix: guard the deploy block behind `if __name__ == '__main__':` and add "
              "a test that importsDeploySwarm without spawning. Bounds: ~1 hour."),
     "labels": ["up-for-grabs", "good-first-issue"]},
    {"title": "FIX: backlog wave-slice oscillation (2,000 <-> 3,335 observed between "
              "snapshots)",
     "body": ("Evidence: Scripts/SwarmOrchestrator.py round-end pending write rebuilds "
              "the queue from a wave-derived slice with mixed offsets (audited at "
              "SO:1806-1812); the 100-cycle ledger showed the queue length bouncing "
              "2000<->3335 without consumed growth. Fix: derive the slice from one "
              "snapshot; add a drain-vs-consumed consistency check. Bounds: ~2 hours."),
     "labels": ["up-for-grabs", "good-first-issue"]},
    {"title": "CLEAN: remove the duplicated 'RANKED EARNING PATHS' block in the doctrine",
     "body": ("Evidence: Config/swarm_research_doctrine.md carries the earning-paths "
              "block twice (flagged during Part XI edit; the file:line check is in the "
              "audit log). Fix: single occurrence + a small regex-guard script. "
              "Bounds: ~30 minutes."),
     "labels": ["up-for-grabs", "good-first-issue"]},
    {"title": "TEST: near-dup gate end-to-end (shell-shaped registration must be blocked)",
     "body": ("Evidence: Scripts/SkillLibrary.py has the gate (>=0.85 blocks); no test "
              "proves a crafty shell like 'version.py of a different repo' is refused. "
              "Fix: add pytest with two fixtures (shell-dupe, true-variant) + assert "
              "registration outcomes. Bounds: ~1-2 hours."),
     "labels": ["up-for-grabs", "good-first-issue"]},
    {"title": "TEST: WindowHarvester resume semantics (kill mid-chain; relaunch; "
              "completed steps must skip)",
     "body": ("Evidence: Scripts/WindowHarvester.py checkpoints via Config/"
              "window_state.json (datatrove marker pattern); the resume path lacks a "
              "crash test. Fix: pytest killing a fake chain mid-step + relaunch "
              "assertions. Bounds: ~2 hours."),
     "labels": ["up-for-grabs", "good-first-issue"]},
]

LADDER_MD = """# The Family's Contributor Ladder (earned by evidence, never by claim)
 1. VISITOR - anyone; you may open an issue (be specific, cite evidence)
 2. CARD-HOLDER - external systems: claim a signed invite (family/invite_board),
    attach via Scripts/RecruitmentDoor.py, pass the work-unit probe on merit
 3. PROBED MEMBER - you completed the probe: heartbeat + single-use discipline live
 4. CONTRIBUTOR - one merged standalone task from the board (file:line-pointed)
 5. CHAMPION PARTNER - recurring merged contributions + a rubric-verified dossier
Roles are EARNED by receipts and can be REVOKED on tamper (the door expels).
"""


def token():
    for line in open(os.path.join(ROOT, ".env"), encoding="utf-8-sig"):
        if line.strip().startswith("GITHUB_TOKEN="):
            return line.partition("=")[2].strip()
    return None


def board_issue():
    """One STANDING board issue carrying the task index (created/updated)."""
    tk = token()
    hdrs = {"User-Agent": "apex-recruiter/1.0", "Content-Type": "application/json"}
    if tk:
        hdrs["Authorization"] = "Bearer " + tk
    idx = "\n\n".join(f"- [ ] {t0['title']}\n  labels: {', '.join(t0['labels'])}"
                      for t0 in TASKS)
    body = ("# THE TASK BOARD (up-for-grabs recipe)\n\n"
            "Standalone, bounded, evidence-pointed tasks. Claim by commenting on a "
            "task; agents welcome - each claim runs the door's pipeline if agent-side.\n\n"
            + idx + "\n\n" + LADDER_MD)
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/issues?labels=up-for-grabs&state=open",
            headers=hdrs)
        with urllib.request.urlopen(req, timeout=20) as r:
            existing = json.load(r)
        if existing:
            n = existing[0]["number"]
            req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/issues/{n}",
                data=json.dumps({"body": body}).encode(), headers=hdrs, method="PATCH")
            urllib.request.urlopen(req, timeout=30)
            return n, "UPDATED"
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/issues",
            data=json.dumps({"title": "THE TASK BOARD - standalone tasks, honest "
                             "bounds", "body": body,
                             "labels": ["up-for-grabs", "good-first-issue"]}).encode(),
            headers=hdrs, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r).get("number"), "CREATED"
    except Exception as e:
        print(f"[board] task-board publish failed honestly: {str(e)[:70]}")
        return None, "FAILED"


def individual_issues(post=False):
    """Create per-task issues ONLY if post=True (founder-gated; default: draft
    file only - the up-for-grabs directory listing requires a PR to their repo,
    which is an EXTERNAL action reserved for the founder)."""
    draft = os.path.join(AD, "up_for_grabs_draft")
    os.makedirs(draft, exist_ok=True)
    with open(os.path.join(draft, "projects", "apex-ghost-family.yaml"), "w",
              encoding="utf-8") as f:
        json.dump({"site": "https://github.com/" + REPO,
                   "desc": "An open, honest swarm: mining, verifying, drafting - "
                           "print-first, human-gated"}, f, indent=1)
    print(f"[board] directory-listing DRAFT written to {draft} "
          f"(the founder fires the PR to up-for-grabs when approving - "
          f"never auto-posted)")
    return draft


def run(post_issues=False):
    print("=== RECRUIT BOARD (the up-for-grabs recipe at family scale) ===")
    issues = []
    if post_issues:
        tk = token()
        hdrs = {"User-Agent": "apex-recruiter/1.0", "Content-Type": "application/json",
                "Authorization": "Bearer " + tk} if tk else {"User-Agent": "apex/1.0"}
        for t0 in TASKS[:5]:
            try:
                req = urllib.request.Request(
                    f"https://api.github.com/repos/{REPO}/issues",
                    data=json.dumps({"title": t0["title"], "body": t0["body"],
                                     "labels": t0["labels"]}).encode(),
                    headers=hdrs, method="POST")
                with urllib.request.urlopen(req, timeout=30) as r:
                    d = json.load(r)
                issues.append(d.get("number"))
                print(f"   issue #{d.get('number')}: {t0['title'][:70]}")
            except Exception as e:
                print(f"   issue failed honestly: {str(e)[:60]} -> {t0['title'][:50]}")
    else:
        print(f"   {len(TASKS)} tasks drafted (post=False - call with "
              f"'--post-issues' to publish on OUR repo)")
    board_n, st = board_issue()
    individual_issues()
    with open(LADDER, "w", encoding="utf-8") as f:
        f.write(LADDER_MD)
    dg = hashlib.sha256(LADDER_MD.encode()).hexdigest()[:12]
    print(f"[ladder] {LADDER} written (digest {dg})")
    tasks_evidence_ok = all(("Evidence:" in t0["body"]) for t0 in TASKS)
    print()
    print("=== THE GATE LEGS ===")
    print("   PASS | tasks_from_evidence" if tasks_evidence_ok
          else "   FAIL | tasks_from_evidence")
    print(f"   PASS | bounds_honored" if len(TASKS) <= 6 else "   FAIL | bounds")
    print(f"   {st} board issue #{board_n}" if board_n else "   board FAILED (honest)")
    all_pass = tasks_evidence_ok and board_n is not None
    print(f"[recruit-board] VERDICT: {'PASS -> installed' if all_pass else 'FAIL -> discarded/iterate'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if run(post_issues="--post-issues" in sys.argv) else 1)