"""THE NATIVE-ARMS PROOF: groq gpt-oss-120b WITH the schema-constrained
`tools` (the trained-native function-calling = the top-tier's own hands).
5 shots, the engine's EXACT action-schema; count the strict tool_calls.
This = the capability-test that decides the engine-branch design. $0."""
import json
import os
import sys

import requests as rq

import sys
import time

import requests as rq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import CloudBrain  # noqa: E402  (the family's own honest key-reader)

key = CloudBrain.env_keys().get("GROQ_API_KEY")

TARGET = os.environ.get("NATIVE_TARGET", "groq")
BASE = ("https://api.groq.com/openai/v1/chat/completions"
        if TARGET == "groq" else "http://127.0.0.1:1234/v1/chat/completions")
MODEL = ("openai/gpt-oss-120b" if TARGET == "groq"
         else "qwen2.5-coder-7b-instruct")
AUTH = ({"Authorization": "Bearer " + key} if TARGET == "groq" else {})
print(f"[target]: {TARGET} ({MODEL})")
TOOLS = [
  {"type": "function", "function": {"name": "write_file",
    "description": "Create or overwrite a workspace file with exact text.",
    "parameters": {"type": "object", "properties": {"path": {"type": "string"},
        "text": {"type": "string"}}, "required": ["path", "text"]}}},
  {"type": "function", "function": {"name": "read_file",
    "description": "Read a workspace file.",
    "parameters": {"type": "object", "properties": {"path": {"type": "string"}},
                   "required": ["path"]}}},
  {"type": "function", "function": {"name": "edit_file",
    "description": "Replace an exact substring in a workspace file.",
    "parameters": {"type": "object", "properties": {"path": {"type": "string"},
        "old": {"type": "string"}, "new": {"type": "string"}},
        "required": ["path", "old", "new"]}}},
  {"type": "function", "function": {"name": "run_python",
    "description": "Run a workspace python file in the sealed container.",
    "parameters": {"type": "object", "properties": {"path": {"type": "string"}},
                   "required": ["path"]}}},
  {"type": "function", "function": {"name": "finish",
    "description": "End the job with one honest sentence about what happened.",
    "parameters": {"type": "object", "properties": {"summary": {"type": "string"}},
                   "required": ["summary"]}}},
]
SYSTEM = ("You are Apex's coding hands in a sealed container. ONE tool action "
          "per reply, exactly the schema. Never write code as prose when a "
          "tool fits; call finish only after the goal is truly met.")
ASKS = [
  "Write calc.py containing divide(a,b) returning a//b, with a __main__ self-test that asserts divide(6,3)==2.",
  "Read the file calc.py to inspect its current content.",
  "Fix calc.py so divide raises ValueError when b==0; use one tool action.",
  "Run calc.py to see whether its self-test passes.",
  "The self-test passed. Finish with one sentence.",
]
lat = []
compliant = 0
for i, ask in enumerate(ASKS, 1):
    t0 = time.time()
    r = None
    for attempt in range(3):
        r = rq.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": "Bearer " + key},
                    json={"model": "openai/gpt-oss-120b", "temperature": 0,
                          "max_tokens": 800, "tools": TOOLS,
                          "tool_choice": "required",
                          "messages": [{"role": "system", "content": SYSTEM},
                                       {"role": "user", "content": ask}]},
                    timeout=60)
        if r.status_code == 429:
            wait = 45 * (attempt + 1)
            print(f"  shot-{i}: 429 (the organ-window) - waiting {wait}s")
            time.sleep(wait)
            continue
        break
    dt = round(time.time() - t0, 2)
    lat.append(dt)
    ok = False
    detail = ""
    if r.status_code == 200:
        m = r.json()["choices"][0]["message"]
        tc = m.get("tool_calls") or []
        if tc and tc[0]["function"]["name"]:
            ok = True
            detail = (tc[0]["function"]["name"] +
                      " args<" + tc[0]["function"]["arguments"][:70] + ">")
    print(f"  shot-{i}: HTTP {r.status_code} in {dt}s | {detail if ok else (r.text)[:80]}")
    compliant += ok
print(f"\n[native-strict compliance]: {compliant}/5 in {round(sum(lat)/len(lat),2)}s avg")
print("[VERDICT]:", "THE HANDS-CONVERSION = APPROVED-BY-EVIDENCE" if compliant >= 4
      else "the native lane = mixed - inspect the misses honestly")