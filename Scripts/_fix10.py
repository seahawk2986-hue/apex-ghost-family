"""_fix10: strengthen the engine's retry-prompt (one-call law) + kill the runner's zombie unpack."""
import io
import py_compile
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

P = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
src = open(P, encoding="utf-8").read()
i = src.find('            convo.append({"role": "user", "content":')
if i == -1:
    i = src.find('convo.append({"role": "user", "content":')
print("[current retry-text]:", repr(src[i:i+320]))

old = src[i:i+src.find("))", i)+2]
new = ('convo.append({"role": "user", "content":\n'
       '                "INVALID: exactly one tool-call per turn. You may have "\n'
       '                "sent multiple calls or a wrapped markup - they are all "\n'
       '                "refused. Reply with EXACTLY ONE JSON object '
       '{"action": "<tool>", "args": {...}} - the first single step only. "\n'
       '                "You will be re-prompted after each executed step."})')
src = src[:i] + src.replace(old, new, 1)
open(P, "w", encoding="utf-8").write(src)
py_compile.compile(P, doraise=True)
print("[engine]: the one-call law = in the retry (compiled)")

R = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\_acceptance_final.py"
run = open(R, encoding="utf-8").read()
lines = run.splitlines()
out = [l for l in lines if "ck, wid = final.get" not in l]
print("[runner killed-lines]:", len(lines) - len(out))
open(R, "w", encoding="utf-8").write("\n".join(out) + "\n")
py_compile.compile(R, doraise=True)
print("[runner compiled]")