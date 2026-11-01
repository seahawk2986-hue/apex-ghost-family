"""CostLedger: THE deterministic line-level cure.
Every line containing backslash+dollar: replace exactly that 2-char
sequence with 2-backslashes+dollar (an idempotent, safe doubling that
also fixes any odd runs: 1->2, 3->4? no - handled: runs>1 first
collapsed to 1, then doubled - canonical 2 always)."""
import os
import warnings

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "Scripts", "CostLedger.py")
raw = open(p, "rb").read().decode("utf-8-sig")
BS = chr(92)
D = "$"
line_fixed = 0
out_lines = []
for i, ln in enumerate(raw.splitlines(keepends=True), 1):
    if (BS + D) in ln:
        # collapse every backslash-run before $ to exactly one, then double
        j = 0
        buf = []
        while j < len(ln):
            if ln[j] == BS and j + 1 < len(ln) and ln[j + 1] == D:
                buf.append(BS * 2 + D)          # the canonical \\$
                j += 2
                continue
            if ln[j] == BS:
                k = j
                while k < len(ln) and ln[k] == BS:
                    k += 1
                run = k - j
                if k < len(ln) and ln[k] == D:
                    buf.append(BS * 2 + D)
                    j = k + 1
                    continue
                buf.append(BS * run)            # non-$ runs untouched
                j = k
                continue
            buf.append(ln[j])
            j += 1
        if "".join(buf) != ln:
            line_fixed += 1
            print(f"L{i}: {ln.strip()[:60]!r}  ->  {''.join(buf).strip()[:60]!r}")
        out_lines.append("".join(buf))
    else:
        out_lines.append(ln)
open(p, "wb").write("".join(out_lines).encode("utf-8"))
print("lines-fixed:", line_fixed)
with warnings.catch_warnings(record=True) as ws:
    warnings.simplefilter("always")
    compile(open(p, "rb").read(), p, "exec")
    left = [getattr(w, "lineno", "?") for w in ws
            if issubclass(w.category, SyntaxWarning)]
    print("warnings-left:", len(left), left)