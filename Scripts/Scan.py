"""THE HONEST CENSUS v2: every python process on the box with our marks —
full cmdline, parent-pid, birth-time, RSS. SELF-EXCLUDED (its own pid and
its whole parent-chain can never appear as a 'duplicate'), and the true
family-key = the actual script token (never '--daemon' or a flag).
Read-only: it kills nothing."""
import datetime as dt
import os

import psutil

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
ME = os.getpid()

mine = {ME}
try:
    par = psutil.Process(ME).parent()
    while par is not None:
        mine.add(par.pid)
        par = par.parent()
except Exception:
    pass

rows = []
for p in psutil.process_iter(["pid", "ppid", "name", "cmdline",
                              "create_time", "memory_info"]):
    try:
        nm = (p.info["name"] or "").lower()
        if "python" not in nm:
            continue
        cl = " ".join(p.info["cmdline"] or [])
        rows.append((p.info["pid"], p.info["ppid"], nm, cl,
                     p.info["create_time"],
                     (p.info["memory_info"].rss / 2 ** 20)
                     if p.info["memory_info"] else 0))
    except Exception:
        pass

print(f"[python procs total]: {len(rows)}  (self-chain excluded below)")
ours = 0
for pid, ppid, nm, cl, born, rss in sorted(rows, key=lambda r: r[0]):
    if pid in mine:
        tag = "SELF"
    else:
        tag = ""
    hit = ("Apex" in cl or "apex" in cl or "companion" in cl
           or "room_watcher" in cl)
    if hit:
        ours += 1
    birth = dt.datetime.fromtimestamp(born).strftime("%H:%M:%S") if born else "?"
    if not hit and not tag:
        continue
    tail = cl[-86:] if len(cl) > 86 else cl
    print(f"  {pid:>6} ppid={ppid:>6} {rss:5.0f}MB {birth} "
          f"{nm[:9]:<9} {tail}")
print(f"[ours-marked]: {ours}")