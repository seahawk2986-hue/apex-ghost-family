"""THE LAST 3 (the Attic-frozen instruments = to census-zero)."""
import os

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"


def linefix(rel, i, new):
    p = os.path.join(ROOT, rel)
    lines = open(p, encoding="utf-8-sig", errors="replace").readlines()
    old = lines[i - 1]
    lines[i - 1] = new
    open(p, "w", encoding="utf-8").writelines(lines)
    print(f"[fix] {rel} L{i}:")
    print(f"   - {old.rstrip()[:100]}")
    print(f"   + {new.rstrip()[:100]}")


# 1. DriveComplete: the stray bare return (L37) = deleted
linefix(r"Scripts\Attic\DriveComplete.py", 37, "")

# 2. YamlFix: the r-string was split mid-literal (the L43-45 rebuild)
linefix(r"Scripts\Attic\YamlFix.py", 43,
        '    r = subprocess.run([r"C:\\Users\\seaha\\Downloads\\Apex-'
        'With-Triggers-Fixed\\apex_venv\\Scripts\\python",\n')

# 3. _fix_v3b: the docstring = 4-quotes end = unbalanced (L5)
linefix(r"Scripts\Attic\_fix_v3b.py", 5,
        "tuple len!=2 in the S5-S8's P-feeds = slice.\"\"\"\n")

# verify all three compile now
import py_compile
for rel in (r"Scripts\Attic\DriveComplete.py",
            r"Scripts\Attic\YamlFix.py",
            r"Scripts\Attic\_fix_v3b.py"):
    try:
        py_compile.compile(os.path.join(ROOT, rel), doraise=True,
                           cfile=os.devnull)
        print(f"[compile-ok] {rel}")
    except Exception as e:
        print(f"[STILL-BAD] {rel}: {str(e)[:90]}")