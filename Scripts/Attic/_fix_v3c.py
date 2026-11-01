"""THE DESIGNV3's TOLERANT-UNPACK CURE: the catalog-loops take ANY
tuple-length (the 2/3 honest mix = the note-optional)."""
import re

p = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\DesignV3.py"
t = open(p, encoding="utf-8").read()
# the 3-var unpacks -> the tolerant form
t = t.replace(
    "    for i, (n, st, note) in enumerate([",
    "    for i, it in enumerate([")
t = t.replace(
    "        (\"the secure-checkout-label\", \"applied\", \"the Stripe-via-Polar microcopy\")",
    "        (\"the secure-checkout-label\", \"applied\")")
# inject the note-extraction where the 3-loops were (the generic): after
# each such enumerate-block's header-line, the loop's P-call = n,st[,note]
t = re.sub(r"    for i, it in enumerate\(\[(\s*\n(?:.*\n)*?)(\s*\]\)\s*:\n)\s*P\((\d+[^\n]*)\n\s*P\(",
           r"    for i, it in enumerate([\1\2    P(\3", t) if False else t
# the robust-general rewrite: 3 P-loops -> the tolerant-P(*it)
t = t.replace("P(31 + i, n, S4, st, note)",
              "P(31 + i, it[0], S4, it[1], it[2] if len(it) > 2 else '')")
t = t.replace("P(51 + i, n, S5, st)",
              "P(51 + i, it[0], S5, it[1], it[2] if len(it) > 2 else '')")
t = t.replace("P(76 + i, n if isinstance(n, str) else n[0], S7, \"applied\")",
              "P(76 + i, it[0] if isinstance(it, tuple) else it, S7, 'applied', it[1] if isinstance(it, tuple) and len(it) > 1 else '')")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("[fix-v3c] the tolerant-unpacks installed (the 3 P-loops)")