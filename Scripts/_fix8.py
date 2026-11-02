"""_fix8: the ev-call = one-line (the implicit-concat needs no split)."""
import io
import py_compile
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
src = open(P, encoding="utf-8").read()
broken1 = '            ev("model-retry", "invalid tool action: " + str(error)\n'
broken2 = '                          " | raw-head: " + urllib.parse.quote(str(raw)[:220]))'
if broken1 in src and broken2 in src:
    src = src.replace(broken1, "", 1)
    src = src.replace(broken2,
                      '            ev("model-retry", "invalid tool action: " + str(error) + " | raw-head: " + urllib.parse.quote(str(raw)[:220]))', 1)
    open(P, "w", encoding="utf-8").write(src)
    py_compile.compile(P, doraise=True)
    print("[engine]: one-lined + compiled CLEAN")
else:
    print("[state]:", "broken1" if broken1 in src else "-", "broken2" in src)
print("[urllib imported]:", "import urllib" in src)