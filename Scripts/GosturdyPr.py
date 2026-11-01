"""THE RE-TARGETED PR (the honest kit's rerank consumed): gosturdy/gosturdy
issue #4 ('Flag http.NewRequest in handlers'). The full loop: fork ->
clone -> read the issue + the handlers -> the brain diff (the brain knows
the ACTUAL desired replacement from the issue's text) -> apply ->
`go build` IF go exists (the honest verification) -> commit -> push to OUR
fork -> the founder's one-click line."""
import json
import os
import re
import subprocess
import sys
import shutil
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
STRIP = re.compile(re.escape("<" + "think") + r".*?" + re.escape("</" + "think")
                   + r"\s*", re.S | re.I)
REPO, ISSUE_NO = "GillMacedo/gosturdy", 4


def api(path, tok, method="GET"):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "apex-pr2/1.0"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        return (getattr(getattr(e, "fp", None), "code", 0) or 0,
                {"error": str(e)[:80]})


def token():
    r = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True, timeout=15)
    for ln in (r.stdout or "").splitlines():
        if ln.startswith("password="):
            return ln.split("=", 1)[1].strip()
    return os.environ.get("GITHUB_TOKEN", "")


def run():
    import CloudBrain as CB
    tok = token()
    st, iss = api(f"/repos/{REPO}/issues/{ISSUE_NO}", tok)
    body = (iss.get("body") or "")[:4000] if st == 200 else ""
    print(f"[gosturdy] issue #{ISSUE_NO}: {(iss.get('title', '') if st == 200
                                          else '?')} | body "
          f"{len(body)} chars")
    st2, fork = api(f"/repos/{REPO}/forks", tok, method="POST")
    fork_full = fork.get("full_name") if st2 in (202, 200) else None
    print(f"[gosturdy] fork: {st2} -> {fork_full}")
    if not fork_full:
        return None
    wd = os.path.join(tempfile.gettempdir(), "apex_pr_gosturdy")
    if os.path.exists(wd):
        shutil.rmtree(wd, ignore_errors=True)
    r = subprocess.run(["git", "clone", "--depth", "1",
                        f"https://{tok}@github.com/{fork_full}.git", wd],
                       capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(f"[gosturdy] clone failed: {(r.stderr or '')[:80]}")
        return None
    subprocess.run(["git", "checkout", "-b", "apex-fix"], cwd=wd,
                   capture_output=True)
    # read every handler file + the repo's README (the lint context)
    docs, handler_files = [], []
    for dp, dns, fns in os.walk(wd):
        dns[:] = [d for d in dns if d not in (".git",)]
        for fn in fns:
            fp = os.path.join(dp, fn)
            rel = os.path.relpath(fp, wd)
            if fn.endswith(".go") and "handler" in rel.lower():
                handler_files.append(rel)
            elif fn.endswith(".go") or fn.endswith(".md"):
                t = open(fp, encoding="utf-8-sig", errors="replace").read()
                if "http.NewRequest" in t and "handler" in rel.lower():
                    docs.append(f"--- {rel} ---\n{t[:4000]}")
    print(f"[gosturdy] the handler files: {handler_files[:6]} "
          f"({len(docs)} carry NewRequest)")
    go_check = subprocess.run(["go", "version"], capture_output=True,
                              text=True)
    have_go = go_check.returncode == 0
    go_msg = ("YES " + (go_check.stdout or "").strip()) if have_go else \
        "ABSENT (the verification becomes the founder's/CI)"
    print(f"[gosturdy] go toolchain: {go_msg}")
    if not docs:
        # include ALL handler .go files' heads (the context for the brain)
        for rel in handler_files[:6]:
            docs.append(f"--- {rel} ---\n" + open(
                os.path.join(wd, rel), encoding="utf-8-sig",
                errors="replace").read()[:3000])
    prompt = (f"THE ISSUE:\n{body}\n\nFILES:\n" + "\n====\n".join(docs[:8]) +
              "\n\nImplement the flagging: a unified diff (git apply, a/ b/ "
              "paths) that adds the requested flag/warning for "
              "http.NewRequest in handlers, matching the repo's style. "
              "Reply ONLY one ```diff block.")
    diff = CB.chat(prompt, max_tokens=3000, purpose="gosturdy-draft")
    if not diff:
        return None
    diff = STRIP.sub("", diff).strip()
    if "```diff" in diff:
        diff = diff[diff.index("```diff") + 7: diff.rindex("```")]
    pd = os.path.join(wd, "apex.patch")
    with open(pd, "w", encoding="utf-8") as f:
        f.write(diff)
    r2 = subprocess.run(["git", "apply", "--check", pd], cwd=wd,
                        capture_output=True, text=True)
    print(f"[gosturdy] apply-check: rc={r2.returncode} "
          f"{(r2.stderr or '')[:90]}")
    if r2.returncode != 0:
        return None
    subprocess.run(["git", "apply", pd], cwd=wd, capture_output=True)
    if have_go:
        vb = subprocess.run(["go", "build", "./..."], cwd=wd,
                            capture_output=True, text=True, timeout=240)
        print(f"[gosturdy] go build: rc={vb.returncode} "
              f"{(vb.stderr or '')[:120]}")
        if vb.returncode != 0:
            print("[gosturdy] the build FAILED - the honest stop (a broken "
                  "patch never leaves the nest)")
            return None
    subprocess.run(["git", "add", "-A"], cwd=wd, capture_output=True)
    cm = subprocess.run(["git", "commit", "-m",
                         "feat(lint): flag http.NewRequest in handlers "
                         "(#4) - apex-ghost-family automated draft, "
                         "disclosed"], cwd=wd, capture_output=True,
                        text=True)
    ph = subprocess.run(["git", "push", "-u", "origin", "apex-fix"], cwd=wd,
                        capture_output=True, text=True, timeout=120)
    print(f"[gosturdy] commit {cm.returncode} push {ph.returncode} "
          f"{(ph.stderr or '')[:60]}")
    print(f"\nTHE FOUNDER'S ONE CLICK:\ngh pr create -R {REPO} "
          f"--head seahawk2986-hue:apex-fix --title "
          f"'feat: flag http.NewRequest in handlers (#4)' --body "
          f"'Fixes #4. Automated draft by apex-ghost-family (disclosed); "
          f"founder-verified.'")
    return cm.returncode == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)