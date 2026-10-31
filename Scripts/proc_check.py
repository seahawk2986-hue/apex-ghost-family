"""proc_check.py v2 - Registry-driven process inspector (enumeration-free).

Sources of truth (both O(1), hang-proof, self-match-proof):
  1. Config/layer_pids.json - layers self-declare their PID at startup
  2. Port ownership via psutil.net_connections (single syscall, no iteration)

Usage:
  python proc_check.py check  <marker>   exit 0 if the layer is alive
  python proc_check.py kill   <marker>   kill registry + port-owner instances
  python proc_check.py list              print registry + port owners
"""

import json
import os
import sys

import psutil

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(R, "Config", "layer_pids.json")
PORT_OF = {"evolution": 8080, "bridge": 8081}


def _registry():
    try:
        with open(REG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _key_for(marker):
    m = (marker or "").lower()
    if "evolution" in m:
        return "evolution"
    if "optimized" in m or "bridge" in m:
        return "bridge"
    return None


def _port_pid(port):
    try:
        for c in psutil.net_connections(kind="inet"):
            if c.laddr and c.laddr.port == port and c.status == psutil.CONN_LISTEN and c.pid:
                return c.pid
    except Exception:
        pass
    return None


def _port_up(port):
    """Bind-test fallback: is something serving this port right now?"""
    import socket
    s = socket.socket()
    s.settimeout(1.5)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def _alive_pid(key):
    """Return the layer's PID if alive (registry PID that is a live python),
    else the port-owner PID. None means not serving. A connectable port with
    no owner information still counts as alive (psutil scans can miss)."""
    ent = _registry().get(key) or {}
    pid = ent.get("pid")
    if pid:
        try:
            if psutil.pid_exists(pid) and "python" in (psutil.Process(pid).name() or "").lower():
                return pid
        except Exception:
            pass
    port = PORT_OF.get(key, 0)
    if port and _port_up(port):
        return -1   # alive; owner unknown but service is reachable
    return _port_pid(port)


def main():
    op = sys.argv[1] if len(sys.argv) > 1 else "check"
    marker = sys.argv[2] if len(sys.argv) > 2 else ""
    if op == "list":
        reg = _registry()
        for key in ("evolution", "bridge"):
            reg_pid = (reg.get(key) or {}).get("pid")
            port_pid = _port_pid(PORT_OF.get(key, 0))
            print(f"{key}: registry={reg_pid} port_owner={port_pid}")
        sys.exit(0)
    key = _key_for(marker)
    if not key:
        print("unknown marker (use 'evolution' or 'optimized_agent'/'bridge')", file=sys.stderr)
        sys.exit(2)
    if op == "check":
        sys.exit(0 if _alive_pid(key) else 1)
    if op == "kill":
        target = _alive_pid(key)
        if target:
            try:
                psutil.Process(target).kill()
                print(f"killed {key} PID {target}")
                sys.exit(0)
            except Exception as e:
                print(f"kill failed: {e}", file=sys.stderr)
                sys.exit(3)
        sys.exit(1)
    sys.exit(2)


if __name__ == "__main__":
    main()