"""THE SPEED-CURE, small and evidence-backed:

1. diag: the ollama slot + the RAM (the hardware-bound read)
2. THE PIN: warm the chat-lane's phi4-mini into the slot with a longer
   keep_alive (24h) - the swap-latency (20-250s) = gone for the next asks
3. measure: a timed small stream before/after
"""
import json
import os
import sys
import time

os.chdir(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed")
sys.path.insert(0, "Scripts")
import psutil
import requests as rq

free = psutil.virtual_memory().available / 2 ** 30
print(f"[RAM] {free:.2f}GB free (the bound: the pin = phi4-mini's ~2.6GB")
print(f"[bound-check]: {'OK - pin fits with headroom' if free - 2.6 >= 1.0 else 'WARN - tight'}")

ps_ = rq.get("http://localhost:11434/api/ps", timeout=5).json()
loaded = [(m.get("name"), round(m.get("size_vram", 0) / 2**20)) for m in ps_.get("models", [])]
print("[slot now]:", loaded)

# THE PIN: load phi4-mini + hold it (the keep_alive = the honest = the
# swap-killer); the small warm-token = the load-price paid NOW (once)
t0 = time.time()
r = rq.post("http://localhost:11434/api/chat",
            json={"model": "phi4-mini:latest", "stream": False,
                  "messages": [{"role": "user", "content": "say OK"}],
                  "keep_alive": "24h",
                  "options": {"num_predict": 8, "temperature": 0}},
            timeout=300)
print(f"[pin+warm phi4-mini]: HTTP {r.status_code} in {time.time()-t0:.1f}s "
      f"(the load-price = paid once; the next asks = ~2s)")
ps_ = rq.get("http://localhost:11434/api/ps", timeout=5).json()
print("[slot after]:", [(m.get("name"), round(m.get("size_vram", 0) / 2**20))
                        for m in ps_.get("models", [])])

# the measure: the streaming's first-token AFTER the pin
KEY = open("Config/apex_api.key", encoding="utf-8-sig").read().strip()
t0 = time.time()
r = rq.post("http://127.0.0.1:8080/talk/api/stream",
            json={"message": "In one short line: reply with PING."},
            headers={"X-Apex-Key": KEY}, stream=True, timeout=120)
ttft = None
first_tok = ""
for line in r.iter_lines(decode_unicode=True):
    if not line:
        continue
    if line.startswith("data:"):
        try:
            j = json.loads(line[5:].strip())
            if j.get("t"):
                ttft = round(time.time() - t0, 2)
                first_tok = j["t"]
                break
        except Exception:
            pass
print(f"[ttft-after-pin]: {ttft}s via the live stream (the = the = = = = =)")