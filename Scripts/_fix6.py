"""_fix6: restore the tested tail + full-sim + verify. The final recovery."""
import io
import py_compile
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
LIVE = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
STAGED = (r"C:\Users\seaha\Apex-Adapter-FixtureStaging"
          r"\Apex-Integrated-STAGED\v2_job_engine.py")
live = open(LIVE, encoding="utf-8").read()
staged = open(STAGED, encoding="utf-8").read()

a = live.find('    action, args = value["action"], value["args"]')
print("[a-find]:", a, "| [context]:", repr(live[a - 50:a + 80]) if a != -1 else "NONE")
a += len('    action, args = value["action"], value["args"]') + 1
b = live.find("\ndef model_message_text", a)
print("[b-find]:", b)
assert a != -1 and b != -1 and b >= a, "anchors lost"
tail_start = staged.find('    action, args = value["action"], value["args"]')
tail_start += len('    action, args = value["action"], value["args"]')
tail_end = staged.find("\ndef model_message_text", tail_start)
tail = staged[tail_start:tail_end]
assert "return {" in tail and "_ACTION_FIELDS" in tail, "wrong tail"
live2 = live[:a] + "\n" + tail + live[b:]
open(LIVE, "w", encoding="utf-8").write(live2)
py_compile.compile(LIVE, doraise=True)
print("[tail restored + compiled]")

import importlib.util
import sys as s2
s2.path.insert(0, r"C:\Users\seaha\Apex-Adapter")
spec = importlib.util.spec_from_file_location("eng3", LIVE)
eng = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eng)
TC, SL, GT, LBr, RBr, QT = chr(60), chr(47), chr(62), chr(123), chr(125), chr(34)
qo, qc = TC + "tool_call" + GT, TC + SL + "tool_call" + GT
inner = (LBr + QT + "name" + QT + ": " + QT + "write_file" + QT + ", " + QT
         + "arguments" + QT + ": " + LBr + QT + "path" + QT + ": " + QT + "x.py"
         + QT + ", " + QT + "content" + QT + ": " + QT + "hello" + QT
         + RBr + RBr)
for raw in (qo + inner + qc,
            "```json\n" + LBr + QT + "action" + QT + ": " + QT + "read_file"
            + QT + ", " + QT + "args" + QT + ": " + LBr + QT + "path" + QT
            + ": " + QT + "y.py" + QT + RBr + RBr + "\n```"):
    v = eng.normalize_tool_action(raw)
    print("   [v]:", str(v)[:110])
print("[SIM = THE LIVE TRUTH]")