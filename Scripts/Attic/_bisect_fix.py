"""THE BISECT-CURE: find each SyntaxWarning's true line (the prefix-compile
bisection - the multi-line-string escapes only warn in whole-context),
then double the backslash on THAT line."""
import os
import warnings

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
FILES = (r"Scripts\CostLedger.py",
         r"Scripts\Attic\ApplyDrive.py",
         r"Scripts\Attic\_adapter_tidy.py")


def warn_lines(rel):
    p = os.path.join(ROOT, rel)
    raw = open(p, "rb").read()
    lines = raw.decode("utf-8-sig", "replace").splitlines(keepends=True)
    bad = []
    for i in range(1, len(lines) + 1):
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            try:
                compile("".join(lines[:i]), "<s>", "exec")
            except Exception:
                pass
        if any(issubclass(w.category, SyntaxWarning) for w in ws):
            bad.append(i)
    return p, lines, bad


for rel in FILES:
    p, lines, bad = warn_lines(rel)
    fix_at = sorted(set(bad))
    print(f"[{rel}] warning-onset lines: {fix_at[:10]}")
    for i in fix_at:
        ln = lines[i - 1]
        fixed = ln.replace("\\$", "\\\\$").replace("\\S", "\\\\S")
        if fixed != ln:
            lines[i - 1] = fixed
    open(p, "wb").write("".join(lines).encode("utf-8"))
    # re-verify by whole-file compile
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter("always")
        compile(open(p, "rb").read(), rel, "exec")
        left = [str(w.message)[:50] for w in ws
                if issubclass(w.category, SyntaxWarning)]
    print(f"   fixed {len(fix_at)} line(s) | warnings-left={len(left)} "
          f"{left[:2]}")