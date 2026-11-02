"""THE VET-WINDOW (founder-consented): unpin phi4 (+2.7GB) -> the RAM-gate
re-check -> RUN the vet-line bounded organ -> REPIN phi4 24h (the chat-speed
returns). The unpin-window = ~5-6 minutes; the chat = cold-start only there."""
import json
import os
import subprocess as sp
import sys
import time

import psutil
import requests as rq

OLL = "http://localhost:11434"
PY = sys.executable
ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"

def ram():
    v = psutil.virtual_memory()
    return f"{v.available / 2**30:.2f}GB free"

print("[RAM pre]:", ram(), flush=True)
# 1. the unpin (keep_alive=0 = the ollama unload-shape)
r = rq.post(OLL + "/api/generate",
            json={"model": "phi4-mini:latest", "prompt": "",
                  "keep_alive": 0}, timeout=60)
ps = rq.get(OLL + "/api/ps", timeout=10).json()
print("[unpin]: HTTP", r.status_code, "| slot now:",
      [m.get("name") for m in ps.get("models", [])] or "(empty)",
      "| RAM:", ram(), flush=True)

# 2. the vet-line run (its own RAM-gate = the proof-of-honesty)
t0 = time.time()
sub = sp.run([PY, "-X", "utf8", os.path.join(ROOT, "Scripts", "VetLine.py")],
             capture_output=True, text=True, cwd=ROOT, timeout=420,
             encoding="utf-8", errors="replace")
out = (sub.stdout or "") + (sub.stderr or "")
print("[vet-line exit]:", sub.returncode, f"({round(time.time() - t0, 1)}s)")
print("\n".join("  " + l[:128] for l in out.splitlines()[-16:]), flush=True)

# 3. the REPIN (the founder's standing 24h pin = restored)
rp = rq.post(OLL + "/api/generate",
             json={"model": "phi4-mini:latest", "prompt": "",
                   "keep_alive": "24h"}, timeout=300)
ps2 = rq.get(OLL + "/api/ps", timeout=10).json()
print("[repin]: HTTP", rp.status_code, "| slot:",
      [(m.get("name"), round(m.get("size_vram", 0) / 2 ** 20))
       for m in ps2.get("models", [])], "| RAM:", ram())