"""YamlFix v2: raw-string paths + validate + push (the clean pass)."""
import subprocess

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
YML = ROOT + r"\.github\workflows\apex-hub.yml"
PY = ROOT + r"\apex_venv\Scripts\python.exe"
import yaml as _y
try:
    d = _y.safe_load(open(YML, encoding="utf-8").read())
    print("YAML VALID:", list(d.keys()))
except ImportError:
    subprocess.run([PY, "-m", "pip", "install", "pyyaml", "--quiet",
                    "--disable-pip-version-check"], timeout=180)
    d = _y.safe_load(open(YML, encoding="utf-8").read())
    print("pyyaml installed; YAML VALID:", list(d.keys()))


def git(*a):
    r = subprocess.run(["git"] + list(a), capture_output=True, text=True,
                       timeout=200, cwd=ROOT)
    return ((r.stdout or "") + (r.stderr or "")).strip()[-200:]


git("add", ".github/workflows/apex-hub.yml")
print("commit:", git("commit", "-m", "hub: yaml validated locally (parse-check discipline)"))
print("push:", git("push"))