"""FreeSwarmMCP.py - FreeSwarm-as-MCP: the keyring's $0 lanes exposed as
an MCP tool server (OpenCode local stdio). THE LAWS IN CODE:

  1. MONEY LAW       - only $0 lanes enter this server (openrouter :free,
                       nim's free tier, GitHub Models' free tier). No paid
                       key ever compounds a completion.
  2. HONESTY LAW     - every response discloses the serving lane and the
                       measured verdict of the session ledger; an
                       UNMEASURED lane serves only with the warning mark.
  3. SESSION-MIND LAW- this tool is work-machinery (organs, sub-agents
                       and their routine asks). It is NOT the session's
                       chat mind and never substitutes it; the model chain
                       laws govern that separately.
  4. CAPS ARE REAL   - the rotator walks n independent caps; receipts
                       (use X/N today) are printed for every serve.

Protocol: newline-delimited JSON-RPC 2.0 over stdio (MCP); only the three
verbs a tool server needs: initialize, tools/list, tools/call.
"""
import json
import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import FreeSwarm  # noqa: E402

# The session's measured lane ledger (if it grades a matching lane, the
# verdict is disclosed honestly; unmeasured = served with the warning)
LEDGER = r"C:\Users\seaha\OneDrive\Documents\Default Project\.opencode\lane_ledger.json"

SERVER_INFO = {"name": "freeswarm-lanes", "version": "1.0.0"}
STDOUT_LOCK = threading.Lock()


def lane_verdict(model_id):
    """THE HONESTY LAW: the measured verdict, or the warning-mark."""
    try:
        with open(LEDGER, encoding="utf-8") as f:
            led = json.load(f)
        row = (led.get("scores") or {})
        for lane, sc in row.items():
            if model_id and lane.endswith(model_id):
                v = sc.get("verdict", "unmeasured")
                return v, led.get("bench_day", "?")
    except Exception:
        pass
    return "unmeasured", None


def tool_ask(args):
    prompt = str(args.get("prompt", "")).strip()
    if not prompt:
        return {"isError": True, "content": [{"type": "text",
                "text": "freeswarm_ask needs a non-empty prompt"}]}
    max_tokens = int(args.get("max_tokens", 500) or 500)
    purpose = str(args.get("purpose", "mcp-ask"))[:40]
    out = []
    _print = print
    # capture the rotator's receipt line (the law: receipts, not claims)
    import io
    buf = io.StringIO()
    real_stdout = sys.stdout
    try:
        sys.stdout = buf
        text = FreeSwarm.ask(prompt, max_tokens=max_tokens, purpose=purpose)
    finally:
        sys.stdout = real_stdout
    receipts = [ln for ln in buf.getvalue().splitlines()
                if ln.startswith("[freeswarm]")]
    if not (text or "").strip():
        return {"content": [{"type": "text", "text":
                 json.dumps({"served": False,
                             "reason": "all free lanes spent or dead "
                                       "(the floor holds; nothing paid "
                                       "was substituted)",
                             "receipts": receipts}, indent=1)}]}
    mid = ""
    for ln in receipts:
        if "served by " in ln:
            mid = ln.split("served by ", 1)[1].split(" (", 1)[0].split("/", 1)[-1]
    verdict, bench_day = lane_verdict(mid)
    warn = "" if verdict not in ("unmeasured",) else \
        " [WARNING: serving lane unmeasured for coding-equivalence]"
    return {"content": [{"type": "text", "text":
             (text or "") + "\n\n" +
             json.dumps({"served_by": mid, "verdict": verdict,
                         "bench_day": bench_day, "warning": warn.strip(),
                         "$0": True, "purpose": purpose,
                         "receipts": receipts}, indent=1)}]}


def tool_stats(args):
    import io
    buf = io.StringIO()
    real_stdout = sys.stdout
    try:
        sys.stdout = buf
        stats = FreeSwarm.pool_stats()
    finally:
        sys.stdout = real_stdout
    stats["verdict_disclosure"] = "ports carry the session ledger verdicts"
    return {"content": [{"type": "text", "text": json.dumps(stats, indent=1)}]}


TOOLS = [
    {"name": "freeswarm_ask",
     "description":
         "Ask ONE question through the free-lane rotator ($0 lanes only: "
         "openrouter free, nim, GitHub Models). Work-machinery tool - NOT "
         "the session's chat mind. Response discloses the serving lane, "
         "its measured verdict, and today's cap usage.",
     "inputSchema": {"type": "object", "properties": {
         "prompt": {"type": "string"},
         "max_tokens": {"type": "integer", "default": 500},
         "purpose": {"type": "string", "default": "mcp-ask"}},
         "required": ["prompt"]}},
    {"name": "freeswarm_stats",
     "description": "Pool state: seats, providers, calls today, excluded lanes.",
     "inputSchema": {"type": "object", "properties": {}}},
]


def _send(msg):
    with STDOUT_LOCK:
        sys.stdout.write(json.dumps(msg, separators=(",", ":")) + "\n")
        sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        method = req.get("method", "")
        rid = req.get("id")
        if method == "initialize":
            _send({"jsonrpc": "2.0", "id": rid, "result": {
                "protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO}})
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            _send({"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            name = (req.get("params") or {}).get("name", "")
            args = (req.get("params") or {}).get("arguments") or {}
            try:
                if name == "freeswarm_ask":
                    res = tool_ask(args)
                elif name == "freeswarm_stats":
                    res = tool_stats(args)
                else:
                    res = {"isError": True, "content": [{"type": "text",
                            "text": f"unknown tool: {name}"}]}
            except Exception as error:
                res = {"isError": True, "content": [{"type": "text",
                        "text": f"freeswarm error: {str(error)[:200]}"}]}
            _send({"jsonrpc": "2.0", "id": rid, "result": res})
        elif method == "ping":
            _send({"jsonrpc": "2.0", "id": rid, "result": {}})
        else:
            if rid is not None:
                _send({"jsonrpc": "2.0", "id": rid, "error":
                       {"code": -32601, "message": "method not found"}})


if __name__ == "__main__":
    main()
