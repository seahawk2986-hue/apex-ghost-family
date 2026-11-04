"""MutationGovernor - THE FIVE OPERATIONAL PRINCIPLES, enforced in code."""
import ast, importlib.util, json, os, py_compile, re, time

HERE = os.path.dirname(os.path.abspath(__file__))
RECEIPTS = os.path.join(HERE, "mutation_governor.jsonl")
FAIL_EV = ("BALKED","VETO","EMPTY_POOL","BUDGET_BREAK","DISCARD","ERROR","FAIL","TIE","MISSING")


def receipt(ev):
    with open(RECEIPTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, default=str) + "\n")


def preflight():
    """P2: compile pass + AST import-resolution pass. Fail-closed."""
    local_mods = {n[:-3] for n in os.listdir(HERE) if n.endswith(".py")}
    bad, ok = [], 0
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py") or name.startswith("_"):
            continue
        path = os.path.join(HERE, name)
        try:
            py_compile.compile(path, doraise=True)
            tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
        except Exception as e:
            bad.append({"script": name, "error": str(e)[:150]}); continue
        unres = []
        for node in ast.walk(tree):
            roots = ([a.name.split(".")[0] for a in node.names]
                     if isinstance(node, ast.Import) else
                     ([node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.module else []))
            for r in roots:
                if r in local_mods:
                    continue
                try:
                    if importlib.util.find_spec(r) is None:
                        unres.append(r)
                except Exception:
                    unres.append(r)
        if unres:
            bad.append({"script": name, "error": "unresolved: " + ",".join(sorted(set(unres)))})
            continue
        ok += 1
    receipt({"ev": "PREFLIGHT", "ok": ok, "broken": len(bad)})
    return {"ok": ok, "broken": bad}


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
    """P4: perpetual zero-cost audit; self-scan of the governor is exempt."""
    suspects = []; scanned = 0
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py") or name == "MutationGovernor.py":
            continue
        scanned += 1
        src = open(os.path.join(HERE, name), encoding="utf-8", errors="replace").read()
        for pat, label in PAID_MARKERS:
            for m in re.finditer(pat, src):
                suspects.append((name, src.count("\n", 0, m.start()) + 1, label))
    receipt({"ev": "ZERO_AUDIT", "scanned": scanned, "suspects": len(suspects)})
    return {"scanned": scanned, "suspects": suspects}


def compression():
    """P5: survey heavy scripts + parse-audit syntax across the Scripts."""
    heavy = []; total = 0
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py"):
            continue
        sz = os.path.getsize(os.path.join(HERE, name)); total += sz
        if sz >= 24 * 1024:
            heavy.append({"script": name, "kb": round(sz / 1024, 1)})
        ast.parse(open(os.path.join(HERE, name), encoding="utf-8", errors="replace").read())
    receipt({"ev": "COMPRESS_SURVEY", "total_kb": round(total / 1024, 1), "heavy": len(heavy)})
    return {"total_kb": round(total / 1024, 1), "heavy": heavy}


def telemetry(n=40):
    """P1: recent failure-receipt scan -> next mutation directives."""
    directives = []
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".jsonl") or name == "mutation_governor.jsonl":
            continue
        try:
            lines = open(os.path.join(HERE, name), encoding="utf-8", errors="replace").readlines()[-n:]
        except Exception:
            continue
        fails = []
        for ln in lines:
            try:
                row = json.loads(ln)
            except Exception:
                continue
            ev = str(row.get("ev", ""))
            if any(t in ev.upper() for t in FAIL_EV):
                fails.append(ev)
        if fails:
            directives.append({"organ": name, "recent_fails": len(fails), "kinds": sorted(set(fails))[:4]})
    receipt({"ev": "TELEMETRY", "organs_with_fails": len(directives)})
    return {"directives": directives}


SEND_DIR = os.path.join(HERE, "SendPacks")
TOKENS_PER_CHAR = 0.28


def pack(script, max_tokens=3000):
    """P5: modular send-pack - imports + defs, token-budgeted chunks."""
    path = os.path.join(HERE, script if script.endswith(".py") else script + ".py")
    src = open(path, encoding="utf-8", errors="replace").read()
    tree = ast.parse(src)
    lines = src.splitlines()
    pieces = []
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
        pieces.append('"""%s"""' % str(tree.body[0].value.value)[:400])
    keep = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign))]
    keep.sort(key=lambda n: n.lineno)
    for node in keep:
        pieces.append("\n".join(lines[node.lineno - 1:node.end_lineno or node.lineno]))
    budget = int(max_tokens / TOKENS_PER_CHAR)
    chunks, cur = [], ""
    for piece in pieces:
        if len(cur) + len(piece) > budget and cur:
            chunks.append(cur); cur = piece
        else:
            cur = (cur + "\n\n\n" + piece) if cur else piece
    if cur:
        chunks.append(cur)
    os.makedirs(SEND_DIR, exist_ok=True)
    base = script.replace(".py", "")
    for i, ch in enumerate(chunks, 1):
        fp = os.path.join(SEND_DIR, "%s.pack%d.of%d.txt" % (base, i, len(chunks)))
        open(fp, "w", encoding="utf-8").write("PACK %d/%d [%s] (keep order)\n\n%s" % (i, len(chunks), base, ch))
        receipt({"ev": "PACK", "script": script, "chunk": os.path.basename(fp)})
    return {"chunks": len(chunks)}


def propose(script, fails=None):
    """OBB: evolution proposes its own mutation via the free lane."""
    import FreeSwarm
    src = open(os.path.join(HERE, script if script.endswith(".py") else script + ".py"), encoding="utf-8", errors="replace").read()
    ctx = "; ".join(json.dumps(f)[:220] for f in (fails or [])[:3])
    prompt = ("EVOLUTION MUTATION ENGINE. Organ: %s. Context: %s. Propose ONE concrete minimal mutation turning this failure into capability. Output ONLY code payload, no prose." % (script, ctx))
    out = str(FreeSwarm.ask(prompt, max_tokens=800, purpose="evolution-mutation") or "")
    receipt({"ev": "MUTATION_PROPOSAL", "organ": script, "proposal": out[:800]})
    return out


def main():
    p = preflight(); z = zero_audit(); c = compression(); t = telemetry()
    print(json.dumps({"preflight_ok": p["ok"], "preflight_broken": p["broken"], "zero_scanned": z["scanned"], "zero_suspects": len(z["suspects"]), "compress_kb": c["total_kb"], "directives": len(t["directives"])}, indent=1))


if __name__ == "__main__":
    cmd = "all"
    if len(os.sys.argv) > 1:
        cmd = os.sys.argv[1]
    if cmd == "preflight":
        print(json.dumps(preflight(), indent=1))
    elif cmd == "audit":
        print(json.dumps(zero_audit(), indent=1))
    elif cmd == "compress":
        print(json.dumps(compression(), indent=1))
    elif cmd == "telemetry":
        print(json.dumps(telemetry(), indent=1))
    elif cmd == "propose" and len(os.sys.argv) > 2:
        print(propose(os.sys.argv[2]))
    elif cmd == "pack" and len(os.sys.argv) > 2:
        print(json.dumps(pack(os.sys.argv[2]), indent=1))
    else:
        main()
