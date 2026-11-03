"""THE OUTCOME YARDSTICK (2026-11-04) - internal activity vs EXTERNAL value.

THE WEAKNESS IT KILLS: all the ledgers can be green while nothing outside
the machine moved. The yardstick publishes BOTH columns on the same page
(/receipts), so "smooth" can never masquerade as "progress".

INTERNAL (counted from the family's own ledgers - real, local):
  drills_30d            GI-gym calibration rows in the last 30 days
  evolution_writes_30d  landed evolution/heal writes in the last 30 days
  chat_turns_30d        customer/owner chat turns in the last 30 days

EXTERNAL (only what a stranger could confirm):
  prs_merged       merged GitHub PRs authored by the founder's account
                   (GitHub REST search: type:pr author:<user> is:merged,
                   token = .env GITHUB_TOKEN, read-only, UA-honest)
  sales            completed Polar orders (api.polar.sh /v1/orders/ with the
                   .env POLAR_OAT; endpoint per PolarAgent.py's own session;
                   an auth shape change = an HONEST 0 + reason, never invented)
  funnel_arrivals  the funnel's arrival log (Apex-Adapter/Logs/funnel_arrivals.log)

$0 API reads only; stdlib + requests; a total failure writes zero-counts
WITH the failure reason (print-first honesty). Wired nightly by ApexDream.
"""
import io
import json
import os
import sys
import time
from datetime import datetime, timedelta

if getattr(sys.stdout, "apex_wrapped", False) is False:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stdout.apex_wrapped = True   # one process, one wrapper (double-wrap
                                     # = the GC closes the shared buffer)

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
OUT = os.path.join(REPO, "Config", "outcomes.json")
EPISODIC = os.path.join(REPO, "memory_episodic.jsonl")

import CloudBrain  # noqa: E402
K = CloudBrain.env_keys()


def _env(k):
    return K.get(k) or ""


def _internal_counts(since):
    drills = chat = 0
    try:
        with open(EPISODIC, encoding="utf-8") as f:
            for ln in f:
                if "GI gym" in ln and ("HIT" in ln or "MISS" in ln):
                    if _row_recent(ln, since) or _row_recent_slow(ln, since):
                        drills += 1
                    continue
                if '"kind": "conversation"' in ln:
                    if _row_recent(ln, since):
                        chat += 1
    except FileNotFoundError:
        pass
    writes = 0
    try:
        tel = os.path.join(REPO, "Logs", "reward_telemetry.jsonl")
        if os.path.isfile(tel):
            for ln in open(tel, encoding="utf-8"):
                if _row_recent(ln, since):
                    writes += 1
    except FileNotFoundError:
        pass
    return {"drills_30d": drills,
            "evolution_writes_30d": writes,
            "chat_turns_30d": chat}


def _row_recent(ln, since):
    try:
        j = json.loads(ln)
        ts = j.get("ts") or j.get("timestamp") or ""
        return bool(ts) and (datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S") >= since
                             if len(ts) >= 19 else False)
    except Exception:
        return False


def _row_recent_slow(ln, since):
    try:
        j = json.loads(ln)
        ts = j.get("ts") or ""
        return ts and datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S") >= since
    except Exception:
        return False


def _prs_merged(owner):
    import requests
    tok = _env("GITHUB_TOKEN")
    out = {"prs_merged": 0, "note": "no token"}
    try:
        r = requests.get(
            "https://api.github.com/search/issues",
            headers={"Accept": "application/vnd.github+json",
                     "Authorization": f"Bearer {tok}" if tok else "",
                     "User-Agent": "ApexGhostFamily/2.0 (receipts; repo README)"},
            params={"q": f"type:pr author:{owner} is:merged", "per_page": 1},
            timeout=20)
    except Exception as e:
        out["note"] = f"gh search failed: {type(e).__name__}"
        return out
    if r.status_code == 200:
        out = {"prs_merged": r.json().get("total_count", 0), "note": "gh:merged"}
    else:
        out = {"prs_merged": 0, "note": f"gh HTTP {r.status_code} (rate/auth) - "
                                        "honest zero, not invented"}
    return out


def _polar_sales():
    import requests
    for key in ("POLAR_OAT", "POLAR_ACCESS_TOKEN", "POLAR_OAT_SANDBOX"):
        tok = _env(key)
        if not tok:
            continue
        base = "https://sandbox-api.polar.sh" if "SANDBOX" in key \
            else "https://api.polar.sh"
        try:
            r = requests.get(base + "/v1/orders/?limit=100",
                             headers={"Authorization": f"Bearer {tok}",
                                      "User-Agent": "ApexGhostFamily/2.0"},
                             timeout=20)
            if r.status_code == 200:
                data = r.json()
                rows = (data.get("items", []) or data.get("results", [])
                        if isinstance(data, dict) else data or [])
                total = sum(1 for _ in rows)
                return {"sales": total,
                        "note": f"polar:{base.split('//')[1].split('.')[0]} (orders rows)"}
            return {"sales": 0, "note": f"polar HTTP {r.status_code} - honest zero"}
        except Exception as e:
            return {"sales": 0, "note": f"polar failed: {type(e).__name__} - honest zero"}
    return {"sales": 0, "note": "no Polar token in .env - honest zero"}


def _funnel_arrivals(since):
    p = os.path.join(AD, "Logs", "funnel_arrivals.log")
    n = 0
    try:
        for ln in open(p, encoding="utf-8", errors="ignore"):
            n += 1
    except FileNotFoundError:
        return {"funnel_arrivals": 0, "note": "no arrival log yet"}
    return {"funnel_arrivals": n, "note": f"apex-adapter arrivals log (total lines; last checked {time.strftime('%Y-%m-%d %H:%M')})"}


def measure(owner="seahawk2986-hue"):
    since = datetime.now() - timedelta(days=30)
    yard = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "window": "internal windows = trailing 30 days; external = cumulative confirmed",
        "internal": _internal_counts(since),
        "external": {},
        "law": "nothing here is promised or invented; every zero carries its reason",
    }
    gh = _prs_merged(owner)
    pol = _polar_sales()
    fun = _funnel_arrivals(since)
    yard["external"] = {"prs_merged": gh["prs_merged"],
                        "sales": pol["sales"],
                        "funnel_arrivals": fun["funnel_arrivals"]}
    yard["external_notes"] = {"github": gh["note"], "polar": pol["note"],
                              "arrivals": fun["note"]}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(yard, f, indent=1)
    os.replace(tmp, OUT)
    try:
        with open(EPISODIC, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "id": os.urandom(6).hex(), "ts": yard["generated"],
                "kind": "yardstick",
                "text": "YARDSTICK: internal " + json.dumps(yard["internal"])[:80]
                        + " | external " + json.dumps(yard["external"])[:120],
                "meta": {}, "imp": 0.9}, ensure_ascii=False) + "\n")
    except Exception:
        pass
    print("[yardstick]:", json.dumps({"internal": yard["internal"],
                                      "external": yard["external"]}, ensure_ascii=False))
    return yard


if __name__ == "__main__":
    measure()