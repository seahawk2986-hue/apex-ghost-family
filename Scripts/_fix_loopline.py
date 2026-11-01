"""THE LOOP-LINE FIXER (by index, byte-exact — the ghost-proof method):
lines 183-190 = the mangled weakest-construct -> the clean two-line form."""
import os

p = os.path.join(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed",
                 "Scripts", "Apex10Loop.py")
lines = open(p, encoding="utf-8").readlines()
# find the mangled start
start = next(i for i, ln in enumerate(lines)
             if 'weakest = min((r for r in before' in ln)
end = next(i for i in range(start, start + 12)
           if 'a = act(pick)' in lines[i]) + 1
lines[start:end] = [
    '    weakest = min((r for r in before\n',
    '                   if r["cap"] not in ("earning", "founder")),\n',
    '                  key=lambda r: r["score"], default=None)\n',
    '    a = act(pick)  # the ACTION-ids are what act() consumes\n',
]
open(p, "w", encoding="utf-8", newline="\n").writelines(lines)
print(f"[fix-loop] lines {start + 1}-{end} rewritten (the clean form)")