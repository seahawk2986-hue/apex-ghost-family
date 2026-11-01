"""CostLedger L3: the last 3-backslash soup -> 2."""
import os
import warnings

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "Scripts", "CostLedger.py")
lines = open(p, "rb").read().decode("utf-8-sig").splitlines(keepends=True)
old = "\\" * 3 + "$0"
new = "\\" * 2 + "$0"
n = 0
for i, ln in enumerate(lines):
    if old in ln:
        lines[i] = ln.replace(old, new)
        n += 1
open(p, "wb").write("".join(lines).encode("utf-8"))
print(f"[fixed] {n} line(s)")
with warnings.catch_warnings(record=True) as ws:
    warnings.simplefilter("always")
    compile(open(p, "rb").read(), p, "exec")
    left = [getattr(w, "lineno", "?") for w in ws
            if issubclass(w.category, SyntaxWarning)]
    print(f"[verify] warnings-left={len(left)} {left}")