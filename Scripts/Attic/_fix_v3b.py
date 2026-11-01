"""THE DESIGNV3 3-TUPLE FLATTENER v2: EVERY 3+-tuple in the P-calls'
lists -> 2 (the unpack's cure, general): the n-status-note triples keep
n+status; the note = appended to the status?? NO: the 3-tuples with a
3rd = the note's = flatten to (n, st). The general: for each list-item
tuple len!=2 in the S5-S8's P-feeds = slice."""
import re

p = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\DesignV3.py"
t = open(p, encoding="utf-8").read()
# the general: (x, y, z) -> (x, y) INSIDE the catalog sections' lines 55-120
# (the safe: only the lines between def-P and the HTML = the P-call tuples)
lines = t.splitlines()
out = []
for ln in lines:
    if ln.strip().startswith(('("', "('", '        ("')):
        # a tuple-item line: find ALL (a, b, c) shapes -> keep (a, b)
        ln = re.sub(r"\((\"[^\"]+\"),\s*(\"[^\"]+\"),\s*[^)]+\)",
                    r"\1, \2", ln)
    out.append(ln)
open(p, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("[fix-v3-general] the 3-tuples flattened (the regex-cure)")