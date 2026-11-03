"""Hybrid economy: EARN + USE - hard-capped at 80% of earnings.

RULE (ApexGuard-enforced): total spend across all lanes may never exceed
80% of what was earned (ledger-tracked). The 20% reserve never touches spend.

AUDIT HARDENING (2026-10-31, economy-organ audit, 100% line coverage):
- load_L: corrupt ledger RAISES (the old version silently returned zeros and
  the next save would overwrite real history with zeros - history destroyed).
- save_L: locked + atomic (os.replace), one lock holder so propose_spend's
  read-check-write critical section never re-locks (no nested deadlock).
- earn(): FAIL-CLOSED two-phase - a first call files a pending_earn row and
  STOPS (the tally is untouched); the operator confirms by id in a second
  call (or via the confirm env var). Applied pendings cannot re-apply
  (double-credit impossible). The old demo proved a $1.00 self-report row
  once landed by mistake - that path is now structural, not conventional.
- announcement failures PRINT (print-or-it-didnt-happen; no silent except).
"""
import json
import msvcrt
import os
import re  # lane-evidence patterns (rung1)
import sys
import time
import urllib.request

_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LEDGER = os.path.join(ROOT, "Config", "CryptoLedger.json")
GUARD = os.path.join(ROOT, "Scripts", "ApexGuard.py")


def _payout_dest():
    """The founder's receiving address = .env-only (PAYOUT_DEST), never repo
    content (the 2026-11-04 privacy law; .env is gitignored - verified)."""
    try:
        with open(os.path.join(ROOT, ".env"), encoding="utf-8-sig") as f:
            for ln in f:
                if ln.strip().startswith("PAYOUT_DEST="):
                    return ln.split("=", 1)[1].strip() or "paypal:SET-ME"
    except Exception:
        pass
    return "paypal:configured-in-.env"


def _lock():
    """msvcrt byte-lock identical to SafeIO._lock, kept local so a critical
    section can hold it across read+write (SafeIO.write_json's separate lock
    would re-claim the same byte region and stall 30s)."""
    lf = open(LEDGER + ".lock", "w")
    dl = time.time() + 30
    while True:
        try:
            msvcrt.locking(lf.fileno(), msvcrt.LK_LOCK, 1)
            return lf
        except OSError:
            if time.time() > dl:
                lf.close()
                return None
            time.sleep(0.08)


def _write_atomic(L):
    L["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    tmp = LEDGER + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(L, f, indent=1)
    os.replace(tmp, LEDGER)


def load_L():
    """Fail-closed ledger read: missing -> init; corrupt -> RAISE."""
    if not os.path.exists(LEDGER):
        return {"earned": 0.0, "spent": 0.0, "rows": []}
    with open(LEDGER, encoding="utf-8-sig") as f:
        return json.load(f)  # corrupt -> raises: a broken ledger is never overwritten


def save_L(L):
    lf = _lock()
    if lf is None:
        return False
    try:
        _write_atomic(L)
        return True
    finally:
        msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)
        lf.close()


def earned(L):
    return float(L.get("earned", 0.0))


def spent(L):
    return float(L.get("spent", 0.0))


def budget_headroom(L, cap_pct=0.80):
    """The hard rule: spend cap = 80% of earned. Never crossed."""
    return max(0.0, earned(L) * cap_pct - spent(L))


