import os
import re
import shutil

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"

# the think-wrap pattern, built at RUNTIME (the tag never appears as raw
# bytes in THIS file - the null-byte/artifact lesson of tonight's edits)
tag = "<" + "think"
close_tag = "</" + "think"
tag_pat = re.escape(tag) + r".*?" + re.escape(close_tag) + r"\s*"

# ---- 1. ApexMemory: the loop var is 'e' - 'txt' x3 are the bug ----
p = os.path.join(ROOT, "ApexMemory.py")
s = open(p, encoding="utf-8-sig").read()
s, n1 = re.subn(r"lessons\.append\(txt\[:180\]\)",
                'lessons.append(e.get("text", "")[:180])', s)
s, n2 = re.subn(r'or txt\.startswith\("GYM\["\)',
                'or (e.get("text", "")).startswith("GYM[")', s)
s, n3 = re.subn(r'1 if "gain" in txt else 0',
                '1 if "gain" in (e.get("text", "")) else 0', s)
open(p, "w", encoding="utf-8", newline="").write(s)
print(f"ApexMemory: txt fixes applied ({n1}+{n2}+{n3})")

# ---- 2. the LIVE job engine: 4 undefined names ----
p2 = os.path.join(AD, "v2_job_engine.py")
s2 = open(p2, encoding="utf-8-sig", errors="replace").read()
orig2 = s2
if "def strip_think(" not in s2:
    doc = ('The r1-class think-strip (the audited repair: the engine CALLED\n'
           'it at line 496 but never defined it - the delegated lane calls\n'
           'returned RAW wrapped text to the plan parser). Removes the think\n'
           'wrap atomically, case-insensitive.')
    st = ('def strip_think(text):\n'
          '    """' + doc + '"""\n'
          '    return re.sub(' + repr(tag_pat) +
          ', "", text or "",\n'
          '                  flags=re.S | re.I).strip()\n\n\n')
    anchor = s2.index("def _delegated_call(")
    s2 = s2[:anchor] + st + s2[anchor:]
    print("strip_think: defined (the engine had only the call)")
if "_evs = []" not in s2:
    before = s2
    s2 = s2.replace('    def ev(action, output="", **kw):\n',
                    '    _evs = []   # the audited repair: the events list '
                    'was NEVER initialized (NameError on every job)\n'
                    '    def ev(action, output="", **kw):\n', 1)
    print("_evs init: placed" if s2 != before else "_evs init: ANCHOR NOT FOUND")
s2_before = s2
s2 = re.sub(r"\bfor e in evs if e\.get\(.action.\) == .plan.\)",
            'for e in _evs if e.get("action") == "plan")', s2)
print("evs -> _evs:", "applied" if s2 != s2_before else "no change")
lane_before = s2
s2 = re.sub(r"decision, _ = lane\(sub_prompt, 300\)",
            'decision = _delegated_call("analyst", sub_prompt, "local", 300)',
            s2)
print("lane -> _delegated_call:", "applied" if s2 != lane_before
      else "no change (check verbatim)")
if s2 != orig2:
    open(p2, "w", encoding="utf-8", newline="").write(s2)
    print("job engine: written")

# ---- 3. the scratch-class one-shots still at the adapter root ----
moved = 0
for fn in ("five_rounds_reassess.py", "full_goal_5x.py",
           "perfection_loop.py", "three_round_assess.py"):
    src = os.path.join(AD, fn)
    dst = os.path.join(AD, "Scratch", fn)
    if os.path.exists(src):
        try:
            shutil.move(src, dst)
            moved += 1
        except Exception as e:
            print("move failed:", fn, str(e)[:50])
print(f"one-shots moved: {moved}/4")