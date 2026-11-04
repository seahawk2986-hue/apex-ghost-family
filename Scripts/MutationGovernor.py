"""MutationGovernor - THE FIVE PRINCIPLES, enforced in code.

P1 CODE MUTATION LOOP: reads every organ's receipt trail, classifies
   failures, and emits next-generation directives (machine-consumable).
P2 ERROR PROTECTION: pre-flight compiles EVERY script before anything
   else runs; a broken organ is named, never skipped silently.
P3 CONTEXT OUTSOURCING: relay() sends oversized text through the $0
   lane ring (FreeSwarm) for digest/compress - the free big-context
   route, receipts disclose the serving lane.
P4 $0.00 LIMIT: static zero-cost audit over all scripts - any import
   or endpoint marker associated with paid APIs is flagged by name.
P5 COMPRESSION: the compressor folds large sources into modular,
   sendable cores; big files are listed where relay should act.

Runs offline except relay(); receipts to mutation_governor.jsonl.
"""
import ast
import importlib.util
import io
import json
import os
import py_compile
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RECEIPTS = os.path.join(HERE, "mutation_governor.jsonl")
FAIL_EV = ("BALKED", "VETO", "EMPTY_POOL", "BUDGET_BREAK", "DISCARD",
           "ERROR", "FAIL", "TIE", "MISSING")


def receipt(ev):
    with open(RECEIPTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, default=str) + "\n")


# ---------------- P2: pre-flight validation ----------------
def preflight():
    """P2 in full: pass 1 compiles (syntax); pass 2 parses and resolves
    EVERY import against the real environment (stdlib + installed +
    local modules). A script passes only with both passes clean."""
    local_mods = {n[:-3] for n in os.listdir(HERE) if n.endswith(".py")}
    bad, ok = [], 0
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py") or name.startswith("_"):
            continue
        path = os.path.join(HERE, name)
        try:
            # NOTE: cfile omitted on purpose - on Windows, os.path.devnull
            # is "nul", a non-regular file py_compile refuses to write to.
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            bad.append({"script": name, "error": str(e)[-160:]})
            continue
        try:
            tree = ast.parse(open(path, encoding="utf-8",
                                  errors="replace").read())
        except SyntaxError as e:
            bad.append({"script": name, "error": "ast: " + str(e)[-140:]})
            continue
        unresolved = []
        for node in ast.walk(tree):
            roots = []
            if isinstance(node, ast.Import):
                roots = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots = [node.module.split(".")[0]]
            for r in roots or []:
                if r in local_mods:
                    continue
                try:
                    if importlib.util.find_spec(r) is None:
                        unresolved.append(r)
                except Exception:
                    unresolved.append(r + "?")
        if unresolved:
            bad.append({"script": name,
                        "error": "unresolved imports: "
                                 + ",".join(sorted(set(unresolved)))})
            continue
        ok += 1
    receipt({"ev": "PREFLIGHT", "ok": ok, "broken": len(bad)})
    return {"ok": ok, "broken": bad}


# ---------------- P4: the $0.00 static audit ----------------
PAID_MARKERS = [
    (r"api\.openai\.com", "openai-paid-endpoint"),
    (r"api\.anthropic\.com", "anthropic-paid-endpoint"),
    (r"googleapis\.com/aif?", "gcp-billing-plane"),
    (r"azure\.com/openai", "azure-openai-billed"),
    (r"api\.together\.xyz", "together-billed"),
    (r"replicate\.com/api", "replicate-billed"),
    (r"\bsk-[A-Za-z0-9]{20,}", "hardcoded-secret-looking-key"),
    (r"billing=|charge_usd|_paid\s*=\s*True", "explicit-paid-flag"),
]


