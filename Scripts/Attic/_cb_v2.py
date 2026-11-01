import py_compile
import re

p = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\CloudBrain.py"
s = open(p, encoding="utf-8-sig").read()

i = s.index("cands = list(models) or [")
j = s.index("]", s.index("llama-3.3-70b-versatile")) + 1
new_cands = '''cands = list(models) or [
        # THE LOCAL-FIRST TIER (the zero-dollar brain: no key, no drain;
        # the RAM law holds: 4.4GB inside the window; the swarm duck queues)
        ("local-coder", "http://localhost:11434/api/chat",
         "qwen2.5-coder:7b", "local-no-key", {}),
        # the VERIFIED cloud set (the ollama probed live; the reasoning
        # models need the token headroom)
        ("ollama", "https://ollama.com/v1/chat/completions",
         "gpt-oss:120b", keys.get("OLLAMA_API_KEY", ""),
         {"Authorization": "Bearer " + keys.get("OLLAMA_API_KEY", "")}),
        ("ollama-20b", "https://ollama.com/v1/chat/completions",
         "gpt-oss:20b", keys.get("OLLAMA_API_KEY", ""),
         {"Authorization": "Bearer " + keys.get("OLLAMA_API_KEY", "")}),
        ("openrouter", "https://openrouter.ai/api/v1/chat/completions",
         "meta-llama/llama-3.2-3b-instruct:free",
         keys.get("OPENROUTER_API_KEY", ""),
         {"Authorization": "Bearer " + keys.get("OPENROUTER_API_KEY", "")}),
        ("groq", "https://api.groq.com/openai/v1/chat/completions",
         "llama-3.3-70b-versatile", keys.get("GROQ_API_KEY", ""),
         {"Authorization": "Bearer " + keys.get("GROQ_API_KEY", "")}),
    ]'''
s = s[:i] + new_cands + s[j:]

body_old = None
m = re.search(
    r'try:\n(\s*)req = urllib\.request\.Request\(\n\s*url, data=json\.dumps\(\{\n'
    r'\s*"model": model,\n\s*"messages": \[\{"role": "user", "content": '
    r'prompt\[:6000\]\}\],\n\s*"max_tokens": max\(max_tokens, 512\) if '
    r'name\.startswith\(\n\s*"ollama"\) else max_tokens,\n'
    r'\s*"temperature": 0\}\)\.encode\(\),\n\s*headers=\{\*\*hdrs, '
    r'"Content-Type": "application/json"\}\)',
    s)
assert m, "the body block's anchor not found"
body_new = (
    "try:\n"
    "            if name.startswith(\"local\"):\n"
    "                body = {\"model\": model, \"stream\": False,\n"
    "                        \"messages\": [{\"role\": \"user\",\n"
    "                                      \"content\": prompt[:6000]}],\n"
    "                        \"options\": {\"num_predict\": max(max_tokens, "
    "512),\n"
    "                                    \"temperature\": 0}}\n"
    "                if os.environ.get(\"CB_FORMAT_JSON\") == \"1\":\n"
    "                    body[\"format\"] = \"json\"\n"
    "            else:\n"
    "                body = {\"model\": model,\n"
    "                        \"messages\": [{\"role\": \"user\",\n"
    "                                      \"content\": prompt[:6000]}],\n"
    "                        \"max_tokens\": max(max_tokens, 512) if "
    "name.startswith(\n"
    "                            (\"ollama\", \"openrouter\", \"groq\")) "
    "else max_tokens,\n"
    "                        \"temperature\": 0}\n"
    "            req = urllib.request.Request(\n"
    "                url, data=json.dumps(body).encode(),\n"
    "                headers={**hdrs, \"Content-Type\": "
    "\"application/json\"})")
s = s[:m.start()] + body_new + s[m.end():]
open(p, "w", encoding="utf-8", newline="").write(s)
py_compile.compile(p, doraise=True)
print("CLOUDBRAIN v2: the local-first tier + the native shapes; COMPILE OK")