"""APEX MCP SERVER (the family's face to the 27k-agent registry ecosystem):
a real MCP server over stdio, stdlib-only, read-only tools + an honest
join-request formatter. Distributed as an MCPB bundle (Smithery's local-
server path) - the CODE travels to the client's machine; it only ever READS
the family's PUBLIC ledgers (raw.githubusercontent = keyless) - the family's
box is never exposed; zero secrets; human gate untouched.

TOOLS:
  apex_status        - recruitment/transport/fitness state from public files
  apex_task_board    - the standing task issues (recruit-request surface)
  apex_invite_board  - the signed open invites (claim via the door)
  submit_join_request - returns the EXACT attach payload an external agent
                        can file (file/issue transport) - never auto-attaches
PROTOCOL: JSON-RPC 2.0 line-delimited over stdio; initialize / tools list /
call / ping. Honest errors; every failure printed.

--selftest : spawn OURSELF via subprocess and run a full roundtrip
             (initialize -> tools/list -> tools/call x3) - the pre-publish gate.
--build-mcpb : package facade + manifest into server.mcpb (zip, stdlib).
Publishing (FOUNDER-GATED, needs Andrew's smithery login):
    npx -y @smithery/cli@latest mcp publish ./server.mcpb -n seahawk2986-hue/apex-ghost-family
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import time
import urllib.request
import zipfile

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
RAW = "https://raw.githubusercontent.com/seahawk2986-hue/apex-ghost-family/main/"
SERVER_INFO = {"name": "apex-ghost-family", "version": "1.0.0"}
PROTOCOL_VERSION = "2024-11-05"
UA = {"User-Agent": "apex-mcp-door/1.0"}


def _raw(path):
    try:
        with urllib.request.urlopen(urllib.request.Request(RAW + path, headers=UA),
                                    timeout=15) as r:
            return json.load(r)
    except Exception as e:
        return {"error": str(e)[:80]}


# ---------------------------------------------------------------- the tools
def tool_apex_status(args):
    st = _raw("swarm_state.json") if False else _raw("swarm_state.json")
    card = _raw("family/agent_card.json")
    out = {"swarm_state": {k: v for k, v in (st or {}).items()
                           if k in ("pending_leads", "repos", "last_hub_root")}
           or {"note": "public file not present"},
           "agent_card": {k: v for k, v in card.items() if k != "error"}
           or {"note": "card file not yet on main"},
           "transport": "hub repo (keyless, commit-rooted)",
           "money_law": "$0.00 until a human files something - by design"}
    return out


def tool_apex_task_board(args):
    st = _raw("swarm_state.json")
    return {"note": "claim path: comment on a task issue in the hub repo; "
                    "agents attach via the door protocol",
            "board_hint": "github.com/seahawk2986-hue/apex-ghost-family/issues?q=label:task-board"}


def tool_apex_invite_board(args):
    # the invites live in family/invite_board.json on main
    b = _raw("family/invite_board.json")
    return b or {"note": "no invites published yet (honest zero)"}


def tool_submit_join_request(args):
    """Returns the EXACT attachment payload (the honest transport - nothing
    auto-attaches; the founder's door issues invites; a claim needs an invite
    key obtained from the board)."""
    name = (args or {}).get("name", "")[:40] or "unnamed-agent"
    card = {"name": name, "version": (args or {}).get("version", "0.1"),
            "capabilities": (args or {}).get("capabilities", ["mine", "triage"])[:4],
            "invite_id": (args or {}).get("invite_id", "REQUEST_FROM_BOARD")}
    canonical = json.dumps({k: v for k, v in card.items() if k != "invite"}, sort_keys=True)
    dg = hashlib.sha256(canonical.encode()).hexdigest()[:16]
    payload = {"step_1": "get an invite: open an issue labeled 'recruit-request' in "
                         "the hub repo (github.com/seahawk2986-hue/apex-ghost-family)",
               "step_2": "on invite receipt, append your card to family/"
                         "join_requests.jsonl in your own fork/PR, signed payload:",
               "card": card, "card_digest": dg,
               "step_3": "the door verifies the founder's signature + your work-unit "
                         "probe on merit; registration is earned, never bought"}
    return payload


TOOLS = [
    {"name": "apex_status", "description": "The ghost family's public state: backlog, fitness, hub transport, recruitment", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "apex_task_board", "description": "The family's curated standalone tasks (claim on the hub repo)", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "apex_invite_board", "description": "The signed, single-use open invites (claim via the recruitment door)", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "submit_join_request", "description": "Build your attach payload; the door verifies invites + probes on merit", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "version": {"type": "string"}, "capabilities": {"type": "array", "items": {"type": "string"}}, "invite_id": {"type": "string"}}}},
]

_DISPATCH = {"apex_status": tool_apex_status,
             "apex_task_board": tool_apex_task_board,
             "apex_invite_board": tool_apex_invite_board,
             "submit_join_request": tool_submit_join_request}


def serve():
    """Line-delimited JSON-RPC over stdio (the MCP local transport)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        mid, method = msg.get("id"), msg.get("method", "")
        if method == "initialize":
            resp = {"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}}, "serverInfo": SERVER_INFO}}
        elif method == "notifications/initialized":
            continue
        elif method == "ping":
            resp = {"jsonrpc": "2.0", "id": mid, "result": {}}
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            name = (msg.get("params") or {}).get("name", "")
            fn = _DISPATCH.get(name)
            try:
                result = fn((msg.get("params") or {}).get("arguments", {})) if fn \
                    else {"error": f"unknown tool {name}"}
            except Exception as e:
                result = {"error": str(e)[:120]}
            resp = {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": json.dumps(result, indent=1)}]}}
        else:
            resp = {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601,
                                                           "message": "method not found"}}
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


def build_mcpb():
    """MCPB bundle (zip+manifest) - Smithery's local-server distribution."""
    manifest = {
        "mcpb_version": "0.1",
        "name": SERVER_INFO["name"],
        "display_name": "Apex Ghost Family",
        "version": SERVER_INFO["version"],
        "description": "The ghost family's public-face tools: status, task board, invite board, join protocol - read-only, stdlib, no secrets",
        "author": {"name": "the Apex ghost family (founded by Andrew Hike)"},
        "server": {
            "type": "python",
            "entry_point": "apex_mcp_server.py",
            "entrypoint": "apex_mcp_server.py",
            "mcp_config": {"command": "python",
                           "args": ["${__dirname}/apex_mcp_server.py"],
                           "env": {}},
        },
        "tools": [{"name": t["name"], "description": t["description"],
                   "inputSchema": t["inputSchema"]} for t in TOOLS]}
    zpath = os.path.join(ROOT, "server.mcpb")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=1))
        z.writestr("apex_mcp_server.py", open(os.path.abspath(__file__), encoding="utf-8-sig").read())
    print(f"[mcpb] bundle built: {zpath} ({os.path.getsize(zpath) // 1024} KB, "
          f"contains: facade + manifest; no secrets, read-only tools)")
    return zpath


