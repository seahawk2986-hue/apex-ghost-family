"""The engine's live state: the one check that ends the mystery."""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
src = open(r"C:\Users\seaha\Apex-Adapter\v2_job_engine.py", encoding="utf-8").read()
tail_ret = 'return {"action": action, "args": args}'
checks = [
    ("shape_rescue def", "def _shape_rescue" in src),
    ("harvest def", "MULTICALL HARVEST" in src),
    ("tail return", tail_ret in src),
    ("model_message_text def", "def model_message_text" in src),
    ("invalid-string count", str(src.count("invalid_tool_response"))),
]
for k, v in checks:
    print(f"   {k}: {v}")
the_big = '"invalid_tool_response"'
the_call = src.find("model_message_text(")
print("   [the string lives inside model_message_text only:", the_call != -1 and the_big in src[the_call:the_call+1200], "]")
where_called = src.count("model_message_text(")
print("   [call-sites of model_message_text]:", where_called, "(1 = only the def = never called)")