"""THE SINGLE-LANE GROQ-STREAM PROBE: which exception does chat_stream
swallow for the groq lane? (the except = made loud for this probe)"""
import json
import os
import sys
import time

os.chdir(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed")
sys.path.insert(0, "Scripts")
import CloudBrain as CB

# the loud-version: copy of chat_stream with the exception-print
keys = CB.env_keys()
url = "https://api.groq.com/openai/v1/chat/completions"
model = "openai/gpt-oss-120b"
hdrs = {"Authorization": "Bearer " + keys.get("GROQ_API_KEY", "")}
body = {"model": model, "stream": True,
        "messages": [{"role": "user", "content": "Count 1 to 3."[:9000]}],
        "max_tokens": 800, "temperature": 0}
n = 0
try:
    import requests as _rq
    with _rq.post(url, headers=hdrs, json=body, stream=True, timeout=90) as r:
        print("[status]", r.status_code)
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            s = line.strip()
            if not s.startswith("data:"):
                print("  [non-data line]", repr(s[:40]))
                continue
            p = s[5:].strip()
            if p == "[DONE]":
                print("  [DONE reached]")
                break
            try:
                j = json.loads(p)
                chs = j.get("choices") or [{}]
                tok = (chs[0].get("delta") or {}).get("content") or ""
                if tok:
                    n += 1
            except Exception as e:
                print("  [parse-fail]", repr(p[:60]), "|", str(e)[:60])
except Exception as e:
    print("[EXCEPTION]", type(e).__name__, str(e)[:140])
print("[tokens]:", n)

# AND the module-level check: the served chat_stream (the real one) w/ groq:
try:
    got = list(CB.chat_stream("Count 1 to 3.", max_tokens=40, purpose="probe",
                              models=("groq",)))
    print("[chat_stream groq]: rows:", len(got), "first:", got[:2])
except Exception as e:
    print("[chat_stream groq-EXC]", type(e).__name__, str(e)[:140])