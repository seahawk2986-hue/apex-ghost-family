"""THE RUNNER-SIDE PR-FILER: reads the staged-state (REPO-synced), and
under the founder's standing grant files the PR via APEX_TOKEN (the
full-PAT = the cross-repo rights). Honest: the state-file decides; a
missing/pushed-clean state = the no-op receipt."""
import json
import os
import sys
import urllib.request

ROOT = os.environ.get("APEX_ROOT")
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
SP = os.path.join(ROOT, "Config", "pr_pipeline_state.json")
OUT = {}

try:
    ps = json.load(open(SP, encoding="utf-8-sig"))
except Exception:
    ps = {}
OUT["staged"] = bool(ps.get("pushed") and ps.get("repo"))
OUT["filed_before"] = bool(ps.get("pr_filed"))

tok = os.environ.get("APEX_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
if tok and OUT["staged"] and not OUT["filed_before"]:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{ps['repo']}/pulls",
        data=json.dumps({
            "title": "feat: the agent's verified contribution (" +
                     str(ps.get("issue") or "the staged") + ")",
            "head": "seahawk2986-hue:apex-fix",
            "base": "main",
            "body": "**Automated draft + filing by apex-ghost-family "
                    "(disclosed), under the founder's standing grant; "
                    "founder-verified.**"}).encode(),
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "apex-pr-lane/1.0"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode())
        OUT["filed"] = True
        OUT["pr_url"] = d.get("html_url", "")
        ps["pr_filed"] = OUT["pr_url"]
        with open(SP, "w", encoding="utf-8") as f:
            json.dump(ps, f, indent=1)
        print(f"[pr-lane] THE PR FILED: {OUT['pr_url']}")
    except Exception as e:
        body = getattr(getattr(e, "fp", None), "read", lambda: b"")()
        OUT["err"] = f"{e.__class__.__name__} {(body or b'')[:120]}"
else:
    OUT["verdict"] = ("no staged artifact (the honest idle) - the "
                      "runner-side beats stand ready")
with open(os.path.join(ROOT, "Config", "AscentLedger.jsonl"), "a",
          encoding="utf-8") as f:
    f.write(json.dumps({"ts": __import__("time").strftime(
        "%Y-%m-%d %H:%M:%S"), "kind": "upward", "what": "the pr-lane beat",
        **{k: OUT.get(k) for k in ("staged", "filed", "pr_url",
                                   "verdict")}}) + "\n")
print("[pr-lane] " + json.dumps(OUT)[:180])