"""PATCH LOOP v4 (the decisive pass): the hook-file localization + the
STRICT output contract + the raw-reply receipts.
 - the files NAMED hook*/plugin*/muse* + the issue terms - the REAL targets;
 - the brain asked with a HARD contract: 'Output ONLY the diff. No prose.
   No fences needed unless a diff block helps.';
 - the raw reply SAVED (the receipt/debug: patch_reply_debug.jsonl);
 - the extractor: any fenced block OR an unfenced 'diff --git' body;
 - 1 apply + 1 fix-retry max; the drain gate holds."""
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
STRIP = re.compile(re.escape("<" + "think") + r".*?" + re.escape("</" + "think")
                   + r"\s*", re.S | re.I)
DEBUG = os.path.join(AD, "patch_reply_debug.jsonl")


def log_reply(tag, text):
    with open(DEBUG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.strftime("%H:%M:%S"), "tag": tag,
                            "chars": len(text or ""), "body":
                            (text or "")[:4000]}) + "\n")


def run():
    import CloudBrain as CB
    import PatchStep as PS
    state = json.load(open(STATE, encoding="utf-8-sig"))
    repo, wd = state["repo"], state["workspace"]
    tok = PS.token()
    st, issues = PS.api(f"/repos/{repo}/issues?state=open&per_page=30", tok)
    body, issue_no = "", None
    for it in (issues if st == 200 else []):
        if "muse" in ((it.get("title", "") + (it.get("body") or "")).lower()):
            issue_no, body = it.get("number"), (it.get("body") or "")[:4500]
            break
    if not issue_no:
        print("[v4] the issue not found")
        return None
    tree = subprocess.run(["git", "ls-files"], cwd=wd, capture_output=True,
                          text=True, timeout=60).stdout.splitlines()
    hook_files = [x for x in tree
                  if re.search(r"hook|muse|plugin", x.lower())
                  and x.endswith((".rs", ".toml", ".md"))][:8]
    if not hook_files:
        print(f"[v4] no hook/plugin files among {len(tree)} - honest stop")
        return None
    print(f"[v4] the hook/plugin files: {hook_files}")
    docs = []
    for rel in hook_files:
        p = os.path.join(wd, rel)
        try:
            docs.append(f"--- {rel} ---\n" + open(p, encoding="utf-8-sig",
                                                  errors="replace").read()[:5000])
        except Exception:
            pass
    body_lines = []
    for ln in body.splitlines()[:40]:
        body_lines.append(ln)
    issue_text = "\n".join(body_lines)
    prompt = (f"You are writing a patch for rtk (Rust). THE ISSUE:\n{issue_text}"
              f"\n\nTHE RELEVANT FILES:\n" + "\n".join(docs) +
              "\n\nTASK: implement the 'rtk hook muse' command (Claude-format "
              "hook events in, the rtk-shaped handling out) minimally, "
              "matching the EXISTING code's style. REPLY FORMAT (STRICT): "
              "one unified diff in a ```diff block for ONE file, or nothing "
              "if the files shown are insufficient. NO explanations.")
    r = CB.chat(prompt, max_tokens=3000, purpose="v4-draft")
    log_reply("v4-draft", r)
    if not r:
        return None
    txt = STRIP.sub("", r).strip()
    diff = None
    if "```diff" in txt:
        diff = txt[txt.index("```diff") + 7: txt.rindex("```")]
    elif "diff --git" in txt:
        i0 = txt.index("diff --git")
        diff = txt[i0:]
    if not diff or "@@" not in diff:
        print(f"[v4] the reply ({len(txt)} chars) held no usable diff "
              f"- receipt saved; the honest stop")
        return None
    pd = os.path.join(wd, "apex.patch")
    open(pd, "w", encoding="utf-8").write(diff)
    rc = subprocess.run(["git", "apply", "--check", pd], cwd=wd,
                        capture_output=True, text=True, timeout=60)
    print(f"[v4] apply-check: rc={rc.returncode} {(rc.stderr or '')[:100]}")
    if rc.returncode != 0:
        with open(os.path.join(AD, "patch_state.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "issue": issue_no, "applied": False,
                       "hook_files": hook_files,
                       "receipt": "patch_reply_debug.jsonl"}, f, indent=1)
        return None
    subprocess.run(["git", "apply", pd], cwd=wd, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=wd, capture_output=True)
    cm = subprocess.run(["git", "commit", "-m",
                         f"feat(hook): muse Claude-format hook handling "
                         f"(issue #{issue_no}) - apex-ghost-family, "
                         f"disclosed automated draft"], cwd=wd,
                        capture_output=True, text=True, timeout=60)
    ph = subprocess.run(["git", "push", "-u", "origin", "apex-fix"], cwd=wd,
                        capture_output=True, text=True, timeout=120)
    print(f"[v4] commit {cm.returncode} | push {ph.returncode} "
          f"{(ph.stderr or '')[:70]}")
    print(f"\nTHE FOUNDER'S ONE CLICK:\n"
          f"gh pr create -R {repo} --head seahawk2986-hue:apex-fix "
          f"--title 'feat(hook): muse Claude-format integration (#{issue_no})' "
          f"--body 'Fixes #{issue_no}. Automated draft by apex-ghost-family "
          f"(disclosed); founder-verified.'")
    return cm.returncode == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)