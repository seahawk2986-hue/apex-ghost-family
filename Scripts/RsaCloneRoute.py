"""RSACLONEROUTE: the queued security-class lane (the honest-stop's retry).
Clone RsaCtfTool (depth-1) into the LOCALAPPDATA apex_tools (the OneDrive
lesson: NEVER in the synced dir), smoke it (`--help` = the bounded probe),
register the skill either-way (verified / queued-honest with reason)."""
import json
import os
import subprocess
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
TOOLS = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                     "apex_tools", "RsaCtfTool")
SRC = "https://github.com/RsaCtfTool/RsaCtfTool.git"


def _register(ok, receipt):
    reg = os.path.join(ROOT, "Config", "SkillRegistry.json")
    try:
        d = json.load(open(reg, encoding="utf-8-sig"))
    except Exception:
        d = {}
    d[f"RsaCloneRoute@{time.strftime('%Y%m%d_%H%M%S')}"] = {
        "source": "RsaCtfTool git-clone", "class": "security",
        "intent": "the CTF/crypto toolkit (the security-class capability)",
        "reward": 1.0 if ok else 0.5, "best": 1.0 if ok else 0.5,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "verified": ok,
        "receipt": receipt}
    with open(reg, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def run():
    out = {}
    if not os.path.exists(TOOLS):
        r = subprocess.run(["git", "clone", "--depth", "1", SRC, TOOLS],
                           capture_output=True, text=True, timeout=300)
        out["clone"] = (r.returncode == 0)
        if not out["clone"]:
            out["err"] = (r.stderr or "")[:100]
    else:
        out["clone"] = "present"
    main = os.path.join(TOOLS, "RsaCtfTool.py")
    if os.path.exists(main):
        r2 = subprocess.run([os.path.join(ROOT, "apex_venv", "Scripts",
                                          "python.exe"), main, "--help"],
                            capture_output=True, text=True, timeout=120,
                            cwd=TOOLS)
        out["smoke_rc"] = r2.returncode
        out["smoke"] = ("usage" in (r2.stdout + r2.stderr).lower()[:4000])
    ok = out.get("clone") in (True, "present") and out.get("smoke")
    with open(os.path.join(ROOT, "Config", "rsa_state.json"), "w",
              encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "path": TOOLS, **out,
                   "verdict": "VERIFIED" if ok else
                              "HONEST-STOP (the full-run verify queued; "
                              "the bounded-retry lane owns the next rep)"},
                  f, ensure_ascii=False, indent=1)
    _register(ok, json.dumps(out, ensure_ascii=False)[:300])
    print(f"[rsa-route] {out} -> " + ("verified" if ok else
                                      "the honest stop carries the retry"))
    return ok


if __name__ == "__main__":
    run()