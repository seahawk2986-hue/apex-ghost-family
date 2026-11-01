"""THE DESIGNV3-CURE (self-contained): the 4 replaces direct."""
p = (r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts"
     r"\DesignV3.py")
t2 = open(p, encoding="utf-8").read()
for old, new in [
    ("for i, (n, st, note) in enumerate([\n        (\"the secure-checkout-label\"",
     "for i, it in enumerate([\n        (\"the secure-checkout-label\""),
    ("for i, (n, st) in enumerate([(\"the skip-link\"",
     "for i, it in enumerate([(\"the skip-link\""),
    ("for i, (n, st, note) in enumerate([\n        (\"the title+keywords\"",
     "for i, it in enumerate([\n        (\"the title+keywords\""),
    ("P(64 + i, n, S6, st, note)",
     "P(64 + i, it[0], S6, it[1], it[2] if len(it) > 2 else '')"),
    ('P(76 + i, n if isinstance(n, str) else n[0], S7, "applied")',
     "P(76 + i, it if isinstance(it, str) else it[0], S7, 'applied')"),
]:
    if old in t2:
        t2 = t2.replace(old, new, 1)
        print(f"[cure-f] {old[:36]}")
    else:
        print(f"[cure-f] {old[:36]} NOT-FOUND")
open(p, "w", encoding="utf-8", newline="\n").write(t2)
print("[cure-f] done")