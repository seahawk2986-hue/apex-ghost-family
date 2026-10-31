"""
ApexInstaller - Autonomous program acquisition for Apex.

"Download any program he needs" - implemented via winget (Windows' official
package manager, signed manifests), supervised by the HostGuard governor.

THE ONE RESTRAINT (user directive 2026-10-30):
    Never do anything that can destabilize the host hardware:
    - payloads (installs) auto-abort when free RAM / CPU / disk breach limits
    - REBOOT, SHUTDOWN and killing the user's own applications are forbidden
      to autonomous action - those need a human (they are how a computer gets
      "crashed by an agent").
Everything else is permitted and logged.

Usage:
    python ApexInstaller.py ensure git.git 7zip.7zip   # install if missing
    python ApexInstaller.py status                     # hardware + tool status
"""

import json
import os
import shutil
import subprocess
import sys
import time

try:
    import psutil
except ImportError:
    psutil = None

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(ROOT, "Logs", "installer.log")
GUARD = os.path.join(ROOT, "Config", "HostGuard.json")

try:
    sys.path.insert(0, ROOT)
    from ApexMemory import ApexMemory
except Exception:
    ApexMemory = None


def _log(msg):
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def load_guard():
    try:
        with open(GUARD, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"min_free_ram_gb": 2.0, "max_cpu_percent": 85,
                "min_free_disk_gb": 5, "install_timeout_s": 900,
                "poll_interval_s": 5}


def hardware_ok(g):
    """Return (ok: bool, reason: str). None-safe when psutil is missing."""
    if psutil is None:
        return True, "psutil unavailable - governor blind"
    vm = psutil.virtual_memory()
    ram_free_gb = vm.available / (1024 ** 3)
    if ram_free_gb < g["min_free_ram_gb"]:
        return False, f"RAM guard: {ram_free_gb:.2f}GB free < {g['min_free_ram_gb']}GB"
    cpu = psutil.cpu_percent(interval=0.5)
    if cpu > g["max_cpu_percent"]:
        return False, f"CPU guard: {cpu:.0f}% > {g['max_cpu_percent']}%"
    d = os.path.splitdrive(ROOT)[0] + "\\"
    disk_free_gb = shutil.disk_usage(d).free / (1024 ** 3)
    if disk_free_gb < g["min_free_disk_gb"]:
        return False, f"Disk guard: {disk_free_gb:.1f}GB free < {g['min_free_disk_gb']}GB on {d}"
    return True, f"OK (ram {ram_free_gb:.2f}GB, cpu {cpu:.0f}%, disk {disk_free_gb:.1f}GB)"


# Forbidden autonomous actions - the hardware-destabilizing class.
FORBIDDEN_COMMANDS = ("shutdown", "restart-computer", "stop-computer",
                      "restart-service", "logoff", "/r /t", "-r -t")


def _forbidden(text):
    t = text.lower()
    return any(f in t for f in FORBIDDEN_COMMANDS)


def winget_available():
    return shutil.which("winget") is not None


def tool_installed(winget_id):
    """Best-effort check: is the winget package already present?"""
    exe_hint = winget_id.split(".")[-1].lower()
    if shutil.which(exe_hint):
        return True
    try:
        r = subprocess.run(["winget", "list", "--id", winget_id],
                           capture_output=True, text=True, timeout=60)
        return r.returncode == 0 and winget_id.lower() in r.stdout.lower()
    except Exception:
        return False


def install_tool(winget_id, scope="user"):
    """Install a program within the governor. Returns dict result."""
    if _forbidden(winget_id):
        return {"status": "REJECTED", "reason": "forbidden action class (hardware restraint)"}
    if not winget_available():
        return {"status": "FAILED", "reason": "winget not found on PATH"}

    if tool_installed(winget_id):
        _log(f"ensure {winget_id}: already present, no install needed")
        return {"status": "ALREADY_PRESENT", "id": winget_id}

    g = load_guard()
    ok, reason = hardware_ok(g)
    if not ok:
        _log(f"install {winget_id}: BLOCKED by governor - {reason}")
        return {"status": "BLOCKED", "reason": reason}

    cmd = ["winget", "install", "--id", winget_id, "--silent",
           "--accept-package-agreements", "--accept-source-agreements"]
    if scope == "user":
        cmd += ["--scope", "user"]
    _log(f"install {winget_id} starting ({reason})")
    t0 = time.time()
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, shell=False)
    except Exception as e:
        return {"status": "FAILED", "reason": f"spawn failed: {e}"}

    tail = []
    while True:
        line = ""
        try:
            line = proc.stdout.readline()
        except Exception:
            pass
        if line:
            tail.append(line.rstrip())
            tail = tail[-30:]
        if proc.poll() is not None:
            break
        if time.time() - t0 > g["install_timeout_s"]:
            proc.kill()
            msg = f"install {winget_id}: TIMEOUT after {g['install_timeout_s']}s - killed"
            _log(msg)
            return {"status": "TIMEOUT", "reason": msg, "tail": tail}
        ok, reason = hardware_ok(g)
        if not ok:
            proc.kill()
            msg = f"install {winget_id}: GOVERNOR ABORT - {reason}"
            _log(msg)
            try:
                if ApexMemory:
                    ApexMemory().record_event("error", msg)
            except Exception:
                pass
            return {"status": "ABORTED", "reason": reason, "tail": tail}
        time.sleep(g["poll_interval_s"])

    code = proc.returncode
    verified = tool_installed(winget_id)
    res = {"status": "INSTALLED" if verified and code == 0 else
           ("INSTALLED" if verified else f"EXIT_{code}"),
           "id": winget_id, "seconds": round(time.time() - t0, 1),
           "tail": tail[-8:], "verified": verified}
    _log(f"install {winget_id} finished: {res['status']}")
    try:
        if ApexMemory:
            m = ApexMemory()
            m.record_event("success" if res["status"] == "INSTALLED" else "error",
                           f"Installer: {res['status']} {winget_id} in {res['seconds']}s")
            if res["status"] == "INSTALLED":
                m.remember(f"Tool provisioned autonomously: {winget_id} (winget).", kind="lesson")
    except Exception:
        pass
    return res


def ensure(*ids):
    out = []
    for wid in ids:
        out.append(install_tool(wid))
    return out


def status():
    g = load_guard()
    ok, reason = hardware_ok(g)
    return {"hardware": reason, "guard_ok": ok,
            "winget": winget_available(), "guard": g}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    op = sys.argv[1]
    if op == "status":
        print(json.dumps(status(), indent=2))
    elif op == "ensure":
        if _forbidden(" ".join(sys.argv[2:])):
            print("REJECTED: forbidden action class (hardware restraint)")
            sys.exit(3)
        print(json.dumps(ensure(*sys.argv[2:]), indent=2, default=str))
    elif op in ("install",):
        print(json.dumps(install_tool(sys.argv[2]), indent=2, default=str))
    else:
        print(f"unknown op {op}; use status/ensure/install")
