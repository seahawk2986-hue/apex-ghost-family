"""The fixer that can write what I cannot type: rewrites the engine's
unwrap-tuple with char-coded, correct marker patterns + self-verifies."""
import io
import py_compile
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py"
src = open(P, encoding="utf-8").read()

TC, LB, RB, SL = chr(60), chr(124), chr(62), chr(47)
qwen_open, qwen_close = TC + "tool_call" + RB, TC + SL + "tool_call" + RB
lt_mark, lt_end = TC + LB + "tool_call" + RB, TC + LB + "end" + RB
a = src.find("for pat in (r\"<response>")
b = src.find(":\n        m = re.search(pat, text)", a)
assert a != -1 and b != -1, "anchors not found"
block = src[a:b]
replacement = (
    "for pat in (\n"
    "                r\"<response>([\\s\\S]*?)</response>\",\n"
    "                re.escape(" + repr(qwen_open) + ") + r\"([\\s\\S]*?)\" + re.escape(" + repr(qwen_close) + "),\n"
    "                re.escape(" + repr(TC + LB + "tool_call" + RB) + ") + r\"([\\s\\S]*?)\" + re.escape(" + repr(TC + LB + "end" + RB) + "))")
src = src[:a] + replacement + src[b:]
open(P, "w", encoding="utf-8").write(src)
py_compile.compile(P, doraise=True)
print("[fixed + compiled]: the unwrap-tuple rebuilt char-coded")

# the self-verify: every pattern must compile as regex
import re
for pat in (r"<response>([\s\S]*?)</response>",
            re.escape(qwen_open) + r"([\s\S]*?)" + re.escape(qwen_close),
            re.escape(TC + LB + "tool_call" + RB) + r"([\s\S]*?)" + re.escape(TC + LB + "end" + RB)):
    re.compile(pat)
    print("   [regex ok]:", pat[:58])
sample = qwen_open + '{"name": "write_file", "arguments": {"path": "x.py"}}' + qwen_close
m = re.search(re.escape(qwen_open) + r"([\s\S]*?)" + re.escape(qwen_close), sample)
print("[live-sim rescue extract]:", m.group(1)[:60])