"""THE MUSE PROVIDER PATCH (v5 - the decisive, honest one): the issue asks
'rtk hook muse' with Muse's Agent-Plugin 1.0.0 bundle format. The pattern =
hooks/<provider>/ (README + the hook script + tests). NOT a diff-edit: NEW
FILES - which is why v2-v4's diffs never applied. Steps:
 1. the FULL issue body + the claude-pattern files read (real);
 2. ONE brain call: produce {path: content} for the muse bundle (the
    claude-shape events preserved);
 3. write the files DIRECTLY in the workspace (no diff apply needed);
 4. bash -n syntax-check + commit + push to OUR FORK;
 5. the founder's one click: gh pr create.
The drain gate: 1-2 calls, ledgered."""
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


def run():
    import CloudBrain as CB
    import PatchStep as PS
    state = json.load(open(STATE, encoding="utf-8-sig"))
    repo, wd = state["repo"], state["workspace"]
    tok = PS.token()
    st, issues = PS.api(f"/repos/{repo}/issues?state=open&per_page=40", tok)
    body, issue_no = "", None
    for it in (issues if st == 200 else []):
        if "muse" in ((it.get("title", "") + (it.get("body") or "")).lower()):
            issue_no, body = it.get("number"), (it.get("body") or "")[:6000]
            break
    if not issue_no:
        print("[v5] the issue not found")
        return None
    def rd(rel, n=6000):
        try:
            return open(os.path.join(wd, rel), encoding="utf-8-sig",
                        errors="replace").read()[:n]
        except Exception:
            return ""
    claude_sh = rd("hooks/claude/rtk-rewrite.sh")
    hooks_main = rd("hooks/README.md", 3000)
    posthook = rd("engine/builtin/posthook.toml", 1500)
    print(f"[v5] issue #{issue_no} body {len(body)} chars | claude hook "
          f"{len(claude_sh)} chars")
    prompt = (f"THE ISSUE (verbatim):\n{body}\n\n"
              f"THE EXISTING CLAUDE PROVIDER (the pattern to follow):\n"
              f"hooks/claude/rtk-rewrite.sh:\n{claude_sh}\n\n"
              f"hooks/README.md (head):\n{hooks_main}\n\n"
              f"TASK: produce the hooks/muse/ provider bundle for Muse Code "
              f"1.4.x (Agent Plugins 1.0.0: .claude-plugin/plugin.json + "
              f"hooks/hooks.json, Claude-format events - muse consumes "
              f"CLAUDE-SHAPE events per the issue). Reply ONLY JSON: "
              f'{{"files": {{"hooks/muse/<path>": "<content>", ...}}}} '
              f"with 2-4 files (the plugin.json, hooks.json, the shell hook "
              f"- rtk-rewrite.sh muse-adapted, and README.md). No fences.")
    r = CB.chat(prompt, max_tokens=3500, purpose="v5-muse-bundle")
    if not r:
        return None
    txt = STRIP.sub("", r).strip()
    m = re.search(r"\{[\s\S]*\}", txt)
    if not m:
        print(f"[v5] no JSON in the reply ({len(txt)} chars) - the receipt: "
              f"kept; honest stop")
        with open(os.path.join(AD, "patch_reply_debug.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%H:%M:%S"),
                                "tag": "v5-muse", "chars": len(txt),
                                "body": txt[:4000]}) + "\n")
        return None
    try:
        files = json.loads(m.group(0)).get("files", {})
    except Exception as e:
        print(f"[v5] the JSON unparseable: {str(e)[:50]} - receipt saved")
        return None
    if not files:
        print("[v5] the empty files map - honest stop")
        return None
    made = []
    for rel, content in files.items():
        rel = str(rel).replace("\\", "/").lstrip("/")
        if ".." in rel or not rel.startswith("hooks/"):
            continue                       # the path guard (never逃 escape)
        fp = os.path.join(wd, rel)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8", newline="\n") as f:
            f.write(str(content))
        made.append(rel)
        if rel.endswith(".sh"):
            os.chmod(fp, 0o755)
            sh = subprocess.run(["bash", "-n", fp], capture_output=True,
                                text=True)
            print(f"[v5] {rel}: bash -n rc={sh.returncode}")
    print(f"[v5] files written: {made}")
    if not made:
        print("[v5] nothing valid to commit - honest stop")
        return None
    subprocess.run(["git", "add", "hooks/muse" if False else "hooks/"],
                   cwd=wd, capture_output=True)
    cm = subprocess.run(["git", "commit", "-m",
                         f"feat(hooks): the muse provider (Agent Plugins "
                         f"1.0.0, Claude-shape events) - issue #{issue_no}, "
                         f"apex-ghost-family automated draft, disclosed"],
                        cwd=wd, capture_output=True, text=True, timeout=60)
    ph = subprocess.run(["git", "push", "-u", "origin", "apex-fix"], cwd=wd,
                        capture_output=True, text=True, timeout=120)
    print(f"[v5] commit {cm.returncode} | push {ph.returncode} "
          f"{(ph.stderr or '')[:70]}")
    print(f"\nTHE FOUNDER'S ONE CLICK:\n"
          f"gh pr create -R {repo} --head seahawk2986-hue:apex-fix "
          f"--title 'feat(hooks): muse provider (Agent Plugins 1.0.0)' "
          f"--body 'Fixes #{issue_no}. The muse bundle follows "
          f"hooks/claude's shape (Claude-format events). Automated draft by "
          f"apex-ghost-family (disclosed); founder-verified.'")
    with open(os.path.join(AD, "patch_state.json"), "w",
              encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "issue": issue_no, "files": made,
                   "pushed": ph.returncode == 0}, f, indent=1)
    return cm.returncode == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)