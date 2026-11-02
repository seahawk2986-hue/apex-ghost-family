"""the whole-function rewrite: normalize_tool_action rebuilt, markers char-coded."""
import io
import py_compile
import sys
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
src = open(P, encoding="utf-8").read()

TC, LB, RB, SL = chr(60), chr(124), chr(62), chr(47)
qwen_open, qwen_close = TC + "tool_call" + RB, TC + SL + "tool_call" + RB
lt_mark, lt_end = TC + LB + "tool_call" + RB, TC + LB + "end" + RB

a = src.find("def normalize_tool_action")
assert a != -1, "def not found"
b = src.find("\ndef ", a + 10)
assert b != -1, "the next def not found"

FN = '''def _shape_rescue(value):
    """THE SHAPERESCUE PREPASS: rescue the model's OWN explicitly-written
    action (re-key canonical); never invent, never guess shell text."""
    if not isinstance(value, dict):
        return None
    for nk, ak in (("name", "arguments"), ("name", "args"),
                   ("action", "arguments"), ("tool", "args"),
                   ("function", "arguments"), ("function", "parameters")):
        if isinstance(value.get(nk), str) and value.get(nk):
            arg = value.get(ak, {})
            if isinstance(arg, str):
                try:
                    arg = json.loads(arg)
                except Exception:
                    arg = {}
            if not isinstance(arg, dict):
                arg = {}
            return {"action": value[nk], "args": arg}
    if set(value) == {"action"} and isinstance(value["action"], dict):
        inner = value["action"]
        if isinstance(inner.get("action"), str) and isinstance(
                inner.get("args"), dict):
            return {"action": inner["action"], "args": inner["args"]}
    return None


def normalize_tool_action(raw):
    """Accept one explicit action, never guess executable text or unknown tools."""
    if not isinstance(raw, str) or len(raw) > 100000:
        raise ValueError("expected a bounded JSON object")
    text = raw.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    elif text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()
    # the ShapeRescue unwraps - markers BUILT from char-codes (never typed):
    qo = re.escape({q!r})
    qc = re.escape({qc!r})
    lm = re.escape({lmr!r})
    le = re.escape({ler!r})
    for pat in (r"<response>([\\s\\S]*?)</response>",
                qo + r"([\\s\\S]*?)" + qc,
                lm + r"([\\s\\S]*?)" + le):
        m = re.search(pat, text)
        if m and m.group(1).strip():
            text = m.group(1).strip()
            break
    try:
        value = json.loads(text)
    except (ValueError, TypeError):
        raise ValueError("invalid JSON; send one object without prose or tool markup")
    if not isinstance(value, dict):
        raise ValueError("exactly one object is required")
    if set(value) == {{"name", "arguments"}}:
        value = {{"action": value["name"], "args": value["arguments"]}}
    if set(value) != {{"action", "args"}}:
        rescued = _shape_rescue(value)
        if rescued:
            value = rescued
        else:
            raise ValueError("required keys: action and args")
    action, args = value["action"], value["args"]
'''.replace("{q!r}", repr(qwen_open)).replace("{qc!r}", repr(qwen_close)) \
   .replace("{lmr!r}", repr(lt_mark)).replace("{ler!r}", repr(lt_end))

src = src[:a] + FN + src[b:]
open(P, "w", encoding="utf-8").write(src)
py_compile.compile(P, doraise=True)
print("[engine]: the whole normalize rewritten + COMPILED CLEAN")
sample = qwen_open + '{"name": "write_file", "arguments": {"path": "x.py"}}' + qwen_close
m = re.search(re.escape(qwen_open) + r"([\s\S]*?)" + re.escape(qwen_close), sample)
print("[sim-rescue extract]:", m.group(1)[:70])