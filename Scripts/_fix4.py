"""_fix4: line-precise brace-de-doubling (docker-format lines preserved) + sim."""
import io
import py_compile
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
lines = open(P, encoding="utf-8").read().splitlines(keepends=True)
fixed = 0
for i, ln in enumerate(lines):
    if "{{" in ln and ".State.Running" not in ln:
        lines[i] = ln.replace("{{", "{").replace("}}", "}")
        fixed += 1
open(P, "w", encoding="utf-8").write("".join(lines))
print("[de-doubled lines]:", fixed)
py_compile.compile(P, doraise=True)
print("[compiled]: CLEAN")

import importlib.util
import sys as s2
s2.path.insert(0, r"C:\Users\seaha\Apex-Adapter")
spec = importlib.util.spec_from_file_location("eng2", P)
eng = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eng)
TC, SL, GT = chr(60), chr(47), chr(62)
qo, qc = TC + "tool_call" + GT, TC + SL + "tool_call" + GT
samples = [
    qo + '{"name":"write_file","arguments":{"path":"x.py","content":"hi"}}' + qc,
    '```json\n{"action":"read_file","args":{"path":"y.py"}}\n```',
    '{"name":"finish","arguments":{"content":"done"}}',
]
for raw in samples:
    try:
        v = eng.normalize_tool_action(raw)
        act = v["action"] if isinstance(v, dict) and "action" in v else None
        print("   [RESCUED]", str(raw)[:40], "->", act, "| args:", str(v.get("args"))[:40] if v else "")
    except Exception as e:
        print("   [declined]", str(raw)[:40], "|", str(e)[:60])
print("[SIM]: the live normalize = verdict above")