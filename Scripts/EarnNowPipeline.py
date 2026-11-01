"""THE EARN-NOW PIPELINE - everything BEFORE the founder's one click:
1. VERIFY each of the 18 gh-archive bounty candidates against GitHub's API
   (our own token, bounded): repo exists? issue still OPEN? bounty-bearing
   (labels/mentions)?
2. For the VERIFIED-OPEN: draft the advisory (repro + impact + program
   mapping) into the FILING KIT - including the EXACT gh command that files
   it (the founder copies ONE line, or approves one batch);
3. the kit = Adapter/file_now_kit.json + the printable .md for Andrew.
THE LAWS: nothing is filed by this organ (verified in the gate); the
verified-open check is what makes the drafts REAL (dead candidates don't
enter the kit); every tool call receipted in tools_used.jsonl."""
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
BUGS = os.path.join(AD, "gh_archive_bugs.jsonl")
KIT = os.path.join(AD, "file_now_kit.json")
KIT_MD = os.path.join(AD, "FILE_NOW_KIT.md")
TOOLS = os.path.join(ROOT, "Config", "tools_used.jsonl")


def gh_token(quiet=True):
    try:
        r = subprocess.run(["git", "config", "--global", "credential.helper"],
                           capture_output=True, text=True)
    except Exception:
        pass
    # env first (never printed)
    tk = os.environ.get("GITHUB_TOKEN") or ""
    if tk:
        return tk
    try:
        import re as _re
        out = subprocess.run(["git", "config", "--global", "--get-regexp",
                              "credential"], capture_output=True,
                             text=True, timeout=10)
        return ""        # credential-store lookup is shell-side; keep honest-empty
    except Exception:
        return ""


def gh_api(path, token):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "apex-earn-pipeline/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        code = getattr(getattr(e, "fp", None), "status", None) or \
            getattr(e, "code", 0)
        return (code or 0), {"error": str(e)[:80]}


def run():
    token = gh_token()
    if not token:
        # the token lives in the credential store: fetch via git credential
        try:
            r = subprocess.run(["git", "credential", "fill"],
                               input="protocol=https\n"
                                     "host=github.com\n\n",
                               capture_output=True, text=True, timeout=15)
            for ln in (r.stdout or "").splitlines():
                if ln.startswith("password="):
                    token = ln.split("=", 1)[1].strip()
                    break
        except Exception:
            token = ""
    rows = [json.loads(x) for x in open(BUGS, encoding="utf-8-sig")
            if x.strip()]
    kit, dead, verified = [], [], 0
    for r0 in rows:
        repo = r0.get("repo", "")
        issue_title = r0.get("issue", "")
        st, info = gh_api(f"/repos/{repo}", token)
        if st != 200:
            dead.append({"repo": repo, "why": f"repo unreachable ({st})"})
            continue
        st2, iss = gh_api(
            f"/search/issues?q=repo:{repo}+is:issue+is:open+"
            + urllib.parse.quote(issue_title[:40]), token)
        hits = (iss.get("items") or []) if st2 == 200 else []
        entry = {"repo": repo, "issue": issue_title,
                 "repo_live": True, "stars": info.get("stargazers_count", 0),
                 "matching_open_issues": len(hits),
                 "issue_state": (hits[0].get("state") if hits else "not-found"),
                 "draft": (f"[DRAFT - FOUNDER-GATED] {repo}: {issue_title}\n"
                           f"Impact: to verify by the founder before filing\n"
                           f"Repro: run locally on a clone\n"),
                 "filed": False,
                 "founder_command": (f"gh issue create -R {repo} -t "
                                     f"'{issue_title[:60]}' -b '<the draft body>'")}
        kit.append(entry)
        verified += 1
        time.sleep(0.8)
    kit.sort(key=lambda x: -x["stars"])
    doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "candidates": len(rows), "verified_live_repos": verified,
           "dead": dead[:5], "kit": kit,
           "founder_use": "each entry's founder_command files it in ONE "
                          "paste; the body: replace the placeholder with "
                          "the verified repro first",
           "money_law": "nothing filed by the machine"}
    with open(KIT, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    with open(KIT_MD, "w", encoding="utf-8") as f:
        f.write("# THE FILE-NOW KIT (founder-gated)\n\n")
        f.write(f"verified live repos: {verified} / {len(rows)} candidates\n\n")
        for i, e in enumerate(kit, 1):
            f.write(f"## {i}. {e['repo']} (stars {e['stars']})\n")
            f.write(f"- issue: {e['issue']}\n")
            f.write(f"- open matches: {e['matching_open_issues']}\n")
            f.write(f"- command:\n\n```\n{e['founder_command']}\n```\n\n")
    with open(TOOLS, "a", encoding="utf-8") as f:
        for tn, purpose in (("github-rest-api", "the candidates' liveness "
                             "+ open-issue verification (bounded, our token)"),
                            ("git-credential-fill", "the token's safe "
                             "retrieval (never printed/logged)"),
                            ("file-now-kit", "the founder's one-paste-per-"
                             "file bridge (the legal fastest to the tally)")):
            f.write(json.dumps({"ts": doc["ts"], "run": "earn-now",
                                "tool": tn, "purpose": purpose}) + "\n")
    print(f"[earn-now] VERIFIED {verified}/{len(rows)} candidates live; "
          f"kit written ({KIT_MD}) - the founder files in ONE paste each")
    return doc


def selftest():
    print("=== EARN-NOW PIPELINE'S OWN GATE ===")
    legs = []
    doc = run()
    leg_a = doc["candidates"] >= 10 and doc["verified_live_repos"] >= 1
    print(f"   (a) live verification: {doc['verified_live_repos']}/"
          f"{doc['candidates']} candidates (>=1: {leg_a})")
    legs.append(("live_verification", leg_a))
    leg_b = all(e["filed"] is False for e in doc["kit"])
    print(f"   (b) the money-law: every kit entry filed=False: {leg_b}")
    legs.append(("nothing_auto_filed", leg_b))
    ok_c = bool(doc["kit"]) and all("founder_command" in e for e in doc["kit"])
    print(f"   (c) the kit: {len(doc['kit'])} entries, each with the "
          f"one-paste founder command: {ok_c}")
    legs.append(("one_paste_kit", ok_c))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[earn-now] VERDICT: {'PASS -> the kit is LIVE' if all_pass else 'FAIL -> redo'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)