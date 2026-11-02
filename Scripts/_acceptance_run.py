"""THE ACCEPTANCE RUN: create files -> run a failing test -> fix it ->
re-run to green -> export the checkpoint. Real model, real container,
every step receipted; hashes at the end."""
import io
import json
import sys
import time
import uuid
import hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
A = r"C:\Users\seaha\Apex-Adapter"
BASE = "http://127.0.0.1:8788"
TOKEN = open(A + r"\adapter_token.txt", encoding="ascii").read().strip()
H = {"Authorization": "Bearer " + TOKEN}

TASK = ("Create two Python files in the workspace. 1) calc.py with divide(a, b) "
        "returning a/b (float division). 2) test_calc.py containing "
        "test_divide_half(): assert divide(7, 2) == 3.5. After creating both, "
        "run the test with python, read the result, fix what fails, and re-run "
        "until it passes. If all green, write RESULT.txt containing 'acceptance-green'.")

rid = str(uuid.uuid4())
_proj = uuid.uuid5(uuid.NAMESPACE_URL, "acceptance-" + time.strftime("%Y%m%d%H%M"))
_body_conv = _proj  # the same-UUID family: convo = project identity
body = {"schema_version": 2, "request_id": rid,
        "conversation_id": str(_body_conv),
        "trigger_message_id": str(uuid.uuid4()),
        "recipient": "apex", "owner": "friend",
        "history": [{"sender": "friend", "recipient": "apex", "content": TASK}],
        "execution": {"mode": "coding",
                      "project_id": str(uuid.uuid5(
                          uuid.NAMESPACE_URL, "proj-" + str(_proj))),
                      "resume": None,
                      "limits": {"wall_ms": 420000, "max_tool_calls": 18,
                                 "max_output_bytes": 200000}}}
r = __import__("requests").post(BASE + "/v2/jobs", json=body, headers=H, timeout=30)
print("[submit]:", r.status_code, r.text[:160])

cursor, t_end, events = 0, time.time() + 430, []
while time.time() < t_end:
    try:
        v = requests.get(BASE + f"/v2/jobs/{rid}?after={cursor}", headers=H,
                         timeout=15).json()
    except Exception:
        time.sleep(2)
        continue
    for e in v.get("events", []):
        if e.get("seq") == cursor + 1:
            cursor = e["seq"]
            events.append(e)
            kind = str(e.get("kind", ""))
            txt = str(e.get("detail") or e.get("text") or e.get("data") or "")[:150]
            print("  [ev]", e["seq"], kind, "|", txt)
    s = v.get("state")
    if s in ("succeeded", "failed", "cancelled"):
        print("[final state]:", s)
        break
    time.sleep(4)

final = v
ck, wid = final.get("checkpoint"), final.get("workspace_id")
print("[checkpoint]:", ck, "| workspace:", wid)
if ck and wid:
    man = requests.get(BASE + f"/v2/workspaces/{wid}/checkpoints/{ck}/manifest",
                       headers=H, timeout=30)
    zp = requests.get(BASE + f"/v2/workspaces/{wid}/checkpoints/{ck}/zip",
                      headers=H, timeout=60)
    z404 = requests.get(BASE + f"/v2/workspaces/{wid}/checkpoints/{uuid.uuid4()}/zip",
                        headers=H, timeout=30)
    print(f"[export]: manifest={man.status_code} zip={zp.status_code} unknown-404={z404.status_code}")
    if zp.status_code == 200:
        zp_path = A + r"\acceptance_export.zip"
        open(zp_path, "wb").write(zp.content)
        print("[zip saved]:", zp_path, len(zp.content), "bytes")
        print("[zip sha256]:", hashlib.sha256(zp.content).hexdigest())
        try:
            names = json.loads(man.text)
            if isinstance(names, dict):
                names = names.get("files", names)
            print("[manifest files]:", json.dumps(names)[:300])
        except Exception:
            print("[manifest head]:", man.text[:200])

out = {"rid": rid, "final": {k: final.get(k) for k in
        ("state", "checkpoint", "workspace_id")}, "events_tail":
       [{k: e.get(k) for k in ("seq", "kind", "detail")} for e in events[-6:]],
       "export_status": {"manifest": getattr(man, 'status_code', None),
                         "zip": getattr(zp, 'status_code', None),
                         "zip_sha256": hashlib.sha256(zp.content).hexdigest()
                         if zp.status_code == 200 else None}}
with open(A + r"\acceptance_run_result.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False, default=str)
print("[saved]: acceptance_run_result.json")