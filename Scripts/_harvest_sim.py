"""The harvest sim: proof the retry-loop poison can never be born again.

Extracts the two REAL functions from the live engine via ast (no imports,
no side effects), stubs their two dependencies, and replays the exact
shape that killed every acceptance run: a two-tool-call batch.
"""
import ast
import io
import json
import os
import re
import sys

import py_compile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
AD = r"C:\Users\seaha\Apex-Adapter"
SRC = os.path.join(AD, "v2_job_engine.py")

# 0) both touched files must compile
py_compile.compile(SRC, doraise=True)
print("[compile]: v2_job_engine.py OK")
py_compile.compile(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Tools\lane_benchmarks.py", doraise=True)
print("[compile]: lane_benchmarks.py OK")

# 1) the regression law: the poison string must not exist in live source
src = open(SRC, encoding="utf-8").read()
n = src.count("invalid_tool_response")
print("[regression]: poison-string occurrences in live engine =", n, "(must be 0)")
assert n == 0, "poison string still in the engine!"

# 2) extract the real functions, no module side effects
ns = {"re": re, "json": json,
      "_ACTION_FIELDS": {"plan": {"steps"}, "write_file": {"path", "content"},
                         "list_files": set()},
      "_shape_rescue": lambda value: None}
got = []
for node in ast.parse(src).body:
    if isinstance(node, ast.FunctionDef) and node.name in (
            "model_message_text", "normalize_tool_action"):
        exec(compile(ast.Module(body=[node], type_ignores=[]), SRC, "exec"), ns)
        got.append(node.name)
assert sorted(got) == ["model_message_text", "normalize_tool_action"], got
mmt, nta = ns["model_message_text"], ns["normalize_tool_action"]

def call(name, args):
    return {"id": "1", "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}

fails = []

# THE KILLER SHAPE: a two-call batch (killed 10/10 retries in every past run)
raw = mmt({"tool_calls": [call("plan", {"steps": "1 write, 2 run"}),
                          call("write_file", {"path": "x.py", "content": "print(1)"})]})
act = nta(raw)
ok = act == {"action": "plan", "args": {"steps": "1 write, 2 run"}}
print("[multi-call harvest]:", "PASS" if ok else "FAIL " + repr(raw))
if not ok:
    fails.append("multi")

ok = nta(mmt({"tool_calls": [call("list_files", {})]}))["action"] == "list_files"
print("[single-call]:", "PASS" if ok else "FAIL")
if not ok:
    fails.append("single")

ok = mmt({"tool_calls": [], "content": "  prose only "}) == "prose only"
print("[empty-calls -> content]:", "PASS" if ok else "FAIL")
if not ok:
    fails.append("content")

ok = mmt({}) is None
print("[nothing -> None (honest stop)]:", "PASS" if ok else "FAIL")
if not ok:
    fails.append("none")

ok = nta(mmt({"function_call": {"name": "list_files", "arguments": "{}"}}))["action"] == "list_files"
print("[legacy function_call]:", "PASS" if ok else "FAIL")
if not ok:
    fails.append("legacy")

print("[verdict]: ALL PASS" if not fails else "[verdict]: FAIL " + ",".join(fails))