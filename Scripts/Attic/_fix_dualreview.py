"""THE DUALREVIEW STRIP-FIXER: the corrupted strip-line can't be matched by
eye (the tag-literal renders invisibly in reads) - fix by LINE INDEX, exact:
find the `_re.sub(` line and rewrite it to the safe think-strip construct."""
import os

p = os.path.join(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed",
                 "Scripts", "DualReview.py")
lines = open(p, encoding="utf-8").readlines()
fixed = 0
for i, ln in enumerate(lines):
    if "_re.sub(" in ln and "flags=" in ln:
        lines[i] = ('            t = _re.sub(_re.escape("<" + "think") '
                    '+ r".*?" + _re.escape("</" + "think")\n'
                    '                        + r"\\s*", "", r,\n'
                    '                        flags=_re.S | _re.I)\n')
        fixed += 1
with open(p, "w", encoding="utf-8", newline="\n") as f:
    f.writelines(lines)
print(f"[fix-dualreview] rewritten {fixed} strip-line(s) by index")
print("[fix-dualreview] the signature fix (delay=6.0) already landed")