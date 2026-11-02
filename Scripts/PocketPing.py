"""PocketPing - Apex pings Andrew's iPhone via ntfy.sh (free, keyless).

The topic = a shared secret in .env (NTFY_TOPIC); the phone side = install
the free ntfy app + subscribe to that topic. Senders = the family organs.
$0 forever; nothing personal leaves home but the honest one-line pings.
"""
import io
import os
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"


def topic():
    for ln in open(os.path.join(REPO, ".env"), encoding="utf-8-sig"):
        if ln.startswith("NTFY_TOPIC="):
            return ln.split("=", 1)[1].strip()
    return None


def ping(title, body, tags="white_check_mark"):
    t = topic()
    if not t:
        return False
    req = urllib.request.Request(
        "https://ntfy.sh/" + t,
        data=(body or "").encode("utf-8"),
        headers={"Title": (title or "Apex").encode("utf-8"),
                 "Tags": tags, "Priority": "high"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception as e:
        print("[ping failed]:", type(e).__name__, str(e)[:70])
        return False


if __name__ == "__main__":
    ok = ping("Apex pings its pocket",
              "the connection = verified; the machine will page you on "
              "weaknesses, walls, and receipts", tags="rocket")
    print("[ping]:", "sent - check the phone (if subscribed)" if ok
          else "honest skip (no NTFY_TOPIC yet)")