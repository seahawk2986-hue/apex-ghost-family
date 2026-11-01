"""THE DESIGNV3 3-TUPLE FLATTENER (byte-safe by line-index): the S5's
last entry's 3-tuple -> 2 (the unpack's honest fix)."""
p = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\DesignV3.py"
lines = open(p, encoding="utf-8").readlines()
i = next(i for i, ln in enumerate(lines) if "reduced-motion" in ln)
lines[i] = '        ("reduced-motion", "not-applicable")]):\n'
open(p, "w", encoding="utf-8", newline="\n").writelines(lines)
print(f"[fix-v3] line {i + 1} flattened")