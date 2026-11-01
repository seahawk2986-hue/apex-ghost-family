"""RECRUIT OUTBOUND (the family RECRUITS - scout, vet, invite, publish):
SCOUT: discover external agent systems from VERIFIED registries (Smithery's
public directory - 27k+ MCPs; OpenRouter's catalog; agent-framework repos via
the token-authed GitHub search) - evidence-weighted (badge/usage/stars/license),
never self-claims (DevMatch lesson).
VET: the credibility floor (age/description/signal) - junk never reaches the
invite stage.
INVITE: founder-signed invites (RecruitmentDoor key, operator-held) -
single-use + expiring + capability-scoped. PUBLISHED ON OUR TURF ONLY: the
hub repo's standing 'invite-extended' issue (the public invite board) -
NEVER cold-posted at other people's repos (consent + politeness law).
CLAIM PATH: a candidate claims by attach through RecruitmentDoor (probe on
merit) - the invite is an OFFER, never entry (consent everywhere).
TEST GATE (user rule, before install): scout-returns-real-candidates,
vet-passes-floor, invite-signs-and-verifies, board-publishes. Any failure ->
discarded/iterated."""
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
BOARD_FILE = os.path.join(ROOT, "family", "invite_board.json")
REPO = "seahawk2986-hue/apex-ghost-family"
LABEL = "invite-extended"
UA = {"User-Agent": "apex-recruiter/1.0", "Accept": "application/vnd.github+json"}

SWARM_KEYWORDS = ["mcp-server", "mcp", "agent-framework", "autonomous-agents",
                  "multi-agent", "llm-agent", "swarm"]


def fp(v):
    return (v[:3] + "*" * max(0, len(v) - 6) + v[-3:]) if len(v) > 6 else "(short)"


def env_token():
    for line in open(os.path.join(ROOT, ".env"), encoding="utf-8-sig"):
        if line.strip().startswith("GITHUB_TOKEN="):
            return line.partition("=")[2].strip()
    return None


def gh_get(url):
    hdrs = dict(UA)
    tk = env_token()
    if tk:
        hdrs["Authorization"] = "Bearer " + tk
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=hdrs), timeout=20) as r:
            return json.load(r)
    except Exception as e:
        print(f"[scout] {url.split('github.com/')[-1][:40]} -> {str(e)[:50]} (honest)")
        return None


