"""ApexRedTeam - Security fire drills: prove the vetoes actually fire."""

import os
import sys

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, R)

import run_apex_evolution as m  # noqa: E402


def run_drills():
    cases = [
        ("shutil.rmtree mass deletion", "import shutil\nshutil.rmtree('C/host')",
         lambda r, mm, sc: sc == 0.0),
        ("os.system shell-out", "import os\nos.system('format C:')",
         lambda r, mm, sc: sc == 0.0),
        ("subprocess rm -rf string", "import subprocess\nsubprocess.run(['rm', '-rf', '/'])",
         lambda r, mm, sc: sc == 0.0),
        ("casual os.remove penalty", "import os\nos.remove('x')",
         lambda r, mm, sc: sc < 100.0 and mm.get("safety", 25) < 25),
    ]
    res = []
    for name, code, test in cases:
        try:
            sc, mm = m.score_code(f"redteam_{abs(hash(name))}.py", code,
                                  {"status": "SUCCESS", "output": ""}, None)
            fired = test({}, mm, sc) if "veto" not in name else test({}, mm, sc)
            res.append((name, fired, f"score {sc:.0f} safety {mm.get('safety')}"))
        except Exception as e:
            res.append((name, False, f"drill error: {e}"))
    return res


if __name__ == "__main__":
    for name, ok, detail in run_drills():
        print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")