"""THE FINAL 4 FIXES - exact bytes, then zero-warnings-or-say-so."""
import os
import warnings

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"


def sub_line(rel, lineno, old, new):
    p = os.path.join(ROOT, rel)
    lines = open(p, "rb").read().decode("utf-8-sig").splitlines(keepends=True)
    i = lineno - 1
    if old not in lines[i]:
        print(f"[MISS] {rel} L{lineno}: pattern absent: {repr(lines[i][:90])}")
        return False
    lines[i] = lines[i].replace(old, new)
    open(p, "wb").write("".join(lines).encode("utf-8"))
    print(f"[fix] {rel} L{lineno}")
    return True


# 1. CostLedger L2: 6-backslash-soup + $0 -> the clean \\$0
sub_line(r"Scripts\CostLedger.py", 2,
         "\\" * 6 + "$0", "\\" * 2 + "$0")

# 2. ApplyDrive L55: the raw-string-cannot-end-in-backslash bug =
#    forward-slash the sys.path (windows-valid, zero escapes)
p = os.path.join(ROOT, r"Scripts\Attic\ApplyDrive.py")
lines = open(p, "rb").read().decode("utf-8-sig").splitlines(keepends=True)
line = lines[54]
print("[before] ApplyDrive L55:", repr(line[:120]))
new = '                 "import sys; sys.path.insert(0, \' + ROOT.replace(chr(92), chr(47)) + \'/Scripts\');"\n'
lines[54] = new
open(p, "wb").write("".join(lines).encode("utf-8"))

# 3. _adapter_tidy L3 + L36: the backslash-soup before Scratch -> \\ (one rendered)
sub_line(r"Scripts\Attic\_adapter_tidy.py", 3,
         "\\" * 3 + "Scratch", "\\" * 2 + "Scratch")
sub_line(r"Scripts\Attic\_adapter_tidy.py", 36,
         "\\" * 5 + "Scratch", "\\" * 2 + "Scratch")

# verify
for rel in (r"Scripts\CostLedger.py", r"Scripts\Attic\ApplyDrive.py",
            r"Scripts\Attic\_adapter_tidy.py"):
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter("always")
        try:
            compile(open(os.path.join(ROOT, rel), "rb").read(), rel, "exec")
        except Exception as e:
            print(f"[COMPILE-FAIL] {rel}: {str(e)[:90]}")
            continue
        left = [f"L{getattr(w, 'lineno', '?')}: {str(w.message)[:40]}"
                for w in ws if issubclass(w.category, SyntaxWarning)]
        print(f"[verify] {rel}: warnings-left={len(left)} {left}")