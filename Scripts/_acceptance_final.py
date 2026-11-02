"""THE ACCEPTANCE, FINAL: the proven micro-shape + the full arc + poll + export.
Every step prints unbuffered; hashes at the end."""
import io
import json
import sys
import time
import uuid

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
A = r"C:\Users\seaha\Apex-Adapter"
T = open(A + r"\adapter_token.txt", encoding="ascii").read().strip()
H = {"Authorization": "Bearer " + T}
BASE = "http://127.0.0.1:8788"

TASK = ("Create calc.py with divide(a,b) returning a/b. Create test_calc.py with "
        "test_divide(): assert divide(7,2)==3.5. Run the test; fix calc.py if it "
        "fails; re-run until green; write RESULT.txt = 'acceptance-green'.")
rid = str(uuid.uuid4())
body = {"schema_version": 2, "request_id": rid,
        "conversation_id": str(uuid.uuid4()),
        "trigger_message_id": str(uuid.uuid4()), "recipient": "apex",
        "owner": "friend", "history": [
            {"sender": "friend", "recipient": "apex", "content": TASK}],
        "execution": {"mode": "coding",
                      "project_id": str(uuid.uuid4()), "resume": None,
                      "limits": {"wall_ms": 600000, "max_tool_calls": 24,
                                 "max_output_bytes": 1000000}}}
t0 = time.time()
r = requests.post(BASE + "/v2/jobs", json=body, headers=H, timeout=(10, 30))
print("[submit]:", r.status_code, "in", round(time.time() - t0, 1), "s |",
      r.text[:180])
if r.status_code != 202:
    sys.exit(0)

cursor, t_end, evs = 0, time.time() + 580, []
final = {}
while time.time() < t_end:
    try:
        v = requests.get(BASE + "/v2/jobs/" + rid + "?after=" + str(cursor),
                         headers=H, timeout=(10, 15)).json()
    except Exception:
        time.sleep(3)
        continue
    for e in v.get("events", []):
        if e.get("seq") == cursor + 1:
            cursor = e["seq"]
            evs.append(e)
            print("  [ev]", e.get("seq"), e.get("action") or e.get("kind"),
                  "|", str(e.get("output") or "")[:110])
    if v.get("state") in ("succeeded", "failed", "cancelled"):
        final = v
        break
    time.sleep(5)

if not final:
    final = {"state": "wall"}
print("[final]:", final.get("state"), "|", str(final.get("failure_note") or "")[:110])
ck = (final.get("checkpoint") or {})
if isinstance(ck, dict) and ck.get("checkpoint_id"):
    ckid, wid = ck["checkpoint_id"], ck["workspace_id"]
    print("[checkpoint files]:", ck.get("file_count"), "| bytes:", ck.get("total_bytes"))
    man = requests.get(BASE + "/v2/workspaces/" + wid + "/checkpoints/" + ckid
                       + "/manifest", headers=H, timeout=(10, 30))
    zp = requests.get(BASE + "/v2/workspaces/" + wid + "/checkpoints/" + ckid
                      + "/zip", headers=H, timeout=(10, 90))
    z404 = requests.get(BASE + "/v2/workspaces/" + wid + "/checkpoints/"
                        + str(uuid.uuid4()) + "/zip", headers=H, timeout=(10, 30))
    print("[export]: manifest", man.status_code, "| zip", zp.status_code,
          "| unknown-404", z404.status_code)
    if zp.status_code == 200:
        p = A + r"\acceptance_export.zip"
        open(p, "wb").write(zp.content)
        sha = __import__("hashlib").sha256(zp.content).hexdigest()
        print("[zip]:", len(zp.content), "b | sha256:", sha)
        print("[manifest]:", man.text[:420])
        json.dump({"rid": rid, "state": final.get("state"),
                   "checkpoint": ck, "zip_sha256": sha,
                   "export": {"manifest": man.status_code, "zip": zp.status_code,
                              "unknown_404": z404.status_code}},
                  open(A + r"\acceptance_run_result.json", "w", encoding="utf-8"),
                  indent=1)
        print("[saved]: acceptance_run_result.json")
    else:
        json.dump({"rid": rid, "state": final.get("state"),
                   "failure_note": final.get("failure_note"),
                   "export_refused": {"manifest": man.status_code,
                                      "zip": zp.status_code}},
                  open(A + r"\acceptance_run_result.json", "w", encoding="utf-8"),
                  indent=1)
        print("[saved honestly]: the run's result only (no zip to seal)")