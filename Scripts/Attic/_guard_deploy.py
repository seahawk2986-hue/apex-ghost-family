"""The audited fix: DeploySwarm's module-level runner (lines 84+) spawns
children AT IMPORT TIME - wrapped under if __name__ == "__main__". The
transform is scripted (exact-indent proof), compile-verified, and gated by
the import-no-spawn test."""
import py_compile
import re

P = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\DeploySwarm.py"
src = open(P, encoding="utf-8-sig").read()
assert 'if __name__ == "__main__":' not in src, "already guarded"
lines = src.splitlines()
idx = next(i for i, l in enumerate(lines)
           if l.startswith("# ELASTIC FLEET"))
head = lines[:idx]
tail = lines[idx:]
guarded = ['if __name__ == "__main__":      # THE FIX (audited): the runner '
           '- spawn + the grain line - must not fire at import time']
for l in tail:
    guarded.append(("    " + l) if l.strip() else l)
out = "\n".join(head + guarded) + "\n"
with open(P, "w", encoding="utf-8", newline="") as f:
    f.write(out)
py_compile.compile(P, doraise=True)
print("transformed + COMPILE OK:", len(out.splitlines()), "lines (guard at", idx + 1, ")")
# verify: exactly one guard, the tail indented, no bare Popen at module level
src2 = open(P, encoding="utf-8-sig").read()
assert src2.count('if __name__ == "__main__":') == 1
bare = [l for l in src2.splitlines()
        if re.match(r"\s*subprocess\.Popen", l) and not l.startswith("    ")]
assert not bare, bare
print("verified: single guard, no module-level Popen")