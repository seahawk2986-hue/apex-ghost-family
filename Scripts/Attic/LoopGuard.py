"""THE SELF-LOOP GUARD: the grain commits carry [skip ci] - only human
pushes trigger shifts. Honesty: the family doesn't run itself in circles."""
import json
import py_compile

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
YML = ROOT + r"\.github\workflows\apex-hub.yml"
yml = open(YML, encoding="utf-8").read()
if '[skip ci]' not in yml:
    yml = yml.replace(
        'git diff --cached --quiet || git commit -m "grain: hub harvest ${GITHUB_RUN_NUMBER} (manifest-digested)"',
        'git diff --cached --quiet || git commit -m "grain: hub harvest ${GITHUB_RUN_NUMBER} (manifest-digested) [skip ci]"')
    open(YML, "w", encoding="utf-8").write(yml)
    print("self-loop guard: [skip ci] armed")

import yaml as _y
_y.safe_load(yml)
print("yaml still-valid:" )
def git(*a):
    r = __import__("subprocess").run(["git"] + list(a), capture_output=True,
                                     text=True, timeout=200, cwd=ROOT)
    return ((r.stdout or "") + (r.stderr or "")).strip()[-200:]
git("add", ".github")
print("commit:", git("commit", "-m", "the self-loop guard: grain commits never re-trigger shifts [skip ci]"))
print("push:", git("push"))
print("THE FAMILY'S MACHINERY CANNOT RUN ITSELF IN CIRCLES - the honesty law reaches its own triggers")