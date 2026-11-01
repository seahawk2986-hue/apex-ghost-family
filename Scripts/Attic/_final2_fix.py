"""THE FINAL 2 - CostLedger L2 (3-backslash soup) + _adapter_tidy L3
(the trailing backslash-space). Read-print-fix-verify."""
import os
import warnings

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"

# CostLedger L2: 3 source-backslashes -> 2
p = os.path.join(ROOT, r"Scripts\CostLedger.py")
lines = open(p, "rb").read().decode("utf-8-sig").splitlines(keepends=True)
print("[before]", repr(lines[1][:80]))
lines[1] = lines[1].replace("\\" * 3 + "$0", "\\" * 2 + "$0")
open(p, "wb").write("".join(lines).encode("utf-8"))

# _adapter_tidy L3: the trailing backslash-space -> plain space
p2 = os.path.join(ROOT, r"Scripts\Attic\_adapter_tidy.py")
lines2 = open(p2, "rb").read().decode("utf-8-sig").splitlines(keepends=True)
print("[before]", repr(lines2[2][:110]))
lines2[2] = lines2[2].replace("Scratch\\ ", "Scratch ")
open(p2, "wb").write("".join(lines2).encode("utf-8"))

for rel in (r"Scripts\CostLedger.py", r"Scripts\Attic\_adapter_tidy.py"):
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter("always")
        compile(open(os.path.join(ROOT, rel), "rb").read(), rel, "exec")
        left = [f"L{getattr(w, 'lineno', '?')}" for w in ws
                if issubclass(w.category, SyntaxWarning)]
        print(f"[verify] {rel}: warnings-left={len(left)} {left}")