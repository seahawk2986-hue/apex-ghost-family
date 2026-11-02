"""THE HANG-DIAG (the small, fast, three-probe): (a) the serve's stream =
the no-first-byte-in-60s? (b) the ollama = the direct small stream (the
slot-state), (c) the serve-side log's tail."""
import json
import os
import sys
import threading
import time

import requests as rq

os.chdir(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed")
sys.path.insert(0, "Scripts")

# (c) first - the log's tail (the evidence exists?)
tail = open("Logs/system.log", encoding="utf-8-sig", errors="ignore"
            ).read().splitlines()[-6:]
for ln in tail:
    print("[log]", ln[:110])

# (b) the ollama-direct: is the local lane stream-healthy right now?
try:
    t0 = time.time()
    with rq.post("http://localhost:11434/api/chat", stream=True, timeout=25,
                 json={"model": "qwen2.5-coder:7b", "stream": True,
                       "messages": [{"role": "user", "content": "say OK"}],
                       "keep_alive": 0,
                       "options": {"num_predict": 16, "temperature": 0}}) as r:
        n = 0
        for line in r.iter_lines(decode_unicode=True):
            if line:
                n += 1
            if n >= 6:
                break
    print(f"[ollama-direct] OK: {n} lines in {time.time()-t0:.1f}s")
except Exception as e:
    print("[ollama-direct]", type(e).__name__, str(e)[:90])

# (a) the serve's stream with a strict 30s read: does ANY byte arrive?
KEY = open("Config/apex_api.key", encoding="utf-8-sig").read().strip()
try:
    t0 = time.time()
    r = rq.post("http://127.0.0.1:8080/talk/api/stream",
                json={"message": "Say OK."},
                headers={"X-Apex-Key": KEY}, stream=True, timeout=30)
    print("[stream] HTTP", r.status_code, "hdr:", r.headers.get("content-type"))
    got = ""
    for line in r.iter_lines(decode_unicode=True):
        if line:
            got += line[:40] + "|"
        if len(got) > 200 or time.time() - t0 > 28:
            break
    print(f"[stream] {time.time()-t0:.1f}s first-bytes: {got[:140]}")
except Exception as e:
    print(f"[stream] {type(e).__name__}", (str(e) or "")[:90])