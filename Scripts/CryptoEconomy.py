"""Hybrid economy: EARN + USE — hard-capped at 80% of earnings.

RULE (ApexGuard-enforced): total spend across all lanes may never exceed
80% of what was earned (ledger-tracked). The 20% reserve never touches spend.
"""
import json
import os
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LEDGER = os.path.join(ROOT, "Config", "CryptoLedger.json")
GUARD = os.path.join(ROOT, "Scripts", "ApexGuard.py")


def load_L():
    try:
        return json.load(open(LEDGER, encoding="utf-8-sig"))
    except Exception:
        return {"earned": 0.0, "spent": 0.0, "rows": []}


def save_L(L):
    L["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    json.dump(L, open(LEDGER, "w", encoding="utf-8"), indent=1)


def earned(L):
    return float(L.get("earned", 0.0))


def spent(L):
    return float(L.get("spent", 0.0))


def budget_headroom(L, cap_pct=0.80):
    """The hard rule: spend cap = 80% of earned. Never crossed."""
    return max(0.0, earned(L) * cap_pct - spent(L))


def earn(amount, source, note=""):
    """The money lands AND THE FAMILY TELLS ANDREW - in the chat window (a
    conversation event the page displays), via voice, and in the status line."""
    L = load_L()
    L["earned"] = earned(L) + float(amount)
    L["rows"].append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "earn",
                      "amount": float(amount), "source": source, "note": note[:150]})
    save_L(L)
    amt = float(amount)
    headroom = budget_headroom(L)
    # 1. THE CHAT WINDOW: a real conversation event - the page shows it
    try:
        row = {"id": os.urandom(6).hex(), "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
               "kind": "conversation", "talk": True, "imp": 1.0,
               "text": f"MONEY LANDED: ${amt:.2f} from {source} -> paypal:thanchanok34@gmail.com - headroom after "
                       f"(80pct cap): ${headroom:.2f}",
               "meta": {"message": f"Just earned ${amt:.2f} for you, Andrew - "
                                    f"from {source}. The 80pct reserve: "
                                    f"${earned(L) * 0.2:.2f} untouched.",
                        "reply": f"Ledger: ${earned(L):.2f} earned total, "
                                 f"${spent(L):.2f} spent."}}
        with open(os.path.join(ROOT, "memory_episodic.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
    except Exception:
        pass
    # 2. THE VOICE: he hears it even away from the window
    try:
        import subprocess
        subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                          "-Command", "& 'C:\\Users\\seaha\\Downloads\\Apex-With-Triggers-Fixed\\Scripts\\ApexSpeak.ps1' -Text "
                          f"'Just earned {amt:.2f} dollars for you, Andrew'"],
                         creationflags=0x00000008)
    except Exception:
        pass
    return earned(L)


def propose_spend(amount, purpose):
    """The ONLY spending gate. Under the 80% cap -> approved; else refused.
    Apex never spends crypto without this approving AND the user having
    explicitly set APEX_ALLOWANCE_USDC (the master switch)."""
    allowance = float(os.getenv("APEX_ALLOWANCE_USDC", "0") or 0)
    if allowance <= 0:
        return {"approved": False,
                "reason": "master switch off (APEX_ALLOWANCE_USDC not set)"}
    L = load_L()
    room = budget_headroom(L)
    if amount > room:
        return {"approved": False,
                "reason": f"spend {amount:.2f} exceeds 80pc headroom {room:.2f} (earned {earned(L):.2f}, spent {spent(L):.2f})"}
    L["spent"] = spent(L) + float(amount)
    L["rows"].append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "spend",
                      "amount": float(amount), "purpose": purpose[:150],
                      "headroom_after": round(budget_headroom(L), 2)})
    save_L(L)
    return {"approved": True, "headroom_after": round(budget_headroom(L), 2)}


# ---- the EARN lane: bounty discovery (read-only, keyless) --------------------
import urllib.request
import re

UA = {"User-Agent": "ApexGhostSwarm/3.0", "Accept": "application/json"}


def credible(b):
    """CREDIBILITY FLOOR (spam-wave lesson, 2026-10-31): a bounty counts only
    if the repo passes: age >= 30d, forks <= 10x stars, description present.
    Scam signature confirmed live tonight: 0-star/144-fork/12-day accounts."""
    try:
        org, repo = b.get("org", ""), b.get("repo", "") or b.get("url", "")
        if "/" not in (org or repo):
            return False
        full = repo if "/" in repo else None
        if not full:
            return False
        req = urllib.request.Request(f"https://api.github.com/repos/{full}", headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.load(r)
        age_days = (time.time() - time.mktime(time.strptime(d["created_at"][:10], "%Y-%m-%d"))) / 86400
        stars, forks = int(d.get("stargazers_count", 0)), int(d.get("forks_count", 0))
        return (age_days >= 30 and (not stars or forks <= 10 * max(1, stars))
                and (d.get("description") or "") != "")
    except Exception:
        return False


def bounty_scan(n=10, tags=("python",)):
    """Algora-style open bounties: public listings -> the exact pipeline we
    already run (grade fit -> code in V2 engine -> user delivers)."""
    out = []
    try:
        tag = tags[int(time.time()) // 3600 % len(tags)]
        url = f"https://api.algora.io/api/v2/bounties?per_page={n}&tag={tag}&status=open"
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
        rows = data if isinstance(data, list) else data.get("bounties", [])
        for b0 in rows if isinstance(rows, list) else []:
            b = b0.get("bounty") or b0
            cand = {"id": str(b0.get("id") or b.get("id") or "")[:24],
                        "title": (b.get("title") or b0.get("title", ""))[:110],
                        "reward": b.get("amount", b0.get("amount", 0)),
                        "org": (b.get("partner") or {}).get("login", b0.get("org", ""))[:40],
                        "url": (b.get("partner") or {}).get("repository", "") or ""}
            if credible(cand):
                out.append(cand)
        return out
    except Exception:
        return out


def rung1_issue_lane(root=r"C:\\Users\\seaha\\Downloads\\Apex-With-Triggers-Fixed"):
    """The UNFAIR ADVANTAGE: bugs the SWARM discovered today in the tools we run
    (llama.cpp/LMStudio-class) become properly-filed issue drafts - the highest
    conversion-probability USDC lane, using knowledge we already earned."""
    import glob as _g
    issues = []
    try:
        for f in _g.glob(root + r"\\Logs\\*.log"):
            with open(f, encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    m = re.search(r"(HTTP 4\d\d|HTTPError.*4\d\d|timeout|ConnectionReset|404|chunked)", line)
                    if m and len(issues) < 8:
                        issues.append({"tool": "llama.cpp/LM Studio stack", "evidence": line[:160],
                                       "class": m.group(1)})
    except Exception:
        pass
    return issues


if __name__ == "__main__":
    L = load_L()
    print(f"LEDGER: earned {earned(L):.2f} | spent {spent(L):.2f} | "
          f"80pc headroom {budget_headroom(L):.2f}")
    bs = bounty_scan()
    print("open bounties discovered:", len(bs))
    for b0 in bs[:5]:
        print("  ", b0)
    # demonstrate the guard
    print("spend test 5.00:", propose_spend(5.00, "api credits test"))
    x = input("earn 10.00 test? (y/N) ") if False else "n"
    if x.strip().lower() == "y":
        earn(10.00, "test", "manual demo")
        print("earn applied; ledger now:", load_L())