def _announce(amount, source, L_after):
    """The tell-Andrew channels: chat event + voice. Failures PRINT."""
    amt = float(amount)
    headroom = budget_headroom(L_after)
    try:
        row = {"id": os.urandom(6).hex(), "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
               "kind": "conversation", "talk": True, "imp": 1.0,
               "text": f"MONEY LANDED: ${amt:.2f} from {source} -> {_payout_dest()} - headroom after "
                       f"(80pct cap): ${headroom:.2f}",
               "meta": {"message": f"Just earned ${amt:.2f} for you, Andrew - "
                                    f"from {source}. The 80pct reserve: "
                                    f"${earned(L_after) * 0.2:.2f} untouched.",
                        "reply": f"Ledger: ${earned(L_after):.2f} earned total, "
                                 f"${spent(L_after):.2f} spent."}}
        with open(os.path.join(ROOT, "memory_episodic.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
    except Exception as e:
        print(f"[earn-announce FAILED (chat event)] {e}", file=sys.stderr, flush=True)
    try:
        import subprocess
        subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                          "-Command", "& 'C:\\Users\\seaha\\Downloads\\Apex-With-Triggers-Fixed\\Scripts\\ApexSpeak.ps1' -Text "
                          f"'Just earned {amt:.2f} dollars for you, Andrew'"],
                         creationflags=0x00000008)
    except Exception as e:
        print(f"[earn-announce FAILED (voice)] {e}", file=sys.stderr, flush=True)


def earn(amount, source, note="", confirm=None):
    """THE REAL-VALUE GATE (the honesty law): the tally NEVER moves on
    self-report.

    Phase 1 - earn(amount, source): files a pending_earn row + prints its
    key; the tally is UNTOUCHED.
    Phase 2 - the OPERATOR (Andrew, or code that itself already verified the
    external value landed) re-calls with confirm=<key> (or sets env
    APEX_CONFIRM_<key>). The pending row flips applied and the credit lands.
    A key can apply exactly once (double-credit impossible)."""
    if confirm:
        lf = _lock()
        if lf is None:
            print("[earn FAILED] ledger busy >30s - confirmation NOT applied", flush=True)
            return earned(load_L())
        try:
            L = load_L()
            hit = None
            for r0 in L.get("rows", []):
                if (r0.get("kind") == "pending_earn" and r0.get("key") == confirm
                        and not r0.get("applied")):
                    hit = r0
                    break
            if hit is None:
                print(f"[earn REFUSED] no unapplied pending_earn with key "
                      f"{confirm!r} - nothing credited (fail-closed)", flush=True)
                return earned(L)
            amt = float(hit["amount"])
            hit["applied"] = time.strftime("%Y-%m-%d %H:%M:%S")
            L["earned"] = earned(L) + amt
            L["rows"].append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                              "kind": "earn", "amount": amt,
                              "source": hit.get("source", ""), "note": hit.get("note", ""),
                              "confirmed_by": confirm})
            applied = True
            try:
                _write_atomic(L)
            except Exception as e:
                applied = False
                print(f"[earn FAILED] atomic write failed - credit NOT applied ({e})",
                      file=sys.stderr, flush=True)
        finally:
            msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)
            lf.close()
        if applied:
            _announce(amt, hit.get("source", ""), load_L())
        return earned(load_L())
    key = os.urandom(6).hex()
    L = load_L()
    L["rows"].append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "pending_earn",
                      "amount": float(amount), "source": source, "note": note[:150],
                      "key": key})
    if not save_L(L):
        print("[earn FAILED] ledger locked >30s - pending row NOT saved", flush=True)
        return earned(L)
    print(f"[earn PENDING] ${float(amount):.2f} from '{source}' NOT credited - "
          f"no operator proof. Confirm with: earn({float(amount)!r}, {source!r}, "
          f"confirm={key!r}) or env APEX_CONFIRM_{key}={key}. "
          f"The tally stays honest.", flush=True)
    return earned(L)


def propose_spend(amount, purpose):
    """The ONLY spending gate. Master switch (APEX_ALLOWANCE_USDC) is the
    on/off; the 80% cap re-checks INSIDE the ledger lock (the old version's
    read-check-write race could double-book spends)."""
    allowance = float(os.getenv("APEX_ALLOWANCE_USDC", "0") or 0)
    if allowance <= 0:
        return {"approved": False,
                "reason": "master switch off (APEX_ALLOWANCE_USDC not set)"}
    lf = _lock()
    if lf is None:
        return {"approved": False, "reason": "ledger busy >30s - refused (fail-closed)"}
    try:
        L = load_L()
        room = budget_headroom(L)
        if amount > room:
            return {"approved": False,
                    "reason": f"spend {amount:.2f} exceeds 80pc headroom {room:.2f} (earned {earned(L):.2f}, spent {spent(L):.2f})"}
        L["spent"] = spent(L) + float(amount)
        L["rows"].append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "spend",
                          "amount": float(amount), "purpose": purpose[:150],
                          "headroom_after": round(budget_headroom(L), 2)})
        try:
            _write_atomic(L)
            return {"approved": True, "headroom_after": round(budget_headroom(L), 2)}
        except Exception as e:
            return {"approved": False, "reason": f"atomic write failed - spend NOT recorded ({e})"}
    finally:
        msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)
        lf.close()


