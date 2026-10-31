"""ApexVersions - Rolling version history + one-command rollback for evolutions."""

import os
import shutil
import time

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = 10


def _vdir(fn):
    return os.path.join(R, "Config", "versions", fn)


def snapshot(fn, msg=None):
    """Capture the just-written file into Config/versions/<fn>/<ts><ext>,
    plus (once) a real git history so every evolution is diffable."""
    src = os.path.join(R, fn)
    if not os.path.exists(src):
        return None
    d = _vdir(fn)
    os.makedirs(d, exist_ok=True)
    base, ext = os.path.splitext(fn)
    dst = os.path.join(d, time.strftime("%Y%m%d_%H%M%S") + (ext or ".py"))
    try:
        shutil.copy2(src, dst)
        snaps = sorted(os.listdir(d))
        if len(snaps) > CAP:
            for old in snaps[:-CAP]:
                try:
                    os.remove(os.path.join(d, old))
                except OSError:
                    pass
    except Exception:
        pass
    # REAL version history: git commit per evolution (diffable, revertable).
    try:
        import subprocess
        gdir = os.path.join(R, ".git")
        gignore = os.path.join(R, ".gitignore")
        if not os.path.exists(gdir):
            # Firewall FIRST: never let secrets into history.
            if not os.path.exists(gignore):
                with open(gignore, "w", encoding="ascii") as f:
                    f.write(".env\nLogs/\nwatchdog.lock\n__pycache__/\nspeculative_test_*\n*.tmp\n")
            subprocess.run(["git", "-C", R, "init"], capture_output=True, timeout=15)
            subprocess.run(["git", "-C", R, "config", "user.name", "Apex"],
                           capture_output=True, timeout=10)
            subprocess.run(["git", "-C", R, "config", "user.email", "apex@local"],
                           capture_output=True, timeout=10)
        subprocess.run(["git", "-C", R, "add", "-A"], capture_output=True, timeout=60)
        subprocess.run(["git", "-C", R, "commit", "-m", msg or f"evolution: {fn}"],
                       capture_output=True, timeout=30)
    except Exception:
        pass
    return dst


def list_versions(fn):
    try:
        return sorted(os.listdir(_vdir(fn)))
    except Exception:
        return []


def rollback(fn, when=None):
    """Restore the latest (or named) snapshot; archives current state first."""
    d = _vdir(fn)
    snaps = list_versions(fn)
    if not snaps:
        return None
    target = when if when in snaps else snaps[-1]
    src = os.path.join(d, target)
    cur = os.path.join(R, fn)
    base, ext = os.path.splitext(fn)
    if os.path.exists(cur):
        shutil.copy2(cur, os.path.join(d, "pre_rollback_" + time.strftime("%Y%m%d_%H%M%S") + (ext or ".py")))
    shutil.copy2(src, cur)
    return target


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "rollback":
        print("rolled back to:", rollback(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
    else:
        print("usage: ApexVersions.py rollback <filename> [timestamp]  | call snapshot() from heal")