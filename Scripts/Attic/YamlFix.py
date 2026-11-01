"""YAML validation + rebuild: parse-before-push (the honest engineering)."""
import subprocess

YML = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\.github\workflows\apex-hub.yml"

CLEAN = """name: ApexHubWorker

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 */2 * * *'
  workflow_dispatch:

permissions:
  contents: read

jobs:
  hub-round:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - name: mining round
        run: python3 family/hub_round.py
      - name: grain home
        uses: actions/upload-artifact@v4
        with:
          name: apex-hub-harvest
          path: hub_round_result.json
"""

open(YML, "w", encoding="utf-8").write(CLEAN)

try:
    import yaml as _y
    d = _y.safe_load(CLEAN)
    print("YAML VALID: top keys:", list(d.keys()))
    print("triggers:", list(d.get(True, d.get("on", {})).keys()))
    print("steps:", [s.get("name", s.get("uses")) for s in
                    d["jobs"]["hub-round"]["steps"]])
except ImportError:
    r = subprocess.run([r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\apex_venv\Scripts\python",
                        "-m", "pip", "install", "pyyaml", "--quiet", "--disable-pip-version-check"],
                       capture_output=True, text=True, timeout=180)
    import yaml as _y
    d = _y.safe_load(CLEAN)
    print("pyyaml installed; YAML VALID:", list(d.keys()))

# push the validated rebuild → the shift fires NOW
def git(*a):
    r = subprocess.run(["git"] + list(a), capture_output=True, text=True,
                       timeout=200, cwd=ROOT__)
    return ((r.stdout or "") + (r.stderr or "")).strip()[-200:]

ROOT__ = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
git("add", ".github/workflows/apex-hub.yml")
print("commit:", git("commit", "-m", "hub: validated yaml (parse-checked before push)"))
print("push:", git("push"))