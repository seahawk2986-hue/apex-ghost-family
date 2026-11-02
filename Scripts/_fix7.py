"""_fix7: inject the raw-head debug into the retry-event + clean the runner."""
import io
import py_compile
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

P = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
src = open(P, encoding="utf-8").read()
old = '        except ValueError as error:\n' \
      '            ev("model-retry", "invalid tool action: " + str(error))'
new = ('        except ValueError as error:\n'
       '            ev("model-retry", "invalid tool action: " + str(error)\n'
       '                          " | raw-head: " + urllib.parse.quote(str(raw)[:220]))')
if old in src:
    src = src.replace(old, new, 1)
    open(P, "w", encoding="utf-8").write(src)
    py_compile.compile(P, doraise=True)
    print("[engine]: retry-event carries the raw-head (compiled)")
else:
    print("[engine]: already carries the debug (skip)")

R = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\_acceptance_final.py"
run = open(R, encoding="utf-8").read()
bad = '    ck, wid = final.get("checkpoint") or (None, None)\n'
if bad in run:
    open(R, "w", encoding="utf-8").write(run.replace(bad, "", 1))
    py_compile.compile(R, doraise=True)
    print("[runner]: unpack-crash line removed (compiled)")
else:
    print("[runner]: clean")

print("[urllib in engine?]", "import urllib" in open(P, encoding="utf-8").read()
      or "urllib." in open(P, encoding="utf-8").read())