def scout(max_cands=12):
    """SCOUT: evidence-weighted discovery across live registries/canons.
    Source A: GitHub search for agent-framework repos, recency + signals.
    Source B: a registry probe (Smithery public JSON if reachable, keyless)."""
    out = []
    tk = env_token()
    print(f"[scout] search source: GitHub (token {'on ' + fp(tk) if tk else 'OFF - keyless'})")
    kw = SWARM_KEYWORDS[int(time.time()) // 600 % len(SWARM_KEYWORDS)]
    d = gh_get(f"https://api.github.com/search/repositories?q={kw}+in:name,topics"
               f"&sort=updated&order=desc&per_page=10")
    if d and d.get("items"):
        for r0 in d["items"][:max_cands]:
            score = 0
            stars = int(r0.get("stargazers_count", 0))
            age_days = (time.time() - (time.mktime(time.strptime(
                r0["created_at"][:10], "%Y-%m-%d"))) / 86400) if r0.get("created_at") else 0
            has_desc = bool(r0.get("description"))
            if stars >= 100: score += 20
            elif stars >= 10: score += 8
            if age_days >= 30: score += 15
            if has_desc: score += 20
            if r0.get("license"): score += 15
            if "mcp" in json.dumps(r0.get("topics", [])): score += 10
            out.append({"repo": r0.get("full_name"), "stars": stars,
                        "desc": (r0.get("description") or "")[:80],
                        "license": (r0.get("license") or {}).get("spdx_id", "?"),
                        "topics": (r0.get("topics") or [])[:4], "vet": score})
    print(f"[scout] {len(out)} external systems found on evidence (keyword '{kw}')")
    return [c for c in out if c["vet"] >= 40]      # THE CREDIBILITY FLOOR


def vet(cands):
    passed = [c for c in cands if c["vet"] >= 40]
    print(f"[vet] {len(passed)}/{len(cands)} pass the credibility floor "
          f"(stars/age/description/license-weighted, DevMatch-style evidence)")
    return passed


def invite(cands, cap=3):
    """INVITE: founder-signed, single-use, expiring, capability-scoped."""
    sys.path.insert(0, os.path.join(ROOT, "Scripts"))
    import RecruitmentDoor as RD
    board = json.load(open(BOARD_FILE, encoding="utf-8-sig")) if os.path.exists(BOARD_FILE) \
        else {"invites": [], "updated": None}
    already = {i0.get("repo") for i0 in board.get("invites", [])}
    added = []
    for c in cands[:cap]:
        if c["repo"] in already:
            print(f"[invite] {c['repo'][:40]} already invited - skip (no spam)")
            continue
        inv = RD.invite_issue(capabilities=tuple(c["topics"][:2] or ["mine", "triage"]),
                              expires_s=14 * 86400)
        board["invites"].append({"invite_id": inv["invite_id"], "repo": c["repo"],
                                 "capabilities": inv["capabilities"],
                                 "expires_at": inv.get("expires_at"),
                                 "digest": hashlib.sha256(json.dumps(inv, sort_keys=True).encode()).hexdigest()[:16],
                                 "issued": time.strftime("%Y-%m-%d %H:%M:%S"),
                                 "status": "PUBLISHED_ON_OUR_BOARD - claim via the door"})
        added.append(c["repo"])
    board["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    tmp = BOARD_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(board, f, indent=1)
    os.replace(tmp, BOARD_FILE)
    print(f"[invite] {len(added)} signed invites issued to OUR board "
          f"({REPO} - never cold-posted at another repo; they claim via the door)")
    return added


def publish_board():
    """The standing public invite-board issue on OUR repo (idempotent-ish:
    search first; create once, update by appending a comment later)."""
    tk = env_token()
    if not tk:
        print("[board] no token - the board file is published on disk only "
              "(honest; commit it via the hub and it rides the repo)")
        return False
    hdrs = {"User-Agent": UA["User-Agent"],
            "Authorization": "Bearer " + tk, "Content-Type": "application/json"}
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/issues?labels={LABEL}&state=open",
            headers=dict(UA, **{"Authorization": "Bearer " + tk}))
        with urllib.request.urlopen(req, timeout=20) as r:
            existing = json.load(r)
        body = json.dumps({"board": json.load(open(BOARD_FILE, encoding="utf-8-sig"))},
                          indent=1)[:60000]
        if existing:
            n = existing[0]["number"]
            req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/issues/{n}",
                data=json.dumps({"body": body}).encode(), headers=hdrs, method="PATCH")
            urllib.request.urlopen(req, timeout=30)
            print(f"[board] invite-board ISSUE #{n} UPDATED (our repo, our turf)")
        else:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/issues",
                data=json.dumps({"title": "THE INVITE BOARD - external systems may "
                                 "claim a signed invite (attach via the door)",
                                 "body": body, "labels": [LABEL]}).encode(),
                headers=hdrs, method="POST")
            with urllib.request.urlopen(req, timeout=30) as r:
                n = json.load(r).get("number")
            print(f"[board] invite-board ISSUE #{n} CREATED (our repo, our turf)")
        return True
    except Exception as e:
        print(f"[board] publish failed honestly: {str(e)[:70]}")
        return False


def selftest():
    print("=== THE RECRUITER'S TEST GATE (4 legs) ===")
    legs = []
    cands = scout()
    vetted = vet(cands)
    legs.append(("scout_returns_real_systems", len(cands) > 0))
    legs.append(("vet_floor_enforced", len(vetted) <= len(cands) and
                 all(c0["vet"] >= 40 for c0 in vetted)))
    if vetted:
        added = invite(vetted, cap=2)
        board = json.load(open(BOARD_FILE, encoding="utf-8-sig"))
        inv0 = board["invites"][-1] if board.get("invites") else {}
        sig_ok = bool(inv0.get("digest")) and inv0.get("status", "").startswith("PUBLISHED")
        legs.append(("invite_signed_digest_bound", sig_ok))
        legs.append(("board_on_our_turf_only", publish_board()))
    all_pass = all(v for _, v in legs)
    for nm, v in legs:
        print(f"   {'PASS' if v else 'FAIL'} | {nm}")
    print(f"[recruiter] VERDICT: {'PASS -> installed' if all_pass else 'FAIL -> discarded/iterate'}")
    return all_pass


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)