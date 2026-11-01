"""THE BOUNDED PATCH LOOP (PatchStep v2): the canon's iterative-refinement
multi-turn method, inside the DrainGate. ROUNDS (max 3 cloud calls ≈
$0.005 total, each ledgered):
 1. SELECT: the issue + the workspace's FILE LIST -> the brain names the
    3-6 files to read (JSON);
 2. DRAFT: those files' real content -> the UNIFIED DIFF;
 3. FIX (conditional): if git apply --check fails, one bounded retry with
    the error text; then commit + push to OUR FORK; the founder's one click.
Honest stops at every refusal; the think-strip; the cap always enforced."""
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
STATE = os.path.join(AD, "pr_pipeline_state.json")
LT = "<" + "think"
GE = "</" + "think"
STRIP = re.compile(re.escape(LT) + r".*?" + re.escape(GE) + r"\s*", re.S | re.I)


def read_jsonl(p):
    try:
        return [json.loads(x) for x in open(p, encoding="utf-8-sig")
                if x.strip()]
    except Exception:
        return []


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True, timeout=120)


def run():
    import CloudBrain as CB
    state = json.load(open(STATE, encoding="utf-8-sig"))
    repo, wd = state["repo"], state["workspace"]
    if not os.path.isdir(wd):
        print("[loop] the workspace is gone - rerun PrPipeline.py")
        return None
    env_keys = CB.env_keys()
    # the issue body (cached from the earlier probes: re-fetch cheaply)
    import PatchStep as PS
    tok = PS.token()
    st, issues = PS.api(f"/repos/{repo}/issues?state=open&per_page=30", tok)
    body = ""
    issue_no = None
    for it in (issues if st == 200 else []):
        if "muse" in ((it.get("title", "") + (it.get("body") or "")).lower()):
            issue_no, body = it.get("number"), (it.get("body") or "")[:4000]
            break
    if not issue_no:
        print("[loop] the issue not found - honest stop")
        return None
    # ROUND 1: SELECT
    tree = subprocess.run(["git", "ls-files"], cwd=wd, capture_output=True,
                          text=True, timeout=60).stdout.splitlines()
    sel_prompt = (f"ISSUE #{issue_no}:\n{body[:1800]}\n\nREPO FILES (names):\n"
                  + "\n".join(tree[:400]) +
                  "\n\nWhich 3-6 files (paths as given) must be READ to "
                  "implement a hook command for this? Reply ONLY JSON: "
                  '{"files": ["path", ...], "what": "<=300 chars"}')
    sel = CB.chat(sel_prompt, max_tokens=400, purpose="patch-select")
    if not sel:
        return None
    sel = STRIP.sub("", sel).strip()
    m = re.search(r"\{.*\}", sel, re.S)
    files = []
    if m:
        try:
            files = json.loads(m.group(0)).get("files", [])[:6]
        except Exception:
            files = []
    if not files:                      # fallback: the located files
        files = [f for f, _ in (state.get("locates") or [])][:4]
    print(f"[loop] selected files: {files}")
    # ROUND 2: DRAFT
    texts = []
    for rel in files:
        fp = os.path.join(wd, rel)
        try:
            texts.append(f"{rel}:\n" + open(
                fp, encoding="utf-8-sig", errors="replace").read()[:5000])
        except Exception:
            pass
    if not texts:
        print("[loop] the selected files unreadable - honest stop")
        return None
    draft_prompt = (f"ISSUE #{issue_no}:\n{body[:1800]}\n\n" +
                    "\n====\n".join(texts) +
                    "\n\nWrite the change as a UNIFIED DIFF (git apply "
                    "format, correct paths). Reply ONLY with the diff in "
                    "one ```diff block.")
    diff = CB.chat(draft_prompt, max_tokens=2000, purpose="patch-draft")
    if not diff:
        return None
    diff = STRIP.sub("", diff).strip()
    if "```diff" in diff:
        diff = diff[diff.index("```diff") + 7: diff.rindex("```")]
    # APPLY
    for attempt in range(1, 3):
        pd = os.path.join(wd, "apex.patch")
        with open(pd, "w", encoding="utf-8") as f:
            f.write(diff)
        r = git("apply", "--check", pd, cwd=wd)
        if r.returncode == 0:
            break
        print(f"[loop] apply-check failed (attempt {attempt}): "
              f"{(r.stderr or '')[:80]}")
        if attempt == 2:
            print("[loop] the diff never applied - honest stop")
            return None
        fix = CB.chat("The diff failed: " + (r.stderr or "")[:400] +
                      "\n\nThe diff:\n" + diff[:3000] +
                      "\nReply ONLY with the corrected ```diff block.",
                      max_tokens=2000, purpose="patch-fix")
        if not fix:
            return None
        diff = STRIP.sub("", fix).strip()
        if "```diff" in fix:
            diff = fix[fix.index("```diff") + 7: fix.rindex("```")]
    git("apply", pd, cwd=wd)
    git("add", "-A", cwd=wd)
    cm = git("commit", "-m", f"fix: advance issue #{issue_no} "
             f"(apex-ghost-family, automated draft - disclosed)", cwd=wd)
    ok = cm.returncode == 0
    ph = git("push", "-u", "origin", "apex-fix", cwd=wd)
    print(f"[loop] commit rc={cm.returncode} | push rc={ph.returncode} "
          f"{(ph.stderr or '')[:60]}")
    print(f"\n[loop] THE FOUNDER'S ONE CLICK:\ngh pr create -R {repo} "
          f"--head seahawk2986-hue:apex-fix --title 'fix: hook muse "
          f"(issue #{issue_no})' --body 'Fixes #{issue_no}. Automated draft "
          f"by apex-ghost-family (disclosed); founder-verified.'")
    with open(os.path.join(AD, "patch_state.json"), "w",
              encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "issue": issue_no, "patch_applied": ok,
                   "pushed": ph.returncode == 0, "files": files}, f,
                  indent=1)
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)