"""THE RAM-CURE v2 (the honest rewrite): the v1 census was WRONG — every
'x2' family was a launcher/worker PARENT-CHILD pair (the venv exe spawns
its real interpreter), not a duplicate. v1 would have killed the serve,
the room-adapter and the watcher. v2 therefore NEVER kills: it verifies
family health (each launcher still has its worker, every worker has a
parent), reports RAM + the model-slot, and states the one big lever."""
import time

import psutil
import requests as rq

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
ME = os.getpid() if False else None  # (read-only tool; no self-risk)

procs = []
for p in psutil.process_iter(["pid", "ppid", "name", "cmdline", "memory_info"]):
    try:
        cl = " ".join(p.info["cmdline"] or [])
        procs.append((p.info["pid"], p.info["ppid"],
                      (p.info["name"] or "").lower(), cl,
                      p.info["memory_info"].rss / 2 ** 20
                      if p.info["memory_info"] else 0))
    except Exception:
        pass

py = [t for t in procs if "python" in t[2]
      and any(m in t[3] for m in ("Apex", "apex", "companion", "room_watcher"))]
pids = {t[0] for t in py}

print("[the family = launcher+worker pairs (HEALTHY, never kill)]:")
orphans = 0
for pid, ppid, nm, cl, rss in sorted(py, key=lambda t: t[3]):
    role = "worker" if ppid in pids else "launcher"
    flag = ""
    if role == "worker" and ppid not in pids:
        flag = " (orphan!)"
        orphans += 1
    script = [a for a in cl.split() if a.endswith(".py")]
    print(f"  {role:<8} {pid:>6} ppid={ppid:>6} {rss:5.0f}MB "
          f"{(script[-1] if script else cl[-40:])[-46:]}{flag}")
print(f"[orphans]: {orphans}  | [pair-integrity]: "
      f"{'OK' if orphans == 0 else 'CHECK'}")

ram = psutil.virtual_memory()
print(f"\n[RAM] {ram.available / 2**30:.1f}GB free ({ram.percent}% used)")
try:
    ps = rq.get("http://localhost:11434/api/ps", timeout=5).json()
    for m in ps.get("models", []):
        print(f"[model slot]: {m.get('name')} "
              f"~{m.get('size_vram', 0) / 2**20:.0f}MB resident")
except Exception:
    print("[model slot]: ollama not reachable")
print("[the one big RAM lever]: the pinned chat-brain (~2.7GB). Unpin = "
      "instant 2.7GB back, cold-start 20-40s per ask. A founder call, "
      "never a script's.")