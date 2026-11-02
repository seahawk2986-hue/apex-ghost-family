"""the tier-verify: the normal + the deep knock (the raw path, no escape traps)."""
import io
import sys
import time
import uuid
import json

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
A = r"C:\Users\seaha\Apex-Adapter"
TOK = open(A + "\\adapter_token.txt", encoding="ascii").read().strip()
H = {"Authorization": "Bearer " + TOK}

for conv, note, dl in (("recheck-normal", "ping", 45000),
                       ("recheck-deep", "Explain why the sky is blue - one sentence.", 75000)):
    body = {"schema_version": 1, "request_id": str(uuid.uuid4()),
            "trigger_message_id": str(uuid.uuid4()),
            "conversation_id": conv + str(time.time()),
            "deadline_ms": dl, "recipient": "apex",
            "history": [{"sender": "friend", "recipient": "apex",
                         "content": note}]}
    t0 = time.time()
    r = requests.post("http://127.0.0.1:8788/v1/respond", json=body,
                      headers=H, timeout=120)
    d = r.json()
    content = str(d.get("message", {}).get("content", ""))[:52]
    acts = d.get("activity", [])
    engine = acts[0].get("output", "?") if acts else "?"
    swarm = next((a.get("output", "") for a in acts
                  if a.get("action") == "SwarmConsensus"), "-")
    print(f"[{conv}]: {r.status_code} in {round(time.time()-t0,1)}s | "
          f"{content!r} | {engine} | {swarm[:40]}")