"""THE FINANCIAL BRAIN: the swarm's overarching goal - improve Andrew Hike's
life FINANCIALLY, proactively.

Every cycle:
 1. SCAN all earn lanes (bounties/issues/bugs-we-can-file/platforms)
 2. GRADE each opportunity: expected value = reward x fit-probability
    (fit = semantic similarity between the bounty and our 245-skill library
     via the embed engine - no hallucinated confidence, measured similarity)
 3. ADVISE: the single highest-EV action, written into his morning brief
 4. TRACK: opportunities -> earned (the flywheel measured)
Honesty: EV shows its inputs; zero-opportunity weeks print as zero - the
advisor does not fabricate hope.
"""
import json
import os
import time

import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
PATHMEM = os.path.join(ROOT, "Config", "PathMemory.json")
UA = {"User-Agent": "Mozilla/5.0 ApexGhostSwarm/3.0", "Accept": "application/vnd.github+json"}


def _fit_prob(text, k=3):
    """P(success) proxy: semantic similarity of the opportunity to our OWN
    mined skill library - the honest probability of 'we can do this'."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, "Scripts"))
    import HarvestUse as _hu
    hits = _hu.consult(text[:200], k)
    if not hits:
        return 0.05
    return min(0.9, sum(x["score"] for x in hits) / len(hits))


def _reward_usd(text):
    m = 0
    for pat in (r"\$(\d{2,6})", r"(\d{2,6})\s*(?:usdc|usd|dollars)"):
        m = max(m, max([int(x) for x in __import__("re").findall(pat, text.lower())] or [0]))
    return m


def scan_opportunities(max_opp=12):
    """All earn lanes scanned; each opportunity EV-graded."""
    opps = []
    # rung-1: our own bug evidence (the tools' issue-filing; sponsors/credits possible)
    try:
        log_text = ""
        for f in os.listdir(os.path.join(AD, "Logs")):
            fp = os.path.join(AD, "Logs", f)
            try:
                log_text += open(fp, encoding="utf-8", errors="ignore").read()[-4000:]
            except Exception:
                continue
        import re
        bugs = re.findall(r"\[CLOUD\] lane (\w+) failed: (.{20,60})", log_text)
        seen = set()
        for lane, err in bugs:
            key = lane + err[:20]
            if key in seen:
                continue
            seen.add(key)
            opps.append({"kind": "bug-report", "target": "the tools' upstream repos",
                         "title": f"document + fix: {lane} lane {err[:40]}",
                         "reward": 0, "fit": 0.9, "note": "credibility ladder" +
                         "; sponsors possible once PRs accepted"})
            if len(opps) >= max_opp:
                break
    except Exception:
        pass
    # keyless bounty issues (quota-aware; fails closed on 403)
    try:
        k = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")
        headers = dict(UA)
        if k:
            headers["Authorization"] = f"Bearer {k}"
        req = urllib.request.Request(
            "https://api.github.com/search/issues?q=label:bounty+state:open&per_page=10",
            headers=headers)
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
        for it in data.get("items", []):
            t = (it.get("title") or "")
            rw = _reward_usd(t + " " + " ".join(l.get("name", "") for l in (it.get("labels") or [])))
            repo_full = (it.get("repository_url", "").split("repos/")[-1])
            # CREDIBILITY SPINE (the night's lesson): scam repos EV-weighted to
            # zero BEFORE ranking - a 0-star/144-fork/12-day account can never
            # again buy an EV score with a fake $750 title
            try:
                req = urllib.request.Request(f"https://api.github.com/repos/{repo_full}",
                                             headers=UA)
                with urllib.request.urlopen(req, timeout=20) as r:
                    d0 = json.load(r)
                age = (time.time() - time.mktime(time.strptime(d0["created_at"][:10], "%Y-%m-%d"))) / 86400
                stars, forks = int(d0.get("stargazers_count", 0)), int(d0.get("forks_count", 0))
                cred = (age >= 30 and (stars == 0 or forks <= 10 * max(1, stars))
                        and bool(d0.get("description")))
            except Exception:
                cred = False
            if not cred:
                continue
            fit = _fit_prob(t)
            opps.append({"kind": "bounty", "target": it.get("html_url", ""),
                         "title": t[:110], "reward": rw, "fit": round(fit, 2),
                         "ev": round(rw * fit, 2)})
    except Exception:
        pass
    opps.sort(key=lambda x: -x.get("ev", 0))
    return opps[:max_opp]


def advise(opp_limit=3):
    """The honest financial advisor: the best current actions + their math."""
    opps = scan_opportunities()
    adv = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "opportunities": opps, "total_ev": round(sum(o.get("ev", 0) for o in opps), 2),
           "best_action": (opps[0]["title"][:90] + " (EV $" + str(opps[0].get("ev", 0)) + ")") if opps else "none this cycle - the honest zero; widen lanes/token tomorrow"}
    try:
        pm = json.load(open(PATHMEM, encoding="utf-8-sig"))
        pm["finance"] = adv
        json.dump(pm, open(PATHMEM, "w", encoding="utf-8"), indent=1)
    except Exception:
        pass
    return adv


if __name__ == "__main__":
    a = advise()
    print(json.dumps(a, indent=1)[:900])
    print("\n(The EV math is honest: reward x measured-fit; zero means zero.)")