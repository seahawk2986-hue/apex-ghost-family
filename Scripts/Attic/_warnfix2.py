"""THE LAST-3 WARNING-SWEEP: escape-proof the remaining lines."""
import os
import warnings

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
FILES = (r"Scripts\CostLedger.py", r"Scripts\Attic\ApplyDrive.py",
         r"Scripts\Attic\_adapter_tidy.py")

for rel in FILES:
    p = os.path.join(ROOT, rel)
    lines = open(p, encoding="utf-8-sig", errors="replace").readlines()
    n = 0
    for i, ln in enumerate(lines):
        if "r'" in ln or 'r"' in ln:
            continue
        new = ln
        # the invalid-escape class: any lone \ before a letter/punct that
        # python flags = doubled (\\) - conservative: only \$ \S \D \W \d
        # \s \w (the regex-family) = the observed offenders
        for tok in ("\\$", "\\S", "\\s", "\\D", "\\d", "\\W", "\\w",
                    "\\-", "\\.", "\\{", "\\}"):
            new = new.replace(tok, "\\" + tok)
        if new != ln:
            lines[i] = new
            n += 1
    open(p, "w", encoding="utf-8").writelines(lines)
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter("always")
        compile(open(p, "rb").read(), rel, "exec")
        w = [str(x.message)[:60] for x in ws
             if issubclass(x.category, SyntaxWarning)]
        print(f"[done] {rel}: {n} line(s) | warnings-left={len(w)} {w}")