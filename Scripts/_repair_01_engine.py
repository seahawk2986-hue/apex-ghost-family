"""The repair-list step 1: the engine restore (the last-good v2) + the verify."""
import io
import shutil
import py_compile
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
GOOD = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Tools\v2_job_engine_shaperescue_v2.py"
LIVE = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
shutil.copyfile(GOOD, LIVE)
py_compile.compile(LIVE, doraise=True)
src = open(LIVE, encoding="utf-8").read()
tail_ok = 'return {"action": action, "args": args}' in src
fields_ok = "_ACTION_FIELDS" in src
print("[step 1 = RESTORED]: compile CLEAN | tail intact:", tail_ok,
      "| _ACTION_FIELDS:", fields_ok)

# step 2: the git rebind + sync
REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
import subprocess
git = lambda *c: subprocess.run(["git", *c], cwd=REPO, capture_output=True,
                                text=True, encoding="utf-8",
                                shell=True)
print("[step 2 = git]: current:", git("log", "--oneline", "-1").stdout.strip())
for c in (["git", "pull", "--rebase", "--autostash", "origin", "main"],
          ["git", "push"]):
    r = git(*c)
    print("  [git]", " ".join(c), "->", (r.stdout or r.stderr or "").strip()[-120:])
print("[step 3 = verify the engine's modules importable]")
sys.path.insert(0, r"C:\Users\seaha\Apex-Adapter")
import importlib.util
spec = importlib.util.spec_from_file_location("e_v", LIVE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print("[step 3 = import LIVE]: OK | normalize present:",
      hasattr(m, "normalize_tool_action"),
      "| shape_rescue present:", hasattr(m, "_shape_rescue"))