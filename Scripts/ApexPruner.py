"""ApexPruner - PHASE 1: the token-slipping pre-processor.

Before ANY external dispatch: strip boilerplate/comments, isolate ONLY the
failing function + its stack trace via AST + regex, and emit a bounded JSON
payload. No file ever leaves home whole; payloads live under the cap.
"""
import ast
import json
import re

BUDGET_CHARS = 6000          # ~1.5k tokens of working payload
TRACE_RX = re.compile(
    r'(Traceback \(most recent call last\):[\s\S]{0,1800})')


def _lines(src):
    return src.splitlines()


def failing_function(src, trace):
    """AST walk: find the named function that owns the deepest code frame."""
    frames = re.findall(r'File "[^"]+", line (\d+), in (\w+)', trace)
    wanted = None
    for _ln, fn in reversed(frames):
        if fn != "<module>":
            wanted = fn
            break
    if not wanted:
        return None
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name == wanted:
            lines = _lines(src)
            seg = lines[node.lineno - 1:min(node.end_lineno + 3, len(lines))]
            return wanted, "\n".join(seg)
    return None


def strip_noise(src):
    """Comments + docstrings + trailing blanks out; imports stay (honest deps)."""
    out = []
    in_doc, q = False, ""
    for ln in src.splitlines():
        s = ln.strip()
        if not in_doc and (s.startswith('"""') or s.startswith("'''")):
            q = s[:3]
            in_doc = not (len(s) > 5 and s.endswith(q) and len(s) > 3)
            if len(s) > 5 and s.endswith(q):
                continue
            continue
        if in_doc:
            in_doc = not s.endswith(q)
            continue
        if ln.lstrip().startswith("#"):
            continue
        out.append(ln.rstrip())
    return "\n".join([x for x in out if x.strip()]) + "\n"


def prune(task, src, error, imports_needed=None):
    """The bounded dispatch payload: {task, context, error, files}."""
    trace = (TRACE_RX.search(error or "") or [None, ""])[1]
    fn = failing_function(src or "", trace)
    context = ""
    if fn:
        name, body = fn
        context = f"function {name}:\n" + strip_noise(body)
        if imports_needed:
            context = "imports:\n" + imports_needed + "\n" + context
    else:
        context = strip_noise((src or ""))[:2500]
    payload = {"task": (task or "repair to green, no prose")[:300],
               "context": context[:BUDGET_CHARS],
               "error": (trace or (error or "")[:900])[:1500],
               "output_contract": ("return ONE unified diff in markdown, "
                                   "no prose, no full-file rewrites")}
    blob = json.dumps(payload)
    if len(blob) > BUDGET_CHARS + 1800:            # the hard cap shim
        payload["context"] = payload["context"][:BUDGET_CHARS // 2]
        blob = json.dumps(payload)
    return payload


if __name__ == "__main__":
    demo = prune("make test_divide green",
                 "def divide(a,b):\n    return a/b  # no zero guard\n",
                 "Traceback (most recent call last):\n"
                 '  File "t.py", line 3, in test_divide\n'
                 "ZeroDivisionError: division by zero")
    print(json.dumps(demo, indent=1)[:700])
    print("[pruner]: payload bytes =", len(json.dumps(demo)))