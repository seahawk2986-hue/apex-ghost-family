"""_fix11: collapse the broken multi-line ev/appends into one safe line."""
import io
import py_compile
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
src = open(P, encoding="utf-8").read()
i = src.find('"INVALID: exactly one tool-call per turn.')
assert i != -1, "the block gone"
d = src.find('"You will be re-prompted after each executed."})', i)
assert d != -1, "the end gone"
# find the convo.append line-start before i
st = src.rfind("convo.append", 0, i)
line = ('            convo.append({"role": "user", "content": "INVALID: exactly '
        'one tool-call per turn. Reply with EXACTLY ONE JSON object '
        '{"action": "<tool>", "args": {...}} - the single next step only; '
        'you will be re-prompted after each executed step."})')
src = src[:st] + line + src[d + len('"You will be re-prompted after each executed."})'):]
open(P, "w", encoding="utf-8").write(src)
py_compile.compile(P, doraise=True)
print("[engine]: ONE-LINE retry-law + compiled CLEAN")

R = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\_acceptance_final.py"
run = open(R, encoding="utf-8").read()
out = "\n".join(l for l in run.splitlines() if "ck, wid = final.get" not in l) + "\n"
open(R, "w", encoding="utf-8").write(out)
py_compile.compile(R, doraise=True)
print("[runner]: zombie-line killed + compiled")