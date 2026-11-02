"""DockerWarden - keeps the sandbox host alive for the coding lane.

The 11/02 root cause: Docker Desktop's engine died under load mid-acceptance;
the seal layer honestly fail-closed (as designed). The warden makes the host
self-heal: if the docker pipe answers nothing, start Docker Desktop and wait
(bounded) for the engine, then report the 3-state truth. Scheduled every
15 min = the coding lane's sandbox host stops being a silent wall. $0, local.
"""
import io
import os
import subprocess
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def daemon_ok():
    r = subprocess.run(["docker", "info", "--format", "ok"],
                       capture_output=True, text=True, timeout=20)
    return r.returncode == 0 and "ok" in (r.stdout or "")


def main():
    if daemon_ok():
        print("[warden]: daemon alive")
        return
    dd = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if not os.path.isfile(dd):
        print("[warden]: Docker Desktop not found - honest red")
        return
    subprocess.Popen([dd])
    for i in range(24):
        time.sleep(5)
        if daemon_ok():
            print(f"[warden]: engine revived after {(i + 1) * 5}s")
            return
    print("[warden]: engine still down after 120s - honest red")


if __name__ == "__main__":
    main()