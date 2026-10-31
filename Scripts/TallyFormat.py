"""Tally format: $ followed by the number - exactly that, nothing else."""
P = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\ApexChatPage.html"
src = open(P, encoding="utf-8-sig").read()
n = 0
old = "el.innerHTML = '$ ' + v + '<small>earned</small>';"
new = "el.textContent = '$ ' + v;"
if old in src:
    src = src.replace(old, new, 1)
    n += 1
open(P, "w", encoding="utf-8-sig").write(src)
print("tally format simplified: $ <number> only (patched:", n, ")")