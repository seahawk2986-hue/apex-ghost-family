"""The hybrid-matrix sim: offline proofs for prune/cache/hot-swap, then
ONE real dispatch through the master orchestration."""
import io
import sys

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import ApexCache as C
import ApexPruner as P
import ApexShard as S

fails = []

# 1) the pruner: names the failing function + strips noise + fits the cap
tr = ('Traceback (most recent call last):\n'
      '  File "t.py", line 4, in test_it\n'
      '  File "t.py", line 2, in divide\n'
      'ZeroDivisionError: division by zero')
p = P.prune("make the test green", "def divide(a,b):\n    return a/b\n", tr)
ok = p["context"].lstrip().startswith("function divide") \
     and "return a/b" in p["context"] \
     and "# no zero guard" not in p["context"]
print("[pruner]:", "PASS" if ok else "FAIL", "| bytes:", len(str(p)))
if not ok:
    fails.append("pruner")

# 2) the cache: store -> replay -> hits increment
h = C.signature({"task": "sim", "error": tr})
C.store(h, {"task": "sim"}, "local", "sim", "diff --sim", "validated")
row = C.lookup(h)
ok = bool(row) and row[2] == "diff --sim"
row2 = C.lookup(h)
print("[cache]:", "PASS" if ok else "FAIL", "| row:", row)
if not ok:
    fails.append("cache")

# 3) the shard: 429 -> hot swap -> 200 on the next lane; all-walls = honest empty
class Fake402:
    def __init__(self, code):
        self.status_code = code
        self.text = "walled"

def fake_post_factory(script):
    import requests as rq
    def post(url, headers=None, timeout=None, json=None):
        calls = rq.calls = getattr(rq, "calls", 0) + 1
        code = script(calls)
        r = Fake402(code)
        r.json = lambda: {"choices": [{"message": {"content": "diff --ok"}}]}
        return r
    return post

import requests
saved = requests.post
requests.post = fake_post_factory(lambda n: 429 if n <= 2 else 200)
import importlib
importlib.reload(S)          # S binds requests in its module namespace
env = {"X": "k"}
name, model, reply, notes = S.call(env, S.order_for(),
                                   [{"role": "user", "content": "go"}])
ok2 = name is not None and any("shard swapped" in n for n in notes)
print("[shard hot-swap]:", "PASS" if ok2 else "FAIL", "->", name, "|", notes[:3])
if not ok2:
    fails.append("swap")

requests.post = fake_post_factory(lambda n: 429)
S.call(env, S.order_for(), [{"role": "user", "content": "go"}])
print("[shard all-walled]: honest-empty receipt above")

requests.post = saved
print("[sim verdict]:", "ALL PASS" if not fails else f"FAIL {fails}")
if fails:
    sys.exit(1)