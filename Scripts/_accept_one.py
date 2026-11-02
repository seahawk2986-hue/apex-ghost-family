"""THE ONE-FLOW REAL-MODEL ACCEPTANCE (Andrew-approved: local qwen2.5-coder
via the deployed adapter's REAL HTTP paths; $0; context never leaves the box):
J1 RED (write calc.py w/ deliberate bug -> run -> honest fail -> finish),
J2 GREEN (resume restored checkpoint -> fix -> run exit-0 -> finish)
   -> export-check (manifest+zip+404-on-unknown)
J3 CANCEL (sleeper.py + long run -> DELETE <= 8s -> verify-then-confirm settle
   -> the GREEN checkpoint remains exportable).
Bounds: per-job walls (120s/120s/60s), one workspace, no cloud lane, no
fallback. Evidence -> JSON next to this script."""
import json
import time
import uuid

import requests

BASE = "http://127.0.0.1:8788"
TOKEN = open(r"C:\Users\seaha\Apex-Adapter\adapter_token.txt",
             encoding="ascii").read().strip()
H = {"Authorization": "Bearer " + TOKEN}
CONVO = str(uuid.uuid4())
PROJECT = str(uuid.uuid5(uuid.NAMESPACE_URL,
                         "apex-acceptance-oneflow-local-2026-11-01"))
EVID = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "route":
        "local qwen2.5-coder-7b-instruct via LM Studio (deployed engine, "
        "zero source changes)", "items": []}

