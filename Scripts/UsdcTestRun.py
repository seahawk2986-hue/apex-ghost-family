"""THE HONEST USDC TEST RUN: the swarm attempts real earnings; the ledger
reports exactly what happened - $0.00 if that is the truth (REPORT-HONESTY)."""
import json
import os
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LEDGER = ROOT + r"\Config\CryptoLedger.json"
UA = {"User-Agent": "ApexGhostSwarm/3.0", "Accept": "application/vnd.github+json"}


def load_L():
    try:
        return json.load(open(LEDGER, encoding="utf-8-sig"))
    except Exception:
        return {"earned": 0.0, "spent": 0.0, "rows": []}


def gh_bounty_lanes(n=10):
    """Keyless bounty discovery: GitHub issues labeled as bounties+rewards on
    public repos - the ONE officially-documented keyless earn lane."""
    out = []
    k = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")
    headers = dict(UA)
    if k:
        headers["Authorization"] = f"Bearer {k}"
    queries = ('label:bounty state:open', 'reward+money label:good-first-issue state:open',
               '"$ bounty" state:open type:issue')
    for q in queries:
        try:
            url = ("https://api.github.com/search/issues?q=" +
                   urllib.request.quote(q) + f"&per_page={n}")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.load(r)
            for it in data.get("items", []):
                out.append({"title": (it.get("title") or "")[:110],
                            "reward_hint": it.get("labels") and
                            ",".join(l.get("name", "") for l in it.get("labels", []))[:60],
                            "repo": it.get("repository_url", "").split("repos/")[-1],
                            "url": it.get("html_url", "")})
            if len(out) >= n:
                break
        except Exception:
            continue
    return out[:n]


def algora_scan(n=10):
    """Algora: client-rendered + closed API (404/406 verified twice tonight)
    -> FAIL-CLOSED: returns [] without forcing their service."""
    return []


# ---- THE TEST RUN ----
print("=== APEX SWARM USDC TEST RUN ===")
print("phase 1: earn lanes scan (all keyless sources, fail-closed)")
found = gh_bounty_lanes()
algora = algora_scan()
print(f"  github bounty-labeled issues found: {len(found)}")
print(f"  algora: {len(algora)} (fail-closed: client-rendered API, verified)")

L = load_L()
print(f"phase 2: ledger state: earned ${L.get('earned', 0):.2f} | spent ${L.get('spent', 0):.2f}")
print("phase 3: conversion paths to USDC:")
print("  - bounties need: accepted merged PR (V2 engine drafts; human submits)")
print("  - payment needs: wallet/account (user custody step - never Apex)")
print("  - master switch: APEX_ALLOWANCE_USDC =", os.getenv("APEX_ALLOWANCE_USDC", "not set"))

print("phase 4: HONEST RESULT")
if found and int(os.getenv("APEX_ALLOWANCE_USDC", "0") or 0) > 0 and False:
    pass  # real payment rails do not exist yet - nothing to credit
print(f"  USDC earned this test run: $0.00")
print(f"  reason: {len(found)} open bounty issues discovered; "
      f"0 payable - payment rails require your wallet + account setup")
# record it honestly in the ledger
L.setdefault("rows", []).append({
    "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "test_run",
    "earned": 0.0, "bounties_found": len(found),
    "note": "keyless earn scan; conversion rails await custody setup"})
json.dump(L, open(LEDGER, "w", encoding="utf-8"), indent=1)
print("  ledger: test run recorded honestly")

if found:
    print("phase 5: next step to NONZERO - the discovered bounties:")
    for b0 in found[:5]:
        print("   -", b0["title"][:70], "| repo:", b0["repo"])
else:
    print("phase 5: no keyless bounty source reachable this run "
          "(search quota + closed platforms) - GITHUB_TOKEN in .env = 80x quota lane")
print("=== END: yield $0.00 (the honest number the evidence supports) ===")