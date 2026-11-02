"""_fix3: de-double the braces inside MY function-range + the FULL sim test."""
import io
import py_compile
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
src = open(P, encoding="utf-8").read()
a = src.find("def _shape_rescue")
assert a != -1
b = src.find("\ndef ", a + 10)
seg = src[a:b]
seg2 = seg.replace("{{", "{").replace("}}", "}")
print("[brace-fixes]:", (seg.count("{{") + seg.count("}}")))
src = src[:a] + seg2 + src[b:]
open(P, "w", encoding="utf-8").write(src)
py_compile.compile(P, doraise=True)
print("[compiled clean]")

# THE FULL FUNCTION SIM (the live path this time):
import importlib.util
import sys
sys.path.insert(0, r"C:\Users\seaha\Apex-Adapter")
spec = importlib.util.spec_from_file_location("eng", P)
eng = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(eng)
except Exception as e:
    print("[import blocked by side-effects]:", str(e)[:80])
else:
    TC, SL, LB = chr(60), chr(47), chr(124)
    qo, qc = TC + "tool_call" + chr(62), TC + SL + "tool_call" + chr(62)
    samples = [
        (qo + '{"name":"write_file","arguments":{"path":"x.py","content":"hi"}}' + qc, "write_file"),
        ('```json\n{"action":"read_file","args":{"path":"y.py"}}\n```', "read_file"),
        ('{"name":"finish","arguments":{"content":"done"}}', "finish"),
        ('garbage {"action":"nope', None),
    ]
    for raw, want in samples:
        try:
            v = eng.normalize_tool_action(raw)
            act = v.get("action") if isinstance(v, tuple) else (v.get("action") if isinstance(v, dict) else None)
            print("   [rescue]", str(raw)[:44], "->", act)
        except Exception as e:
            print("   [declined]", str(raw)[:44], "|", str(e)[:60])