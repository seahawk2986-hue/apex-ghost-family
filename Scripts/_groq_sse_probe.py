"""THE GROQ-SSE MIRROR-DUMP: see exactly what the streaming request
returns vs what chat_stream's parser expects."""
import json
import os
import sys

import requests as rq

os.chdir(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed")
sys.path.insert(0, "Scripts")
import CloudBrain as CB

keys = CB.env_keys()
H = {"Authorization": "Bearer " + keys.get("GROQ_API_KEY", ""),
     "Content-Type": "application/json"}
body = {"model": "openai/gpt-oss-120b", "stream": True,
        "messages": [{"role": "user", "content": "Count 1 to 3."}],
        "max_tokens": 800, "temperature": 0}
try:
    with rq.post("https://api.groq.com/openai/v1/chat/completions",
                 headers=H, json=body, stream=True, timeout=60) as r:
        print("[status]", r.status_code, "| ct:", r.headers.get("content-type"))
        i = 0
        for line in r.iter_lines(decode_unicode=True):
            i += 1
            print(f"  L{i}: {line!r}"[:150])
            if i >= 8:
                break
except Exception as e:
    print("[groq-sse]", type(e).__name__, str(e)[:140])