import re

# 1. ApexGym: the STAGE import + the honest speaker
p = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\ApexGym.py"
src = open(p, encoding="utf-8-sig").read()
if "from SkillLibrary import STAGE" not in src:
    src = src.replace("import os\n",
                      "import os\nfrom SkillLibrary import STAGE   # "
                      "the audited repair (undefined name)\n", 1)
    open(p, "w", encoding="utf-8", newline="").write(src)
    print("ApexGym: STAGE import added")
src = open(p, encoding="utf-8-sig").read()
if "def Speak(" not in src:
    speak_code = (
        "def Speak(text):\n"
        '    """The honest speaker (the audited repair - Speak existed\n'
        "    NOWHERE, so the milestone pulse silently died in the except):\n"
        "    the milestone is SPOKEN into the print + the log row; the voice\n"
        "    hardware is out, the founder briefs lane is the real channel.\"\"\"\n"
        '    print("[speak] " + str(text))\n'
        "\n\n"
        "def log_row(")
    src = src.replace("def log_row(", speak_code, 1)
    open(p, "w", encoding="utf-8", newline="").write(src)
    print("ApexGym: Speak defined")

# 2. InitiativeLoop: the uuid import
p2 = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\InitiativeLoop.py"
s2 = open(p2, encoding="utf-8-sig").read()
if "import uuid" not in s2:
    s2 = s2.replace("import time\n",
                    "import time\nimport uuid   # the audited repair "
                    "(undefined name)\n", 1)
    open(p2, "w", encoding="utf-8", newline="").write(s2)
    print("InitiativeLoop: uuid import added")

# 3. RunROI: the dead stub block (never executed, pyflakes-flagged)
p3 = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\RunROI.py"
s3 = open(p3, encoding="utf-8-sig").read()
dead = re.search(
    r"        for mode, key in \(\(\"archive_pull\", \"gfi\"\), "
    r"\(\"upgrader\", \"curriculum\"\)\):\n"
    r"            gain = a\[key\] - b\[key\]\n"
    r"            if any\(cmd\[1\]\.lower\(\)\.endswith\(mode\.split\('_'\)\[0\] "
    r"\+ \"\*\.py\"\)\n"
    r"                   for _cmd in \[green\] if False\):\n"
    r"                pass\n", s3)
if dead:
    s3 = s3[:dead.start()] + s3[dead.end():]
    open(p3, "w", encoding="utf-8", newline="").write(s3)
    print("RunROI: the dead undefined-cmd stub removed")
else:
    print("RunROI: the stub pattern not found (checking later)")

# 4. SwarmOrchestrator: the dead self._lane_reqs
p4 = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\SwarmOrchestrator.py"
s4 = open(p4, encoding="utf-8-sig").read()
s4, n_sub = re.subn(
    r'int\(e\.get\("reqs", 0\)\) \+ max\(1, self\._lane_reqs if False else 1\)',
    'int(e.get("reqs", 0)) + 1', s4)
open(p4, "w", encoding="utf-8", newline="").write(s4)
print("SwarmOrchestrator: dead self-lane-reqs cleaned (n=%d)" % n_sub)
print("DONE")