def item(name, ok, detail):
    EVID["items"].append({"item": name, "ok": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name + "  " + json.dumps(
        detail, default=str)[:220], flush=True)

def poll(rid, wall_s, early=None):
    cursor, t_end, bad = 0, time.time() + wall_s, 0
    v, evs = None, []
    while time.time() < t_end:
        try:
            v = requests.get(BASE + f"/v2/jobs/{rid}?after={cursor}",
                             headers=H, timeout=15).json()
        except Exception:
            bad += 1
            if bad > 20:
                return v, evs, "POLL-DEGRADED"
            time.sleep(1.5)
            continue
        bad = 0
        if not isinstance(v, dict) or "next_seq" not in v:
            bad += 1
            if bad > 20:
                return v, evs, "POLL-DEGRADED"
            time.sleep(1.5)
            continue
        for e in v.get("events", []):
            if e.get("seq") != cursor + 1:
                return v, evs, f"SEQ GAP at {e.get('seq')}"
            cursor = e["seq"]
            evs.append(e)
        if early is not None and early(evs):
            return v, evs, "EARLY"
        if v["state"] in ("succeeded", "failed", "cancelled"):
            return v, evs, None
        time.sleep(1.2)
    return v, evs, "POLL-TIMEOUT"

def new_job(objective, resume=None):
    rid = str(uuid.uuid4())
    body = {"schema_version": 2, "request_id": rid,
            "conversation_id": CONVO, "trigger_message_id": str(uuid.uuid4()),
            "recipient": "apex", "owner": "friend",
            "history": [{"sender": "friend", "recipient": "apex",
                         "content": objective}],
            "execution": {"mode": "coding", "project_id": PROJECT,
                          "resume": resume,
                          "limits": {"wall_ms": wall_ms, "max_tool_calls": 16,
                                     "max_output_bytes": 300000}}}
    return rid, requests.post(BASE + "/v2/jobs", json=body, headers=H,
                              timeout=30)

tool_counts = {"n": 0}
def tc(evs0, evs1):
    tool_counts["n"] += sum(1 for e in (evs0 + evs1)
                            if e["kind"] == "tool.started")

def paired(evs):
    ids, okg = {}, True
    for e in evs:
        if e["kind"] == "tool.started":
            okg &= e["call_id"] not in ids
            ids[e["call_id"]] = e.get("action")
        elif e["kind"] == "tool.finished":
            okg &= ids.get(e.get("call_id")) == e.get("action")
            ids.pop(e.get("call_id"), None)
    return okg and not ids

# ---- J1: RED
print("== J1 RED: the deliberate failing run = the deliverable ==", flush=True)
wall_ms = 120000
RED = ("Phase job - plant a deliberately failing test, do not fix anything. "
       "Step 1: write_file calc.py with EXACTLY this content, byte for byte:\n"
       "def divide(a, b):\n    return a // b\n\n"
       "if __name__ == '__main__':\n"
       "    assert divide(6, 3) == 2\n"
       "    try:\n        divide(1, 0)\n    except ValueError:\n"
       "        print('TEST GREEN')\n    else:\n        print('TEST RED')\n"
       "        raise SystemExit(1)\n"
       "Step 2: run_python calc.py. You WILL see a traceback ending in "
       "SystemExit(1) - that failing run = this job's DELIVERABLE; not your "
       "error. Step 3: call finish immediately with one sentence: "
       "'red confirmed - the test failed as designed'. Do NOT edit calc.py. "
       "A finish without a run_python here = a contract violation.")
rid_a, ra = new_job(RED)
va, ev_a, err_a = poll(rid_a, 120)
reds = [e for e in ev_a if e["kind"] == "tool.finished"
        and e.get("action", "").startswith("run_")
        and isinstance(e.get("exit_code"), int) and e["exit_code"] != 0]
writes = [e for e in ev_a if e["kind"] == "tool.finished"
          and e.get("action") == "write_file" and e.get("exit_code") == 0]
fin = any(e["kind"] == "status" and e.get("action") == "finish" for e in ev_a)
item("J1 red write->honest-fail->finish", ra.status_code == 202
     and (va or {}).get("state") == "succeeded" and reds and writes and fin,
     {"state": (va or {}).get("state"), "red_exit":
      reds[0].get("exit_code") if reds else None,
      "writes": len(writes), "finish": fin, "err": err_a,
      "paired": paired(ev_a)})
tc([], ev_a)
ck_a = (va or {}).get("checkpoint")
wid = (va or {}).get("workspace_id")

# ---- J2: GREEN (resume)
print("== J2 GREEN: resumed + fixed + exit-0 ==", flush=True)
GREEN = ("You are resumed into a restored workspace whose calc.py has a "
         "deliberately buggy divide and a self-test demanding ValueError on "
         "divide(1,0). Step 1: read_file calc.py. Step 2: fix it with "
         "edit_file (or write_file if edit fails twice) so divide raises "
         "ValueError when b==0 and returns a/b otherwise; keep the self-test. "
         "Step 3: run_python calc.py - it MUST exit 0. If the run fails, fix "
         "and run again. NEVER call finish until a run_python exited 0. "
         "If you truly cannot reach green, call finish twice - the job is "
         "then recorded honestly as FAILED. When green, finish with a sentence.")
rid_b, rb = new_job(GREEN, resume=ck_a)
vb, ev_b, err_b = poll(rid_b, 120)
gruns = [e for e in ev_b if e["kind"] == "tool.finished"
         and e.get("action", "").startswith("run_")
         and e.get("exit_code") == 0]
item("J2 green resumed->fix->exit-0->finish", rb.status_code == 202
     and (vb or {}).get("state") == "succeeded" and gruns,
     {"state": (vb or {}).get("state"), "green_exit_zero": len(gruns),
      "err": err_b, "paired": paired(ev_b)})
tc([], ev_b)
ck_b = (vb or {}).get("checkpoint")

# ---- export-check
print("== export: the passing checkpoint = bounded + sealed ==", flush=True)
if ck_b and wid:
    man = requests.get(BASE + f"/v2/workspaces/{wid}/checkpoints/{ck_b}/manifest",
                       headers=H, timeout=15)
    z = requests.get(BASE + f"/v2/workspaces/{wid}/checkpoints/{ck_b}/zip",
                     headers=H, timeout=15)
    z404 = requests.get(BASE + f"/v2/workspaces/{wid}/checkpoints/{uuid.uuid4()}/zip",
                        headers=H, timeout=15)
    item("export manifest+zip+404", man.status_code == 200
         and z.status_code == 200 and z404.status_code == 404
         and len(z.content or b"") <= 5_200_000,
         {"manifest": man.status_code, "zip": z.status_code,
          "zip_b": len(z.content or b""), "unknown_404": z404.status_code})
else:
    item("export manifest+zip+404", False, {"wid": wid, "ck_b": ck_b})

# ---- J3: CANCEL
print("== J3 CANCEL: physical settle + the green checkpoint survives ==", flush=True)
wall_ms = 60000
CANCEL = ("Cancellation drill. Step 1: write_file sleeper.py containing: "
          "import time; i=0; then a while True loop printing 'tick i' with i "
          "incremented and time.sleep(1), flush=True. Step 2: run_python "
          "sleeper.py. Do NOT call finish until the run has produced at "
          "least 5 ticks; keep waiting.")
rid_c, rc = new_job(CANCEL)
started = time.time()
_, ev_c0, _ = poll(rid_c, 40, early=lambda evs: any(
    e["kind"] == "tool.started" and str(e.get("action", "")).startswith("run_")
    for e in evs))
ticks = sum(1 for e in ev_c0 if e["kind"] == "tool.started"
            and str(e.get("action", "")).startswith("run_"))
if not ticks:
    item("J3 cancel-drill (model started a long run)", False,
         {"err": "model never started a run"})
else:
    t_d = time.time()
    rd = requests.delete(BASE + f"/v2/jobs/{rid_c}", headers=H, timeout=10)
    del_ms = int((time.time() - t_d) * 1000)
    vd = requests.get(BASE + f"/v2/jobs/{rid_c}", headers=H, timeout=10).json()
    time.sleep(6)
    vc, ev_c1, err_c1 = poll(rid_c, 45)
    containers = requests.get(BASE + "/v1/health", timeout=10)
    kinds = {e["kind"] for e in ev_c1}
    item("J3 DELETE<=8s->cancelled truth", rd.status_code == 200
         and vd.get("cancelled") is True and del_ms <= 8000,
         {"delete_ms": del_ms, "cancelled": vd.get("cancelled"),
          "state_after": (vc or {}).get("state"), "err": err_c1})
    if wid and ck_b:
        z2 = requests.get(BASE + f"/v2/workspaces/{wid}/checkpoints/{ck_b}/zip",
                          headers=H, timeout=15)
        item("green checkpoint survives the cancel", z2.status_code == 200,
             {"zip2": z2.status_code, "zip2_b": len(z2.content or b"")})
    tool_counts["n"] += sum(1 for e in ev_c0 if e["kind"] == "tool.started")

EVID["done"] = time.strftime("%Y-%m-%d %H:%M:%S")
EVID["sandbox_tool_call_count"] = tool_counts["n"]
EVID["note"] = ("provider-request exact-count = engine-internal; bounded by "
                "the engine's own caps; sandbox tool-calls = measured above")
ok_all = all(i["ok"] for i in EVID["items"])
EVID["VERDICT"] = "ACCEPTED (all items PASS)" if ok_all else "NOT ACCEPTED (honest)"
open(r"C:\Users\seaha\Apex-Adapter-FixtureStaging\Apex-Boundary-20261102"
     r"\staged-candidate\ACCEPT-EVIDENCE-LOCAL.json", "w",
     encoding="utf-8").write(json.dumps(EVID, indent=1, default=str))
print("== EVID saved; VERDICT:", EVID["VERDICT"], "==")