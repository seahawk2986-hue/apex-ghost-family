"""The truth-resolver sim: only None is re-probed; truth can't be faked."""
import ast
import io
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SRC = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
src = open(SRC, encoding="utf-8").read()
compile(src, SRC, "exec")
print("[compile-gate]: the whole live engine still parses")

NS = {"time": time, "container_truth": None, "ANSWERS": []}


def stub_truth(container, timeout=3.0):
    return NS["ANSWERS"].pop(0) if NS["ANSWERS"] else None


NS["container_truth"] = stub_truth

for node in ast.parse(src).body:
    if isinstance(node, ast.FunctionDef) and node.name == "_resolved_truth":
        exec(compile(ast.Module(body=[node], type_ignores=[]),
                     SRC, "exec"), NS)
_resolved = NS["_resolved_truth"]

fails = []
def case(name, answers, expect):
    NS["ANSWERS"] = list(answers)
    out = _resolved("c")
    ok = out == expect
    print(f"   {name}: -> {out!r} expect {expect!r}: {'PASS' if ok else 'FAIL'}")
    if not ok:
        fails.append(name)


case("unknown-then-confirmed-dead", [None, True], True)
case("unknown-then-confirmed-alive", [None, False], False)
case("daemon-flap-stays-fail-closed", [None, None, None], None)
case("immediate-truth-no-retries", [True], True)

print("[verdict]: ALL PASS" if not fails else f"[verdict]: FAIL {fails}")
assert not fails