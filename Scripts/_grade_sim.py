"""The grade-fix sim: string truths must grade by VALUE (Paris == Paris)."""
import ast
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SRC = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\ApexGym.py"
src = open(SRC, encoding="utf-8").read()
ns = {}
for node in ast.parse(src).body:
    if isinstance(node, ast.FunctionDef) and node.name == "grade":
        exec(compile(ast.Module(body=[node], type_ignores=[]), SRC, "exec"), ns)
grade = ns["grade"]

fails = []
cases = [
    ({"verify_py": "'Paris'"}, "Paris | confidence: high", True),   # THE bug case
    ({"verify_py": "'Paris'"}, "Paris", True),
    ({"verify_py": "'paris'"}, "PARIS", True),                      # case-value truth
    ({"verify_py": "'Paris'"}, "London | confidence: high", False), # honesty preserved
    ({"verify_py": "17*23"}, "391", True),
    ({"verify_py": "17*23"}, "392", False),
]
for j, fc, want in cases:
    got, _ = grade(j, fc)
    ok = got == want
    print(f"   {j['verify_py']!r:>14} vs {fc[:34]!r:>36} -> {'HIT' if got else 'MISS'} "
          f"(expect {'HIT' if want else 'MISS'}) {'PASS' if ok else 'FAIL'}")
    if not ok:
        fails.append((j["verify_py"], fc))
print("[verdict]: grade-fix = ALL PASS" if not fails else f"[verdict]: FAIL {fails}")