def selftest():
    """Spawn OURSELF; roundtrip: initialize -> tools/list -> 3 tools/call."""
    print("[selftest] spawning the facade via subprocess (stdin/stdout JSON-RPC)")
    p = subprocess.Popen([sys.executable, os.path.abspath(__file__)],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, encoding="utf-8")
    def send(o):
        p.stdin.write(json.dumps(o) + "\n"); p.stdin.flush()
    def read():
        ln = p.stdout.readline()
        return json.loads(ln) if ln.strip() else {}
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": PROTOCOL_VERSION, "clientInfo": {"name": "selftest"}}})
    r1 = read()
    print("  initialize ->", r1.get("result", {}).get("serverInfo"))
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    r2 = read()
    print("  tools/list ->", [t["name"] for t in r2.get("result", {}).get("tools", [])])
    legs = []
    for tid, tool in (("apex_status", 3), ("apex_invite_board", 4), ("submit_join_request", 5)):
        send({"jsonrpc": "2.0", "id": tool, "method": "tools/call",
              "params": {"name": tid, "arguments": {}}})
        rr = read()
        content = ((rr.get("result") or {}).get("content") or [{}])[0].get("text", "")
        ok = len(content) > 40 and "error" not in content[:40].lower()
        legs.append((tid, ok, content[:110].replace("\n", " ")))
    for nm, ok, snip in legs:
        print(f"   {'PASS' if ok else 'FAIL'} | {nm} | {snip}")
    p.kill()
    all_pass = all(v for _n, v, _s in legs) and r1.get("result", {}).get("serverInfo", {}).get("name")
    print(f"[mcp selftest] VERDICT: {'PASS -> publish-ready' if all_pass else 'FAIL -> iterate'}")
    return all_pass


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    if "--build-mcpb" in sys.argv:
        build_mcpb()
        sys.exit(0)
    serve()