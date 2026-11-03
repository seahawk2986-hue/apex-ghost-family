"""SwarmNodeServer - THE NODE KIT (the door a volunteer opens: a tiny
pure-stdlib HTTP server that turns ANY machine with its own free keys
into a swarm node, 2026-11-03):

  GET  /health  -> {"ok": true, "capacity_left": n, "region": ...}
  POST /ask     {"prompt", "max_tokens", "purpose"} -> {"reply": ...}

THE HOST'S LAWS (printed at boot):
  - YOUR key, YOUR box, YOUR caps: the server calls the SAME FreeSwarm
    catalog the founder's fleet uses, bound to the .env YOU control
  - the daily_cap is YOURS to set (env APEX_NODE_DAILY_CAP; the fleet
    will never route more onto you than you stated)
  - withdraw anytime: stop the process (or set the cap to 0) and the
    fleet's ping-hour drops you silently within the hour
  - nothing is stored by the node beyond the immediate answer
$0; stdlib only (the volunteeer's box needs nothing installed)."""

import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PORT = int(os.environ.get("APEX_NODE_PORT", "8082"))
DAILY = int(os.environ.get("APEX_NODE_DAILY_CAP", "40"))
REGION = os.environ.get("APEX_NODE_REGION", "undisclosed")
_used = {"n": 0, "day": time.strftime("%Y-%m-%d")}
_lock = threading.Lock()


def _day_roll():
    t = time.strftime("%Y-%m-%d")
    if _used["day"] != t:
        _used["day"], _used["n"] = t, 0


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        return   # the quiet server (the receipt = the fleet's own ledger)

    def _send(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        _day_roll()
        if self.path.startswith("/health"):
            self._send(200, {"ok": True, "region": REGION,
                             "capacity_left": max(0, DAILY - _used["n"]),
                             "protocol": "apex-swarm/1"})
        else:
            self._send(404, {"ok": False})

    def do_POST(self):
        _day_roll()
        if not self.path.startswith("/ask"):
            return self._send(404, {"ok": False})
        try:
            ln = int(self.headers.get("Content-Length", "0") or 0)
            d = json.loads(self.rfile.read(ln) or "{}")
        except Exception:
            return self._send(400, {"ok": False})
        with _lock:
            if _used["n"] >= DAILY:
                return self._send(200, {"reply": "",
                                        "note": "cap reached (the host's law)"})
        prompt = str(d.get("prompt", ""))[:4000]
        mt = int(d.get("max_tokens", 300) or 300)
        purpose = str(d.get("purpose", "node"))[:60]
        try:
            import FreeSwarm as FS
            reply = FS.ask(prompt, max_tokens=mt,
                           purpose=f"node:{purpose}") or ""
        except Exception as e:
            return self._send(200, {"reply": "",
                                    "note": f"lane-fail {type(e).__name__}"})
        with _lock:
            _used["n"] += 1
        self._send(200, {"reply": reply[: int(mt * 6)]})


if __name__ == "__main__":
    print(f"[swarm-node]: http://0.0.0.0:{PORT} | cap {DAILY}/day | region "
          f"{REGION}")
    print("[swarm-node] LAWS: your key stays here; the cap is yours; "
          "withdraw = stop me")
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()
