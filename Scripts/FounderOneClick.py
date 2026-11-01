"""THE FOUNDER'S ONE CLICK, DONE FOR HIM (the granted permission):
1. THE DUPE-CHECK (coordination beats collision): does a muse-PR already
   exist on rtk-ai/rtk? (the issue's author OFFERED one - if theirs landed,
   we DON'T open ours; we comment instead).
2. If clear: create the PR (the API POST, our token) - the body carries
   the DISCLOSURE + the coordination intent verbatim.
3. Report the PR's URL (the link for the founder)."""
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = "rtk-ai/rtk"
FORK_HEAD = "seahawk2986-hue:apex-fix"
sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
import PatchStep as PS

tok = PS.token()


def run():
    # 1. the dupe-check: the repo's open PRs mentioning muse
    st, prs = PS.api(f"/repos/{REPO}/pulls?state=open&per_page=50", tok)
    muse_prs = [p for p in (prs if st == 200 else [])
                if "muse" in (p.get("title", "") + (p.get("body") or "")).lower()]
    if muse_prs:
        print("[one-click] A MUSE PR ALREADY EXISTS - we do NOT collide:")
        for p in muse_prs[:3]:
            print("   ", p.get("html_url"))
        # the comment-instead: post the coordination comment on #4917
        body = ("Coordination-first (apex-ghost-family): we drafted the "
                "part-2 bundle material (plugin.json + hooks.json + the "
                "shell adapter) but saw a PR for this already in flight - "
                "our fork is ready at "
                "https://github.com/seahawk2986-hue/rtk/tree/apex-fix "
                "if the bundle helps your PR; happy to hand it to you.")
        st2, _ = PS.api(f"/repos/{REPO}/issues/4917/comments", tok,
                        method="POST")
        # the direct POST (the json body)
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/issues/4917/comments",
            data=json.dumps({"body": body}).encode(),
            headers={"Authorization": "Bearer " + tok,
                     "Accept": "application/vnd.github+json",
                     "User-Agent": "apex-one-click/1.0"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read().decode())
            print("[one-click] the coordination comment posted:",
                  d.get("html_url", "?"))
        except Exception as e:
            print(f"[one-click] the comment failed: {str(e)[:70]}")
        return None
    # 2. create OUR PR (the disclosed body)
    st3, created = api_create()
    if st3 in (201, 200):
        print("[one-click] THE PR IS LIVE:", created.get("html_url"))
        # the honest receipt into the ledger
        with open(os.path.join(ROOT, "Config", "AscentLedger.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "kind": "upward", "what": "PR-FILED-FOUNDERS-GRANTED",
                "url": created.get("html_url", "")}) + "\n")
        # the briefs lane
        try:
            pm = json.load(open(os.path.join(
                ROOT, "Config", "PathMemory.json"), encoding="utf-8-sig"))
            h = pm.setdefault("andrew_help", {})
            h["briefs"] = int(h.get("briefs", 0)) + 1
            h.setdefault("earn_briefs", []).append(
                {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "text": "PR filed (founder-granted): "
                         + created.get("html_url", "")})
            from SafeIO import write_json as wj
            wj(os.path.join(ROOT, "Config", "PathMemory.json"), pm)
        except Exception:
            pass
        return created.get("html_url")
    print(f"[one-click] the PR creation returned {st3}: "
          f"{str(created)[:160]}")
    return None


def api_create():
    body = ("Part 2 material for #4917 (the Agent Plugins 1.0.0 bundle: "
            "plugin.json + hooks/hooks.json + the Claude-shape adapter; "
            "the parity command stays with the issue author). "
            "**Automated draft by apex-ghost-family (disclosed); "
            "founder-verified.** Coordination-first: if a PR for #4917 is "
            "already in flight, ours here is offered as the bundle part, "
            "free to fold in.")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/pulls",
        data=json.dumps({"title": "feat(hooks): muse provider bundle "
                         "(Agent Plugins 1.0.0)",
                         "head": FORK_HEAD, "base": "main",
                         "body": body}).encode(),
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "apex-one-click/1.0"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except Exception as e:
        return (getattr(getattr(e, "fp", None), "code", 0) or 0,
                {"error": str(e)[:120]})


if __name__ == "__main__":
    run()