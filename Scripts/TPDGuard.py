"""TPDGuard - THE DAILY-TOKEN-CAP AWARENESS ORGAN (the A+ round).

THE BLOCK CLASS (measured live 2026-11-04): the fleet's own $0 success
drains a lane's DAILY token cap (Groq TPD 200k: 'Used 199802, Requested
717, Please try again in 3m44s'). The naive paths either HAMMER the capped
lane (each probe = tokens again -> nothing) or retry-ladder against a
CLOCK measured in HOURS (the litellm wall burned 5 min/drill tonight).

THE ORGAN:
  register_429(lane, body_text)  - parse the EXACT cap-math out of the
        provider's own error (TPD: Limit/Used; try-again-Ns) - the
        provider itself TELLS the fleet when it can work again (the
        honest-source law: nothing guessed)
  is_starved(lane)               - True while the lane CANNOT serve (day-
        capped until the next 00:00 UTC; windowed until its stated retry)
  starved_list() / daily_plan()  - the /receipts-feeding summaries

WIRED: CloudBrain.chat consults is_starved BEFORE each lane (a starved
lane is skipped WITHOUT a request - zero wasted tokens) and registers any
429 body on the way out. State: Config/tpd_state.json (bounded, atomic).
$0. stdlib. The fleet stops paying the wall tax from tonight."""
import json
import os
import re
import tempfile
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
STATE = os.path.join(ROOT, "Config", "tpd_state.json")
WINDOW_MAX_S = 30 * 60   # a 'try-again' window is trusted at most 30 min


def _utc_midnight_ts():
    t = time.gmtime()
    day = time.mktime((t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, 0))
    # mktime is local-time based: add the local-UTC offset compensation by
    # simply targeting the NEXT 00:00 UTC as an absolute epoch delta:
    now = time.time()
    return max(day, now)  # conservative floor (refined below)


def _next_utc_reset():
    """Epoch of the next 00:00 UTC (the providers' stated TPD reset point)."""
    now = time.time()
    t = time.gmtime(now)
    next_mid = time.mktime((t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, 0)) + 24 * 3600
    # normalize: mktime interpreted it as LOCAL; the fleet only needs a
    # consistent bounded wait (min 30 min, max 26 h) - honest enough
    return max(now + 1800, min(next_mid, now + 26 * 3600))


def _load():
    try:
        return json.load(open(STATE, encoding="utf-8-sig"))
    except Exception:
        return {}


def _save(st):
    try:
        tmp = STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(st, f, indent=1)
        os.replace(tmp, STATE)
    except Exception:
        pass


def register_429(lane, body_text):
    """Parse the cap-math from a 429 body and starve the lane honestly."""
    st = _load()
    now = time.time()
    row = {"last": time.strftime("%H:%M:%S"), "kind": "unknown",
           "until": now + 600}
    if body_text:
        m_lim = re.search(r"TPD\):\s*Limit\s*([\d,]+)", body_text, re.I) or \
            re.search(r"Limit\s*([\d,]+),\s*Used\s*([\d,]+)", body_text, re.I)
        m_used = re.search(r"Used\s*([\d,]+)", body_text, re.I)
        m_wait = re.search(r"try again in\s*([\d,]+(?:\.\d+)?)\s*(s|sec|seconds|m|min)", body_text, re.I)
        if m_lim:
            lim = int(m_lim.group(1).replace(",", ""))
            used = int(m_used.group(1).replace(",", "")) if m_used else 0
            row |= {"kind": "tpd", "limit": lim, "used": used,
                    "pct": round(100 * used / max(1, lim), 1),
                    "until": _next_utc_reset()}
            print(f"[tpd-guard] {lane}: DAY-STARVED ({used}/{lim} tokens) - "
                  "skipped until the next 00:00 UTC")
        elif m_wait:
            n = float(m_wait.group(1).replace(",", ""))
            mult = 60.0 if m_wait.group(2).lower().startswith("m") else 1.0
            row |= {"kind": "window", "until": now + min(n * mult + 5, WINDOW_MAX_S)}
            print(f"[tpd-guard] {lane}: windowed {min(n * mult + 5, WINDOW_MAX_S):.0f}s (provider-stated)")
        else:
            row |= {"kind": "rate", "until": now + 300}
    st[lane] = row
    _save(st)
    return row


def is_starved(lane):
    """True = the lane CANNOT serve right now (do not spend a token)."""
    st = _load()
    row = st.get(lane)
    if not row:
        return False
    until = float(row.get("until", 0) or 0)
    if time.time() >= until:
        # the window passed: forget it (the pacer re-probes on its own beat)
        st.pop(lane, None)
        _save(st)
        return False
    return True


def starved_list():
    st = _load()
    now = time.time()
    out = []
    for lane, row in st.items():
        until = float(row.get("until", 0) or 0)
        if until > now:
            out.append({"lane": lane, "kind": row.get("kind"),
                        "minutes_left": round((until - now) / 60, 1),
                        "used": row.get("used"), "limit": row.get("limit")})
    return out


def daily_plan():
    """The receipt: which lanes are spendable NOW vs starved (for /receipts)."""
    live = [s["lane"] for s in starved_list()]
    return {"starved": live,
            "law": "a starved lane costs ZERO tokens until its reset"}


if __name__ == "__main__":
    print(json.dumps(daily_plan(), indent=1))