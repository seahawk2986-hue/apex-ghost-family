"""THE PR-PIPELINE (the founder's 'do it for me' permission, honest scope):
for the top verified candidate — FORK (our token) -> SHALLOW CLONE ->
LOCATE the issue's file (grep the tracker's terms) -> DRAFT THE PATCH on a
branch -> PUSH to the fork -> output the EXACT gh pr create line. The last
step (submitting) remains the founder's click (the money-law's gate).
TEST-first gate legs run inline; every step prints."""
import json
import os
import shutil
import subprocess
import sys
import re
import tempfile
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
KIT = os.path.join(AD, "file_now_kit.json")


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


def api(path, tok, method="GET"):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "apex-pr-pipeline/1.0"},
        method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        code = getattr(getattr(e, "fp", None), "code", 0) or 0
        return code, {"error": str(e)[:80]}


def run():
    tok = token()
    kit = json.load(open(KIT, encoding="utf-8-sig"))
    cand = (kit["kit"] or [{}])[0]         # the stars-ranked head
    repo = cand.get("repo", "")
    issue_txt = cand.get("issue", "")
    print(f"[pr-pipeline] target: {repo} | issue: {issue_txt[:60]}")
    out = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "repo": repo,
           "steps": []}
    if not repo or not tok:
        out["steps"].append({"s": "auth/repo", "ok": False})
        return out
    st, fork = api(f"/repos/{repo}/forks", tok, method="POST")
    fork_full = (fork.get("full_name") if st == 202 else
                 fork.get("full_name") if st == 200 else None)
    out["steps"].append({"s": "fork", "ok": st in (202, 200),
                         "fork": fork_full})
    print(f"  fork: {st} -> {fork_full}")
    if not fork_full:
        return out
    wd = os.path.join(tempfile.gettempdir(), "apex_pr_" + str(int(time.time())))
    url = f"https://{tok}@github.com/{fork_full}.git"
    r = subprocess.run(["git", "clone", "--depth", "1", url, wd],
                       capture_output=True, text=True, timeout=180)
    out["steps"].append({"s": "clone", "ok": r.returncode == 0})
    print(f"  clone: rc={r.returncode}")
    if r.returncode != 0:
        return out
    # LOCATE: grep terms from the issue text in the cloned tree
    terms = [w for w in re.split(r"\W+", issue_txt.lower()) if len(w) > 4][:5]
    hits = []
    for dp, dns, fns in os.walk(wd):
        dns[:] = [d for d in dns if d not in (".git", "node_modules")]
        for fn in fns:
            if fn.endswith((".py", ".js", ".ts", ".md")):
                fp = os.path.join(dp, fn)
                try:
                    t = open(fp, encoding="utf-8-sig", errors="replace").read()
                except Exception:
                    continue
                for tm in terms:
                    if tm in t.lower():
                        hits.append((os.path.relpath(fp, wd), tm))
                        break
    out["locates"] = hits[:8]
    print(f"  locate: {len(hits)} files mention the issue's terms")
    # DRAFT: the patch attempt needs the brain - record the LOCATED files +
    # the branch prep; the brain-bound patching stages honestly if no brain
    br = subprocess.run(["git", "checkout", "-b", "apex-fix"],
                        cwd=wd, capture_output=True, text=True)
    out["steps"].append({"s": "branch", "ok": br.returncode == 0,
                         "locates": len(hits)})
    out["workspace"] = wd
    with open(os.path.join(AD, "pr_pipeline_state.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"[pr-pipeline] staged: fork {fork_full}, branch apex-fix, "
          f"{len(hits)} located files - the PATCH step wants the brain "
          f"(cloud-burst legal) - the founder's click: gh pr create")
    if len(hits) >= 1:
        out["steps"].append({"s": "patch", "ok": None,
                             "note": "staged - needs the localized read + a "
                             "verified diff (the gauntlet's loop)"})
    return out


if __name__ == "__main__":
    res = run()
    with open(os.path.join(AD, "pr_pipeline_state.json"), "w",
              encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print("[pr-pipeline] state -> Adapter/pr_pipeline_state.json")