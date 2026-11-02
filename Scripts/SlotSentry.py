"""SlotSentry - the slot-self-healing organ.

The 11/02 finding: any job ending 'cancelling' (container shutdown
unverified) RETAINS the busy slot; a dead worker can never settle it, and
every fresh job then 409s. Manual unsticks today = 3. This sentry closes
that loop forever:

  1. read jobs_registry.json
  2. a record = STUCK iff: non-terminal state AND its tool_events log
     has been silent > 20 min (never touches an active model loop)
  3. DELETE via the designed auth route (idempotent tombstone)
  4. if the slot survives that, reload the adapter through its
     own scheduled task's reload path (the proven one)
  5. append an honest line to scores/slot_sentry.jsonl

Runs every 10 min from Apex-SlotSentry; $0, local, never invents.
"""
import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
AD = r"C:\Users\seaha\Apex-Adapter"
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
REG = os.path.join(AD, "jobs_registry.json")
EVENTS = os.path.join(AD, "tool_events")
SENTRY = os.path.join(REPO, "scores", "slot_sentry.jsonl")
SILENT_S = 20 * 60


def newest_event_age(rid):
    p = os.path.join(EVENTS, rid + ".jsonl")
    if os.path.isfile(p):
        return time.time() - os.path.getmtime(p)
    rec = json.load(open(REG, encoding="utf-8")).get("jobs", {}).get(rid, {})
    born = rec.get("started") or rec.get("created") or time.time()
    return time.time() - born


def main():
    try:
        data = json.load(open(REG, encoding="utf-8"))
    except Exception as e:
        print("[sentry]: registry unreadable:", str(e)[:60])
        return
    jobs = data.get("jobs", {})
    stuck = []
    for rid, rec in jobs.items():
        state = rec.get("state")
        if state in ("succeeded", "failed", "cancelled"):
            continue
        if newest_event_age(rid) > SILENT_S:
            stuck.append(rid)
    if not stuck:
        print("[sentry]: no stuck slots")
        return

    token = open(os.path.join(AD, "adapter_token.txt"),
                 encoding="ascii").read().strip()
    for rid in stuck:
        req = urllib.request.Request(
            "http://127.0.0.1:8788/v2/jobs/" + rid, method="DELETE",
            headers={"Authorization": "Bearer " + token})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                print("[sentry delete", rid[:8] + "]:",
                      r.status, r.read().decode("utf-8")[:70])
        except Exception as e:
            print("[sentry delete", rid[:8], "] error:", type(e).__name__,
                  str(e)[:60])

    time.sleep(4)
    data = json.load(open(REG, encoding="utf-8"))
    still = data.get("_slot")
    if still:
        print("[sentry]: slot still held -> the proven reload path")
        subprocess.run([os.path.join(REPO, "apex_venv", "Scripts",
                                     "python.exe"), "-X", "utf8",
                        os.path.join(REPO, "Scripts", "_reload_and_wait.py")],
                       timeout=180)
        data = json.load(open(REG, encoding="utf-8"))
        still = data.get("_slot")
    with open(SENTRY, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "stuck": [r[:8] for r in stuck],
                            "slot_now": None if not still else still[:8]},
                           ensure_ascii=False) + "\n")
    print("[sentry]: done | slot:",
          "released" if not still else "still " + str(still)[:8])


if __name__ == "__main__":
    main()