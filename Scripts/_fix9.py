"""_fix9: the raw-head encoder = json.dumps (json = always imported here)."""
import io
import py_compile
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
src = open(P, encoding="utf-8").read()
bad = '" | raw-head: " + urllib.parse.quote(str(raw)[:220]))'
if bad in src:
    src = src.replace(bad, '" | raw-head: " + json.dumps(str(raw)[:220]))', 1)
    open(P, "w", encoding="utf-8").write(src)
    py_compile.compile(P, doraise=True)
    print("[engine]: the encoder = json.dumps (compiled CLEAN)")
else:
    print("[engine]: already clean")
import importlib.util
sys.path.insert(0, r"C:\Users\seaha\Apex-Adapter")
spec = importlib.util.spec_from_file_location("e4", P)
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
print("[import-live]: OK")