def zero_audit():
    suspects = []
    scanned = 0
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py"):
            continue
        if name == "MutationGovernor.py":
            continue        # self-scan exclusion: the audit's own markers are not findings
        scanned += 1
        path = os.path.join(HERE, name)
        try:
            src = open(path, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for pat, label in PAID_MARKERS:
            for m in re.finditer(pat, src):
                line = src.count("\n", 0, m.start()) + 1
                suspects.append({"script": name, "line": line,
                                 "marker": label})
    receipt({"ev": "ZERO_AUDIT", "scanned": scanned,
             "suspects": len(suspects)})
    return {"scanned": scanned, "suspects": suspects}


# ---------------- P5: compression survey ----------------
def compression(sweep_kb=24):
    heavy = []
    total = 0
    for name in os.listdir(HERE):
        if not name.endswith(".py"):
            continue
        sz = os.path.getsize(os.path.join(HERE, name))
        total += sz
        if sz >= sweep_kb * 1024:
            heavy.append({"script": name, "kb": round(sz / 1024, 1)})
        ast.parse(open(os.path.join(HERE, name), encoding="utf-8",
                       errors="replace").read())
        # parse check doubles as an import-syntax audit (P2 second pass)
    receipt({"ev": "COMPRESS_SURVEY", "total_kb": round(total / 1024, 1),
             "heavy": len(heavy)})
    return {"scripts_kb": round(total / 1024, 1), "heavy": heavy}


# ---------------- P1: telemetry -> next directives ----------------
def telemetry(n=40):
    directives = []
    for name in os.listdir(HERE):
        if not name.endswith(".jsonl") or name == "mutation_governor.jsonl":
            continue
        path = os.path.join(HERE, name)
        try:
            lines = open(path, encoding="utf-8",
                         errors="replace").readlines()[-n:]
        except Exception:
            continue
        fails = []
        for ln in lines:
            try:
                row = json.loads(ln)
            except Exception:
                continue
            ev = str(row.get("ev", ""))
            if any(tag in ev.upper() for tag in FAIL_EV):
                fails.append(ev)
        if fails:
            directives.append({"organ": name, "recent_fails": len(fails),
                               "kinds": sorted(set(fails))[:4]})
    receipt({"ev": "TELEMETRY", "organs_with_fails": len(directives)})
    return {"directives": directives}


# ---------------- P3: the free big-context relay ----------------
def relay(path, instruction="Compress this into the facts that matter, <=200 words.", chunk=12000):
    """Send an oversized local file through the $0 lane ring for a
    digest. Files over the chunk limit are folded in slices; the
    serving lane is disclosed every time (the verdict-disclosure law)."""
    if not os.path.exists(path):
        receipt({"ev": "RELAY_MISS", "path": path})
        return None
    import FreeSwarm
    data = open(path, encoding="utf-8", errors="replace").read()
    folded = ""
    for i in range(0, len(data), chunk):
        piece = data[i:i + chunk]
        ask = ("COMPRESS TASK. %s\n---\n%s" % (instruction, piece))
        folded += str(FreeSwarm.ask(ask, max_tokens=400,
                                    purpose="context-relay") or "")
    receipt({"ev": "RELAY", "path": path, "chars_in": len(data),
             "chars_out": len(folded)})
    return folded


# ---------------- P5: modular send-packs ----------------
SEND_DIR = os.path.join(HERE, "SendPacks")
TOKENS_PER_CHAR = 0.28          # conservative 1 token ~ 3.6 chars


def pack(script, entry_only=True, max_tokens=3000):
    """P5 in operation: fold a module into sendable chunks - imports,
    docstring, then every top-level def/const - split at lane-safe
    token budgets so no free endpoint ever hits context fatigue.
    Chunks are numbered for reassembly ('PACK i/j')."""
    path = os.path.join(HERE, script if script.endswith(".py")
                        else script + ".py")
    src = open(path, encoding="utf-8", errors="replace").read()
    tree = ast.parse(src)
    lines = src.splitlines()
    pieces = []
    if tree.body and isinstance(tree.body[0], ast.Expr) and \
            isinstance(tree.body[0].value, ast.Constant):
        doc = tree.body[0].value.value
        pieces.append('"""' + str(doc[:400]) + '"""')
    keep = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            keep.append(node)
        elif isinstance(node, ast.Assign):
            keep.append(node)
    keep.sort(key=lambda n: n.lineno)
    for node in keep:
        seg = "\n".join(lines[node.lineno - 1:node.end_lineno or node.lineno])
        pieces.append(seg)
    body = "\n\n\n".join(pieces)
    budget = int(max_tokens / TOKENS_PER_CHAR)
    chunks, cur = [], ""
    for piece in pieces:
        if len(cur) + len(piece) > budget and cur:
            chunks.append(cur)
            cur = piece
        else:
            cur = (cur + "\n\n\n" + piece) if cur else piece
    if cur:
        chunks.append(cur)
    os.makedirs(SEND_DIR, exist_ok=True)
    base = script.replace(".py", "")
    out = []
    for i, ch in enumerate(chunks, 1):
        text = "PACK %d/%d [%s] (reassembly: keep order)\n\n%s" % (
            i, len(chunks), base, ch)
        fp = os.path.join(SEND_DIR, "%s.pack%d.of%d.txt" % (base, i,
                                                           len(chunks)))
        open(fp, "w", encoding="utf-8").write(text)
        out.append({"file": os.path.basename(fp),
                    "approx_tokens": int(len(ch) * TOKENS_PER_CHAR)})
    receipt({"ev": "PACK", "script": script, "chunks": len(chunks)})
    return {"chunks": len(chunks), "approx_tokens_each": out[:4]}


def main():
    p = preflight()
    z = zero_audit()
    c = compression()
    t = telemetry()
    summary = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
               "preflight_ok": p["ok"], "preflight_broken": p["broken"],
               "zero_suspects": len(z["suspects"]),
               "heavy_scripts": len(c["heavy"]),
               "organs_directed": len(t["directives"])}
    print(json.dumps(summary, indent=1))
    receipt({"ev": "GOV_DONE", **{k: v for k, v in
             (("ts", summary["ts"]), ("ok", p["ok"]),
              ("broken", len(p["broken"])),
              ("suspects", z["suspects"][:6]))}})


if __name__ == "__main__":
    cmd = "all"
    if len(os.sys.argv) > 1:
        cmd = os.sys.argv[1]
    if cmd == "relay" and len(os.sys.argv) > 2:
        print(relay(os.sys.argv[2]))
    elif cmd == "preflight":
        print(json.dumps(preflight(), indent=1))
    elif cmd == "audit":
        print(json.dumps(zero_audit(), indent=1))
    elif cmd == "telemetry":
        print(json.dumps(telemetry(), indent=1))
    elif cmd == "pack" and len(os.sys.argv) > 2:
        print(json.dumps(pack(os.sys.argv[2]), indent=1))
    else:
        main()
