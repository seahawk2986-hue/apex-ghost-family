# the close-out: kill the OpenCode desktop + the CLI server (the = the founder-approved)
import io
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
for exe in ("OpenCode.exe", "opencode-cli.exe"):
    r = subprocess.run(["taskkill", "/F", "/IM", exe, "/T"],
                       capture_output=True, text=True)
    print(f"[kill {exe}]:", (r.stdout or r.stderr).strip()[:100])
print("[done]: OpenCode fully closed — reopen and say 'resume the repair list'")