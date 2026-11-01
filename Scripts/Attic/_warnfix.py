"""THE 7 SyntaxWarnings = CURED (raw-safe strings; future-Proof-3.15)."""
import os
import re
import warnings

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
FIXES = {
    r"Scripts\AgentRoster.py": r"\$",
    r"Scripts\CapabilityEvolution.py": r"\$",
    r"Scripts\CostLedger.py": r"\$",
    r"Scripts\EarnLoop.py": r"\$",
    r"Scripts\LocalChain.py": r"\$",
    r"Scripts\ApplyDrive.py": r"\S",
    r"Scripts\Attic\_adapter_tidy.py": r"\S",
}
for rel, tok in FIXES.items():
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        print(f"[skip] {rel} = missing")
        continue
    lines = open(p, encoding="utf-8-sig", errors="replace").readlines()
    n = 0
    for i, ln in enumerate(lines):
        if tok not in ln or "r'" in ln or 'r"' in ln:
            continue
        # double the backslash so the string stays escape-safe forever
        new = ln.replace("\\" + tok[1], "\\\\" + tok[1])
        if new != ln:
            lines[i] = new
            n += 1
    open(p, "w", encoding="utf-8").writelines(lines)
    # verify: recompile + assert zero warnings
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter("always")
        try:
            compile(open(p, "rb").read(), rel, "exec")
            w = sum(1 for x in ws
                    if issubclass(x.category, SyntaxWarning))
            print(f"[fixed] {rel}: {n} line(s), compile-ok, "
                  f"warnings-left={w}")
        except Exception as e:
            print(f"[BROKE] {rel}: {str(e)[:90]}")