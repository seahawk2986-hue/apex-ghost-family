"""CostLedger: NORMALIZE every backslash-run around $ and S to the
canonical \\ (2 source-backslashes = one rendered). Regex, whole file."""
import os
import re
import warnings

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "Scripts", "CostLedger.py")
src = open(p, "rb").read().decode("utf-8-sig")

# any run of 1..N backslashes immediately before $ or S (word) = -> exactly 2,
# EXCEPT a lone backslash preceding a slash-backslash pair chain (leave the
# escaped-backslash case: \\\$ = \\ + \$ -> the run-normalizer covers it
# since runs count ALL consecutive backslashes).
src2 = re.sub(r"(\\+)(" + re.escape("$") + r")", "\\\\" + "$", src)
src2 = re.sub(r"(\\+)S", "\\\\" + "S", src2)
open(p, "wb").write(src2.encode("utf-8"))

with warnings.catch_warnings(record=True) as ws:
    warnings.simplefilter("always")
    compile(open(p, "rb").read(), p, "exec")
    left = [f"L{getattr(w, 'lineno', '?')}: {str(w.message)[:30]}"
            for w in ws if issubclass(w.category, SyntaxWarning)]
    print(f"[verify] warnings-left={len(left)} {left}")