"""THE FORENSIC: find any remaining invalid-escape in CostLedger - the
ast-level token scan (no guessing)."""
import io
import os
import re
import tokenize
import warnings

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "Scripts", "CostLedger.py")
raw = open(p, "rb").read().decode("utf-8-sig")
src = raw

# 1. the raw byte-grep: every backslash-dollar with 6 chars before
for m in re.finditer(r".{0,20}\\\$.{0,10}", src):
    ln = src[:m.start()].count("\n") + 1
    print(f"byte-grep L{ln}: {m.group(0)!r}"[:120])

# 2. the tokenizer: exact STRING tokens still containing an odd lone \$
try:
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        pass
except SyntaxError as e:
    print("tokenize SyntaxError:", e)
except Exception:
    pass

# 3. the honest compile-line attribution: per-prefix bisection with lineno
with warnings.catch_warnings(record=True) as ws:
    warnings.simplefilter("always")
    compile(open(p, "rb").read(), p, "exec")
    for w in ws:
        print("warning:", getattr(w, "lineno", "?"),
              getattr(w, "filename", "?"), str(w.message)[:40])