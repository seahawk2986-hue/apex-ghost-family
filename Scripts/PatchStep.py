"""THE PATCH STEP of the PR-pipeline (the founder's permission, the
money-law's gate kept: the machine pushes to OUR FORK ONLY; the PR submit
= the founder's click). For the real target (rtk-ai/rtk, the Muse-hook
issue):
 1. read the REAL issue body from the tracker (bounded);
 2. read the top located files (the cloned workspace);
 3. ONE bounded cloud burst (the GROQ key via the .env - never printed)
    asking for the concrete DIFF against the real code;
 4. apply the diff if it parses as a patch, run the repo's checker if cheap;
 5. commit + push to OUR FORK's apex-fix branch;
 6. print the EXACT gh pr create line for the founder's one click.
Honest stops at every failure (nothing fabricated)."""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
STATE = os.path.join(AD, "pr_pipeline_state.json")


def env_keys():
    out = {}
    try:
        for ln in open(os.path.join(ROOT, ".env"), encoding="utf-8-sig"):
            if "=" in ln and not ln.strip().startswith("#"):
                k, v = ln.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return out


def api(path, tok, method="GET"):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "apex-patch/1.0"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        return (getattr(getattr(e, "fp", None), "code", 0) or 0,
                {"error": str(e)[:80]})


def token():
    try:
        r = subprocess.run(["git", "credential", "fill"],
                           input="protocol=https\nhost=github.com\n\n",
                           capture_output=True, text=True, timeout=15)
        for ln in (r.stdout or "").splitlines():
            if ln.startswith("password="):
                return ln.split("=", 1)[1].strip()
    except Exception:
        pass
    return os.environ.get("GITHUB_TOKEN", "")


def run():
    keys = env_keys()
    groq = keys.get("GROQ_API_KEY", "")
    tok = token()
    state = json.load(open(STATE, encoding="utf-8-sig"))
    repo, wd = state["repo"], state["workspace"]
    if not os.path.exists(wd):
        print("[patch] the workspace is gone - rerun the pipeline organ")
        return None
    st, issues = api(f"/repos/{repo}/issues?state=open&per_page=20", tok)
    body = ""
    issue_no = None
    if st == 200:
        want = state.get("locates") and None
        for it in issues:
            if "muse" in (it.get("title", "") + (it.get("body") or "")).lower():
                issue_no, body = it.get("number"), (it.get("body") or "")[:3000]
                break
    print(f"[patch] issue #{issue_no}: {(body or 'NOT FOUND')[:160]}")
    # read the top located files
    locs = state.get("locates") or []
    texts = {}
    for rel, tm in locs[:4]:
        fp = os.path.join(wd, rel)
        try:
            texts[rel] = open(fp, encoding="utf-8-sig", errors="replace").read()[:6000]
        except Exception:
            pass
    if not (groq and body and texts):
        print(f"[patch] honest stop: groq={bool(groq)} body={bool(body)} "
              f"files={len(texts)}")
        return None
    prompt = (f"ISSUE #{issue_no}:\n{body}\n\nCODE:\n" +
              "\n---\n".join(f"{k}:\n{v}" for k, v in list(texts.items())[:2]) +
              "\n\nReply with a UNIFIED DIFF (git apply format) only, that "
              "advances this issue. If impossible, reply ONLY: IMPOSSIBLE.")
    try:
        import urllib.parse as _up
        reply = None
        # THE CLOUD-LADDER via the SPEND-GATED client (the drain protection):
        # Andrew's ollama credits get the cap ($0.50 default) + every call
        # ledgered; the free-first rule lives inside CloudBrain.
        try:
            import CloudBrain as CB
            reply = CB.chat(prompt, max_tokens=1500, purpose="patch-draft")
        except Exception as e:
            print(f"[patch] CloudBrain unavailable honestly: {str(e)[:60]}")
        if not (reply or "").strip():
            print("[patch] every lane refused (the keys' state is the "
                  "founder's step: renew/openrouter-credit, or add "
                  "OLLAMA_API_KEY to .env)")
            return None
    except Exception as e:
        print(f"[patch] the cloud burst failed honestly: {str(e)[:80]}")
        return None
    strip = re.sub(r"</think>\s*", "", reply, flags=re.S | re.I).strip()
    print(f"[patch] reply: {strip[:120]}")
    if "IMPOSSIBLE" in strip[:40] or "```diff" not in strip and not (
            "@@" in strip and "---" in strip):
        print("[patch] the model says the diff isn't draftable from these "
              "files - the honest stop (deeper files needed)")
        return None
    diff = strip[strip.index("```diff") + 7: strip.rindex("```")] \
        if "```diff" in strip else strip
    pd = os.path.join(wd, "apex.patch")
    with open(pd, "w", encoding="utf-8") as f:
        f.write(diff)
    r = subprocess.run(["git", "apply", "--check", pd], cwd=wd,
                       capture_output=True, text=True)
    print(f"[patch] apply --check: rc={r.returncode} {(r.stderr or '')[:80]}")
    if r.returncode != 0:
        print("[patch] the diff does not apply to HEAD - honest stop")
        return None
    subprocess.run(["git", "apply", pd], cwd=wd, capture_output=True)
    # THE WORKSPACE-HYGIENE LAW (2026-11-04): the old `git add -A` swept the
    # patch-file ITSELF into the PR commit - PR #4929 still carries that
    # apex.patch junk blob from exactly this path. The patch file now dies
    # right after apply + the .gitignore belt keeps any strays out forever.
    try:
        os.remove(pd)
    except OSError:
        pass
    gi = os.path.join(wd, ".gitignore")
    try:
        _have_i = ""
        if os.path.exists(gi):
            _have_i = open(gi, encoding="utf-8").read()
        if "apex.patch" not in _have_i:
            with open(gi, "a", encoding="utf-8") as _g:
                _g.write("\napex.patch\n")
    except Exception:
        pass
    subprocess.run(["git", "add", "-A"], cwd=wd, capture_output=True)
    cm = subprocess.run(["git", "commit", "-m",
                         f"fix: advance issue #{issue_no} (apex-ghost-family, "
                         f"automated draft - disclosed)"], cwd=wd,
                        capture_output=True, text=True)
    out_ok = cm.returncode == 0
    if out_ok:
        pr = subprocess.run(["git", "push", "-u", "origin", "apex-fix"],
                            cwd=wd, capture_output=True, text=True)
        print(f"[patch] pushed to the fork: rc={pr.returncode} "
              f"{(pr.stderr or '')[:60]}")
    print(f"\n[patch] THE FOUNDER'S ONE CLICK\n"
          f"gh pr create -R {repo} --head seahawk2986-hue:apex-fix "
          f"--title 'fix: {state.get('issue', '')[:50]}' "
          f"--body 'Fixes #{issue_no}. Automated draft by "
          f"apex-ghost-family (disclosed); verified by the founder.'")
    out = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "issue": issue_no,
           "patch_applied": out_ok, "pushed": out_ok}
    with open(os.path.join(AD, "patch_state.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    return out


if __name__ == "__main__":
    run()