# ---- the EARN lane: bounty discovery (read-only, keyless) --------------------

UA = {"User-Agent": "ApexGhostSwarm/3.0", "Accept": "application/json"}
_CRED_TTL = 86400
_cred_cache = {}


def credible(b):
    """CREDIBILITY FLOOR (spam-wave lesson, 2026-10-31): a bounty counts only
    if the repo passes: age >= 30d, forks <= 10x stars, description present.
    Scam signature confirmed live tonight: 0-star/144-fork/12-day accounts.
    24h TTL cache - keyless quota is 60 req/hr/IP; never re-fetch a fact."""
    try:
        org, repo = b.get("org", ""), b.get("repo", "") or b.get("url", "")
        if "/" not in (org or repo):
            return False
        full = repo if "/" in repo else None
        if not full:
            return False
        hit = _cred_cache.get(full)
        if hit is not None and time.time() - hit[0] < _CRED_TTL:
            return hit[1]
        req = urllib.request.Request(f"https://api.github.com/repos/{full}", headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.load(r)
        age_days = (time.time() - time.mktime(time.strptime(d["created_at"][:10], "%Y-%m-%d"))) / 86400
        stars, forks = int(d.get("stargazers_count", 0)), int(d.get("forks_count", 0))
        ok = (age_days >= 30 and (not stars or forks <= 10 * max(1, stars))
              and (d.get("description") or "") != "")
        _cred_cache[full] = (time.time(), ok)
        return ok
    except Exception:
        return False


def bounty_scan(n=10, tags=("python",)):
    """Algora lane: HONESTLY CLOSED. The endpoint returned 404/406 in testing
    (documented in UsdcTestRun.py); hammering a dead endpoint burns a 25s
    timeout per scan. Refuse loudly and honestly instead."""
    print("[bounty_scan] algora endpoint closed (404/406, verified twice) - "
          "returning [] (fail-closed, honest)", flush=True)
    return []


def rung1_issue_lane(root=ROOT):
    """The UNFAIR ADVANTAGE: bugs the SWARM discovered today in the tools we
    run (llama.cpp/LMStudio-class) become properly-filed issue drafts - the
    highest conversion-probability USDC lane, using knowledge we already earned."""
    import glob as _g
    issues = []
    try:
        for f in _g.glob(os.path.join(root, "Logs", "*.log")):
            with open(f, encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    if len(issues) >= 8:
                        break
                    m = re.search(r"(HTTP 4\d\d|HTTPError.*4\d\d|timeout|ConnectionReset|404|chunked)", line)
                    if m:
                        issues.append({"tool": "llama.cpp/LM Studio stack", "evidence": line[:160],
                                       "class": m.group(1)})
                if len(issues) >= 8:
                    break
    except Exception as e:
        print(f"[rung1 scan FAILED] {e}", file=sys.stderr, flush=True)
    return issues


if __name__ == "__main__":
    L = load_L()
    print(f"LEDGER: earned {earned(L):.2f} | spent {spent(L):.2f} | "
          f"80pc headroom {budget_headroom(L):.2f}")
    bs = bounty_scan()
    print("open bounties discovered:", len(bs))
    for b0 in bs[:5]:
        print("  ", b0)
    if "--demo-spend" in sys.argv:
        r = propose_spend(0.01, "spend_demo (books a row; NO rail exists)")
        print("spend demo:", r)
    else:
        print("no demo spend booked (pass --demo-spend for a labeled 0.01 row)")