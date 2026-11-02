"""THE ASCII-CURE for ApexEars.ps1: PS 5.1 reads a no-BOM .ps1 as ANSI, so
any non-ASCII char (the em-dash in the fallback-line) mangles into a parse
error that KILLS THE EARS AT BOOT. Replace every non-ASCII char with a safe
ASCII twin, write pure-ASCII, re-audit, and print the brace balance."""
import os

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
P = os.path.join(ROOT, "Scripts", "ApexEars.ps1")

raw = open(P, "rb").read()
if raw.startswith(b"\xef\xbb\xbf"):
    raw = raw[3:]
text = raw.decode("utf-8", "replace")

SWAP = {"—": "-", "–": "-", "…": "...", "“": '"', "”": '"',
        "‘": "'", "’": "'", "\xa0": " ", "•": "*", "·": "-"}

lines = text.splitlines()
print("[non-ascii rows found]:")
hit = False
for i, l in enumerate(lines, 1):
    bad = [c for c in l if ord(c) > 126]
    if bad:
        hit = True
        print(f"  L{i}: {[hex(ord(c)) for c in bad]}")
        for c in bad:
            l = l.replace(c, SWAP.get(c, "?"))
        lines[i - 1] = l
if not hit:
    print("  (none)")

out = "\n".join(lines) + "\n"
assert out.isascii(), "non-ascii survived the swap — aborting write"
open(P, "w", encoding="ascii", newline="\n").write(out)
print("[written]: pure-ASCII ApexEars.ps1")

bal = out.count("{") - out.count("}")
print(f"[brace balance]: {bal:+d}")