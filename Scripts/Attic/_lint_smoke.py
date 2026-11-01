"""THE LINT-STAGE SMOKE: ruff's real verdict on a bad + a good file."""
import os
import sys
import tempfile

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import QualityGate as QG

t = tempfile.mkdtemp()
bad = os.path.join(t, "bad.py")
good = os.path.join(t, "good.py")
open(bad, "w").write("import os\nimport json\nx = 1\n")
open(good, "w").write("import json\n\ndef f(d):\n    return json.dumps(d)\n")
r1 = QG.stage_lint([bad], t)
r2 = QG.stage_lint([good], t)
ok = (r1["ok"] is False and r1.get("tool") == "ruff" and r2["ok"] is True)
print(f"[lint-smoke] bad->{str(r1['ok'])} ({r1.get('note', '')[:70]})")
print(f"[lint-smoke] good->{r2['ok']} | VERDICT: {'PASS' if ok else 'CHECK'}")