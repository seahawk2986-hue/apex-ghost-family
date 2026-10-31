import os, sys, json, ast, time, shutil, re, subprocess, threading
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks
import uvicorn, requests

R = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
from ApexMemory import ApexMemory
MEM = ApexMemory()
try:
    from ApexPacing import PACER
except Exception:
    PACER = None
import sys as _sys
_sys.path.insert(0, os.path.join(R, "Scripts"))
try:
    from ApexVersions import snapshot as _snapshot
    from ApexSkills import distill as _distill, curriculum as _curriculum
except Exception:
    _snapshot = None
    _distill = None
    _curriculum = None
try:
    from ApexCloudLanes import ask as cloud_ask
except Exception:
    cloud_ask = None
try:
    from HardwareGovernor import HardwareGovernor as _HG_cls
except Exception:
    _HG_cls = None
_HG = _HG_cls() if _HG_cls else None
L = os.path.join(R, "Logs")
Q, M, I = os.path.join(R, "apex_tasks.txt"), os.path.join(L, "reward_telemetry.json"), os.path.join(R, "inbound_adaptations.txt")
U = os.environ.get("APEX_LLM_URL", "http://127.0.0.1:1234/v1/chat/completions")
os.makedirs(L, exist_ok=True)

class FriendPayload(BaseModel): message: str

def log(lyr, msg):
    print(f"[{lyr.upper()}] {msg}")
    path = os.path.join(L, f"{lyr}.log")
    try:
        if os.path.exists(path) and os.path.getsize(path) > 5 * 1024 * 1024:
            os.replace(path, path + ".1")   # bounded logs: rotate at 5MB
        with open(path, "a", encoding="utf-8") as f: f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except OSError:
        pass  # logging must never crash the loop

def query_ds(p):
    try:
        r = requests.post(U, json={"model": "deepseek-r1-distill-llama-8b", "messages": [{"role": "user", "content": p}], "temperature": 0.1, "stream": False, "max_tokens": 800}, timeout=300)
        if r.status_code == 200:
            choices = r.json().get("choices", [])
            if choices and isinstance(choices, list):
                return choices[0].get("message", {}).get("content", "").strip()
        # non-200 (model unloaded/unloaded mid-call) is a drop too - never silent
        log("system", f"DeepSeek HTTP {r.status_code} - bursting planner thought to cloud lanes")
        if cloud_ask: return cloud_ask(p, max_tokens=700)
    except Exception as e:
        log("system", f"DeepSeek drop: {e} - bursting planner thought to cloud lanes")
        if cloud_ask: return cloud_ask(p, max_tokens=700)
    return ""

def query_qw(p, schema=False):
    payload = {"model": "qwen2.5-coder-7b-instruct", "messages": [{"role": "user", "content": p}], "temperature": 0.2, "stream": False}
    if schema: payload["response_format"] = {"type": "json_object"}
    payload["max_tokens"] = 1600
    try:
        r = requests.post(U, json=payload, timeout=120.0)
        if r.status_code == 200:
            choices = r.json().get("choices", [])
            if choices and isinstance(choices, list):
                return choices[0].get("message", {}).get("content", "").strip()
        log("system", f"Qwen HTTP {r.status_code} - bursting coding task to cloud lanes")
        if cloud_ask: return cloud_ask(p, max_tokens=1600)
    except Exception as e:
        log("system", f"Qwen drop: {e} - bursting coding task to cloud lanes")
        if cloud_ask: return cloud_ask(p, max_tokens=1600)
    return ""

def _apply_patches(cur_full, patch_out):
    """Apply Aider-style SEARCH/REPLACE blocks (minimal-diff editing).
    Every SEARCH must match the current content exactly and exactly once.
    Returns the patched full content, or None if nothing could be applied."""
    if not patch_out:
        return None
    blocks = re.findall(
        r"<<<<<<< SEARCH\n(.*?)\n?=======\n(.*?)\n?>>>>>>> REPLACE",
        patch_out, re.DOTALL)
    if not blocks:
        return None
    text, applied = cur_full, 0
    for old, new in blocks:
        if old and text.count(old) == 1:
            text = text.replace(old, new)
            applied += 1
    return text if applied else None

def ext_code(o, ex):
    if not o: return ""
    m = re.search(r"```powershell\s*(.*?)\s*```" if ex == ".ps1" else r"```python\s*(.*?)\s*```", o, re.DOTALL | re.IGNORECASE)
    if m: return m.group(1).strip()
    gm = re.search(r"```\s*(.*?)\s*```", o, re.DOTALL)
    return gm.group(1).strip() if gm else o.strip()

LEDGER = os.path.join(R, "Config", "RewardLedger.json")

def _shell_destructive(node):
    """True if a Call node's string constants form a destructive shell command."""
    strs = []
    for c in ast.walk(node):
        if isinstance(c, ast.Constant) and isinstance(c.value, str):
            strs.append(c.value.strip().lower())
    if any(("rm -rf" in s) or ("rmdir" in s) or ("format c" in s) or ("del /" in s) for s in strs):
        return True
    toks = [s for s in strs if s]
    _OFFENSIVE_TOKENS = ("rm", "rmdir", "del", "del.exe", "rd", "format", "erase",
                         "shutdown", "logoff", "restart", "psshutdown")
    if toks and toks[0] in _OFFENSIVE_TOKENS:
        return True
    if any(t == "shutdown" for t in toks):
        return True
    return False

def _load_ledger():
    try:
        with open(LEDGER, "r", encoding="utf-8-sig") as f: return json.load(f)
    except Exception: return {}

def _save_ledger(lg):
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "w", encoding="utf-8") as f: json.dump(lg, f, indent=1)
    except Exception: pass

def _bump_ledger(fn, base_dict, scr, success):
    """Ledger update: attempts/successes/streaks + per-file best tracking."""
    lg = _load_ledger()
    rec = lg.get(fn) or {"best": 0.0, "best_base": 0.0, "attempts": 0, "successes": 0, "streak": 0}
    rec["attempts"] = rec.get("attempts", 0) + 1
    if success:
        rec["successes"] = rec.get("successes", 0) + 1
        rec["streak"] = rec.get("streak", 0) + 1
        try: bb = sum(float(v) for v in (base_dict or {}).values())
        except Exception: bb = 0.0
        rec["best_base"] = max(float(rec.get("best_base", 0.0) or 0.0), bb)
        rec["best"] = max(float(rec.get("best", 0.0) or 0.0), float(scr or 0.0))
    else:
        rec["streak"] = 0
    lg[fn] = rec
    _save_ledger(lg)

def score_code(fn, c, res, prev_res=None):
    """Multi-dimensional reward (deterministic, no model calls):
    syntax 30 + safety 25 + runtime 20 + output-proof 15 + progress 10.
    Streak/minimal bonuses are applied in heal. REGRESSION and NO-OP
    candidates are flagged and the write gate refuses them."""
    s, m = 0.0, {"syntax": 0, "safety": 0, "runtime": 0, "output": 0, "progress": 0}
    if not c:
        return 0.0, {"syntax": 0, "error": "empty code"}
    try:
        root = ast.parse(c, filename=fn, mode="exec"); s += 30.0; m["syntax"] = 30
    except Exception as e:
        log("reward", f"Syntax error: {e}"); return 0.0, m
    danger = False
    penalty = 0
    # Resolve import aliases FIRST so "import shutil as s; s.rmtree()" is caught.
    _aliases = {}
    for n0 in ast.walk(root):
        if isinstance(n0, ast.Import):
            for _a in n0.names:
                if _a.asname:
                    _aliases[_a.asname] = _a.name
        elif isinstance(n0, ast.ImportFrom) and n0.module:
            for _a in n0.names:
                if _a.asname:
                    _aliases[_a.asname] = f"{n0.module}.{_a.name}"
    _DANGEROUS_MODULES = ("os", "shutil", "subprocess", "ctypes")
    for n in ast.walk(root):
        # VETO: importing ctypes = raw host-API escape vector
        if isinstance(n, ast.Import):
            for _a in n.names:
                if _a.name.split(".")[0] == "ctypes":
                    danger = True
        elif isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "ctypes":
            danger = True
        if not isinstance(n, ast.Call):
            continue
        meth = getattr(n.func, "attr", "")
        raw_base = getattr(getattr(n.func, "value", None), "id", "") or ""
        base_id = _aliases.get(raw_base, raw_base).split(".")[0]
        # FULL VETO: mass deletion or shell-out from evolving candidates
        if (meth == "rmtree" and base_id in ("os", "shutil")) or \
           (meth in ("system", "popen") and base_id in ("os",)):
            danger = True
        # FULL VETO: getattr obfuscation - ANY getattr(<mod>, 'dangerous') call.
        # The module may arrive as a Name reference, Attribute chain, or string.
        if isinstance(n.func, ast.Name) and getattr(n.func, "id", "") == "getattr":
            _args = list(getattr(n, "args", []))
            _mod_name = None
            if _args:
                _m0 = _args[0]
                if isinstance(_m0, ast.Name):
                    _mod_name = _aliases.get(_m0.id, _m0.id).split(".")[0]
                elif isinstance(_m0, ast.Attribute):
                    _mod_name = (_aliases.get(getattr(_m0, "attr", ""), getattr(_m0, "attr", "")) or getattr(_m0, "attr", "")).split(".")[0]
                elif isinstance(_m0, ast.Constant) and isinstance(_m0.value, str):
                    _mod_name = _aliases.get(_m0.value, _m0.value).split(".")[0]
            if len(_args) > 1 and _mod_name in _DANGEROUS_MODULES:
                _a1 = _args[1]
                if isinstance(_a1, ast.Constant) and isinstance(_a1.value, str) and \
                        _a1.value in ("system", "popen", "rmtree", "remove", "unlink", "kill", "terminate"):
                    danger = True
        # HARD PENALTY: casual file deletion (temp cleanup patterns)
        if meth in ("remove", "unlink") and base_id in ("os", "pathlib"):
            penalty += 15
        # FULL VETO: subprocess/os shell whose command is destructive
        if isinstance(n.func, ast.Attribute) and getattr(n.func, "attr", "") in ("run", "system", "Popen", "popen", "check_output", "call"):
            _mod = base_id
            if _mod in ("subprocess", "os") and _shell_destructive(n):
                danger = True
        if isinstance(n.func, ast.Name) and getattr(n.func, "id", "") in ("run", "system", "Popen") and _shell_destructive(n):
            danger = True
        # HARD PENALTY: dynamic execution (eval/exec) in evolving candidates
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and getattr(n.func, "id", "") in ("eval", "exec"):
            penalty += 10
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and getattr(n.func, "attr", "") in ("eval", "exec"):
            penalty += 10
    if danger:
        log("security", "CRITICAL SECURITY VETO"); m["safety"] = -100; return 0.0, m
    s += 25.0
    if penalty:
        s -= penalty
        m["safety"] = max(0, 25 - penalty)
        log("reward", f"FS-deletion penalty applied: -{penalty}")
    else:
        m["safety"] = 25
    if res.get("status") == "SUCCESS":
        s += 20.0; m["runtime"] = 20
        prev_out = ((prev_res or {}).get("output") or "").strip()
        cand_out = (res.get("output") or "").strip()
        if cand_out or not prev_out:
            s += 15.0; m["output"] = 15
        else:
            m["behavior_loss"] = True
            log("reward", "BEHAVIOR LOSS: predecessor produced output, candidate is silent.")
    else:
        log("reward", "Runtime degradation.")
    # Static lint (ruff): undefined names are near-certain runtime crashes;
    # unused imports are hygiene. Scored before the ledger comparison so the
    # progress gate sees lint-adjusted quality.
    try:
        _lt = os.path.join(R, f"lint_probe_{abs(hash((fn, len(c)))) % 10**8}.py")
        with open(_lt, "w", encoding="utf-8") as f: f.write(c)
        _r = subprocess.run([sys.executable, "-m", "ruff", "check", "--isolated",
                             "--select", "F821,F401", "--output-format", "concise", _lt],
                            capture_output=True, text=True, timeout=25)
        try: os.remove(_lt)
        except OSError: pass
        if _r.returncode == 1:
            _f821 = sum(1 for _l in (_r.stdout or "").splitlines() if "F821" in _l)
            _f401 = sum(1 for _l in (_r.stdout or "").splitlines() if "F401" in _l)
            _pen = 10 * _f821 + 3 * _f401
            if _pen:
                s -= _pen
                m["lint_penalty"] = _pen
                log("reward", f"Lint: {_f821} undefined-name(s), {_f401} unused-import(s) -> -{_pen}")
        # Security SAST (bandit): HIGH findings -15, MEDIUM -5 (industry scanner)
        _b = subprocess.run([sys.executable, "-m", "bandit", "-q", "-f", "json", _lt],
                            capture_output=True, text=True, timeout=40)
        if _b.returncode in (0, 1):
            try:
                _bres = json.loads(_b.stdout or "{}").get("results", [])
                _hi = sum(1 for _r0 in _bres if _r0.get("issue_severity") == "HIGH")
                _me = sum(1 for _r0 in _bres if _r0.get("issue_severity") == "MEDIUM")
                _bpen = 15 * _hi + 5 * _me
                if _bpen:
                    s -= _bpen
                    m["bandit_penalty"] = _bpen
                    log("reward", f"Bandit: {_hi} HIGH, {_me} MEDIUM security finding(s) -> -{_bpen}")
            except Exception:
                pass
        try: os.remove(_lt)
        except OSError: pass
    except Exception:
        pass
    base = s
    rec = (_load_ledger().get(fn) or {})
    pb = float(rec.get("best_base", 0.0) or 0.0)
    if pb <= 0.0 or base > pb:
        s += 10.0; m["progress"] = 10
    else:
        m["progress"] = 0
        if not m.get("behavior_loss"): m["noop"] = True
        log("reward", f"NO-OP/REGRESSION: base {base:.0f} vs ledger best {pb:.0f}")
    try:
        with open(M, "a", encoding="utf-8") as tf: tf.write(json.dumps({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "target_file": fn, "total_reward": s, "metrics_matrix": m}) + "\n")
    except Exception: pass
    return s, m

DOCKER_SANDBOX = {"checked": 0, "available": None, "last_check": 0.0}

def _docker_engine():
    d = DOCKER_SANDBOX
    if time.time() - d["last_check"] > 60:   # re-probe at most every 60s
        try:
            r = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=20)
            d["available"] = (r.returncode == 0)
        except Exception:
            d["available"] = False
        d["last_check"] = time.time()
        d["checked"] += 1
    return bool(d["available"])

def _docker_sandbox(fn, code, image="python:3.12-slim"):
    """Execute a candidate in a disposable, sealed container. The candidate
    physically CANNOT read host files, hosts' env, or reach the network."""
    droot = os.path.join(R, "Config", "sandbox_runs")
    d = os.path.join(droot, f"{int(time.time() * 1000)}_{fn}")
    os.makedirs(d, exist_ok=True)
    tp = os.path.join(d, fn)
    with open(tp, "w", encoding="utf-8") as f: f.write(code)
    name = f"apexev-sbx-{os.path.basename(d)[:32]}"
    try:
        res = subprocess.run(
            ["docker", "run", "--rm", "--network", "none", "--name", name,
             "--read-only", "--tmpfs", "/tmp",
             "-v", f"{d}:/sandbox", "-w", "/sandbox",
             image, "python", f"/sandbox/{fn}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45)
        return {"status": "SUCCESS" if res.returncode == 0 else "CRASHED",
                "error": None if res.returncode == 0 else (res.stderr or "container nonzero"),
                "output": (res.stdout or ""), "isolated": True}
    except subprocess.TimeoutExpired:
        return {"status": "CRASHED", "error": "sandbox timeout (container)", "output": "", "isolated": True}
    except Exception as e:
        return {"status": "CRASHED", "error": f"sandbox failure: {e}", "output": "", "isolated": False}
    finally:
        try:
            subprocess.run(["docker", "kill", name], capture_output=True, timeout=8)
            shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass

def sandbox(fn, c):
    """Container-first execution with honest host fallback. A broken Docker
    never changes candidate judgment - it only relaxes isolation, visibly."""
    if _docker_engine():
        res = _docker_sandbox(fn, c)
        if res.get("isolated") and (res.get("status") == "SUCCESS" or res.get("error") not in (None, "sandbox failure")):
            return res
        log("reward", f"Container sandbox trouble ({str(res.get('error'))[:60]}) - host fallback")
    t = os.path.join(R, f"speculative_test_{fn}")
    if os.path.exists(t): os.remove(t)
    with open(t, "w", encoding="utf-8") as f: f.write(c)
    try:
        res = subprocess.run([sys.executable, t], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8, cwd=R)
        if os.path.exists(t): os.remove(t)
        return {"status": "SUCCESS" if res.returncode == 0 else "CRASHED", "error": None if res.returncode == 0 else res.stderr, "output": (res.stdout or ""), "isolated": False}
    except Exception as e:
        if os.path.exists(t): os.remove(t)
        log("reward", f"Sandbox did not complete cleanly: {e}")
        return {"status": "CRASHED", "error": f"Sandbox failure: {e}", "output": "", "isolated": False}

def _set_strategy(text):
    """Deliberative scratchpad: carry working intent across cycles."""
    try:
        os.makedirs(os.path.join(R, "Config"), exist_ok=True)
        with open(os.path.join(R, "Config", "ApexStrategy.json"), "w", encoding="utf-8") as f:
            json.dump({"strategy": text[:220], "updated": time.strftime("%Y-%m-%d %H:%M:%S")}, f)
    except Exception:
        pass


def _container_run_tests(fn, code, tests_code):
    """Execute a candidate + its intent-derived test suite inside the sealed
    container. METRICS ONLY: results never gate rewards (self-grade gaming)."""
    droot = os.path.join(R, "Config", "sandbox_runs")
    d = os.path.join(droot, f"{int(time.time() * 1000)}_tdd_{fn}")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, fn), "w", encoding="utf-8") as f: f.write(code)
    with open(os.path.join(d, "run_tests.py"), "w", encoding="utf-8") as f: f.write(tests_code)
    name = f"apexev-tdd-{os.path.basename(d)[:28]}"
    try:
        res = subprocess.run(
            ["docker", "run", "--rm", "--network", "none", "--name", name,
             "--read-only", "--tmpfs", "/tmp",
             "-v", f"{d}:/sandbox", "-w", "/sandbox",
             "python:3.12-slim", "python", "/sandbox/run_tests.py"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45)
        return {"status": "PASSED" if (res.returncode == 0 and "ALL TESTS PASSED" in (res.stdout or "")) else "FAILED",
                "output": (res.stdout or "")[:1200],
                "error": (res.stderr or "")[:300] if res.returncode else None}
    except Exception as e:
        return {"status": "ERROR", "output": "", "error": str(e)[:200]}
    finally:
        try:
            shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass

def heal(fn, intent, code, minimal=False, predicted=None, tests_code=None, skill_used=None):
    ex = os.path.splitext(fn)[1].strip().lower()
    # Predecessor behavior baseline (computed ONCE - the live file is the
    # predecessor until a candidate actually passes the write gate).
    try:
        with open(os.path.join(R, fn), "r", encoding="utf-8") as f: _prev_code = f.read()
        prev_res = sandbox(fn, _prev_code)
    except Exception:
        prev_res = {"status": "SKIP", "output": ""}
    for traj in range(3):
        log("evolution", f"Optimizing {fn} (Pass {traj+1}/3)...")
        res = sandbox(fn, code)
        scr, m = score_code(fn, code, res, prev_res)
        _streak = int((_load_ledger().get(fn) or {}).get("streak", 0) or 0)
        if res.get("status") == "SUCCESS":
            scr += min(9.0, 3.0 * (_streak + 1)); m["streak_bonus"] = min(9.0, 3.0 * (_streak + 1))
        if minimal:
            scr += 2.0; m["minimal_diff"] = 2
        # World-model calibration: EVERY trajectory is scored against a
        # prediction (critic forecast / strategy prior) - real forecast samples.
        prev_out = ((prev_res or {}).get("output") or "").strip()
        cand_out = (res.get("output") or "").strip()
        actual = ("gain" if len(cand_out) > len(prev_out)
                  else "loss" if len(cand_out) < len(prev_out) else "parity")
        expected = (predicted or ("parity" if minimal else "variable")) if traj == 0 else "gain-repair"
        try:
            MEM.record_event("calibration",
                             f"{fn} pass {traj+1} predicted {expected}, actual {actual} "
                             f"(strategy={'minimal' if minimal else 'rewrite'})",
                             file=fn, predicted=expected, actual=actual,
                             strategy="minimal" if minimal else "rewrite")
            if traj == 0 and minimal:
                lg = _load_ledger()
                rec = lg.setdefault(fn, {"best": 0.0, "best_base": 0.0, "attempts": 0, "successes": 0, "streak": 0})
                rec["parity_total"] = rec.get("parity_total", 0) + 1
                if actual == "parity":
                    rec["parity_hits"] = rec.get("parity_hits", 0) + 1
                _save_ledger(lg)
        except Exception:
            pass
        try: MEM.record_event("evolution_pass", f"{fn} pass {traj+1}/3 scored {scr:.0f} ({res['status']})", file=fn)
        except Exception: pass
        if scr >= 100.0 and not m.get("behavior_loss") and not m.get("noop"):
            tp, a = os.path.join(R, fn), os.path.join(R, "Backup_Archive")
            os.makedirs(a, exist_ok=True)
            if os.path.exists(tp): shutil.copy2(tp, os.path.join(a, f"{fn}.bak"))
            with open(tp, "w", encoding="utf-8") as f: f.write(code)
            log("system", f"SUCCESS: Written {fn}")
            try:
                MEM.record_event("success", f"Written {fn} (reward {scr:.0f}) with intent: {intent[:150]}", file=fn)
                MEM.remember(f"Lesson: successfully evolved {fn} (reward {scr:.0f}). What worked: {intent[:180]}", kind="lesson")
            except Exception: pass
            try:
                if _snapshot:
                    _snapshot(fn, msg=f"evolution: {fn} reward {scr:.0f}")
                if _distill:
                    _distill(fn, intent, scr)  # certify as a skill
                _set_strategy(f"continue {fn} (success streak {(_streak or 0) + 1}); keep changes surgical; verify output parity")
                if skill_used:
                    try:
                        from ApexSkills import mark_win
                        mark_win(skill_used)   # which certified skills actually win
                    except Exception:
                        pass
                try:
                    from ApexGuard import seal_file as _seal
                    _seal(fn)   # integrity manifest: tamper with the evolution -> boot fails loudly
                except Exception:
                    pass
                # TDD verification (metrics-only: tests inform, never gate rewards)
                try:
                    if cloud_ask and _docker_engine():
                        _tests_raw = cloud_ask(
                            f"You are Apex's TDD unit for the file {fn}.\nTask intent: {intent}\n"
                            f"Write a PLAIN-python test script (no external deps) that verifies this code:\n"
                            f"```python\n{code[:3500]}\n```\n"
                            "The candidate already exists at /sandbox/candidate.py when your tests run; "
                            "your script MUST start with:\n"
                            "exec(compile(open('/sandbox/candidate.py').read(), 'candidate', 'exec'))\n"
                            "then run REAL asserts on the resulting globals/functions, print actual results, "
                            "and print 'ALL TESTS PASSED' as the final successful statement. "
                            "Output ONLY the test script in one ```python block.",
                            max_tokens=700)
                        _tc = ext_code(_tests_raw or "", ".py")
                        if _tc:
                            _tdd = _container_run_tests(fn, code, _tc)
                            MEM.record_event("tdd", f"{fn}: {_tdd['status']} on intent-derived tests",
                                             file=fn, result=_tdd["status"])
                            log("system", f"TDD: {_tdd['status']} for {fn}")
                except Exception:
                    pass
            except Exception:
                pass
            # Post-write spec check: re-run the intent-derived tests in the
            # container against the newly written file (drift detection).
            try:
                if tests_code and _docker_engine():
                    _tdd3 = _container_run_tests(fn, code, tests_code)
                    MEM.record_event("tdd", f"{fn} post-write spec check: {_tdd3.get('status')}",
                                     file=fn, result=_tdd3.get("status"))
                    log("system", f"Post-write TDD: {_tdd3.get('status')}")
            except Exception:
                pass
            _bump_ledger(fn, {k: m.get(k, 0) for k in ("syntax", "safety", "runtime", "output")}, scr, True)
            return True
        log("evolution", "Threshold unmet. Patching with Qwen coder...")
        fence = "powershell" if ex == ".ps1" else "python"
        code = ext_code(query_qw(
            f"You are Apex's code repair unit. Your patch for {fn} crashed.\nIntent: {intent}\n"
            f"[BAD CODE]:\n{code}\n[ERROR]:\n{res['error']}\n"
            f"Fix the bugs completely. Keep the working parts intact. "
            f"Output ONLY the full corrected file in a single ```{fence} fenced block."), ex)
    _bump_ledger(fn, None, None, False)
    _set_strategy("switch to a different file; use smaller surgical changes; verify behavior parity against the ledger best")
    try:
        MEM.remember(f"Failure lesson: {fn} rejected after 3 repair passes. Last error: {str((res or {}).get('error') or (res or {}).get('output') or 'unknown')[:160]}. Next time: smaller, surgical change.", kind="lesson")
    except Exception: pass
    return False

CORE_MODULES = {"run_apex_evolution.py", "optimized_agent.py", "apex_ipce_engine.py", "apexmemory.py", "apexwebscraper.py", "apexnetscraper.py"}

def plan():
    log("planner", "Evaluating workspace...")
    # Only .py files: the scorer (ast.parse) can't evaluate .ps1 targets, so
    # proposing them wastes an entire cycle every time.
    try: all_f = [f for f in os.listdir(R) if f.lower().endswith('.py') and f.lower() not in CORE_MODULES]
    except OSError as e:
        log("system", f"Workspace listing failed: {e}")
        return False
    mem_hist = "None yet."
    try:
        _rows = MEM.recall("workspace optimization lessons errors decisions", k=4, min_similarity=0.20)
        if _rows: mem_hist = "\n".join(f"- ({r['kind']}, {r['similarity']}) {r['text'][:160]}" for r in _rows)
    except Exception: pass
    hist = "No history."
    if os.path.exists(M):
        with open(M, "r", encoding="utf-8") as f: lines = f.readlines()[-6:]
        if lines: hist = "\n".join([f"File: {json.loads(l)['target_file']} Reward: {json.loads(l)['total_reward']}" for l in lines])
    ledger_hist = "none yet"
    try:
        _lg = _load_ledger()
        _tops = sorted(_lg.items(), key=lambda kv: -(kv[1].get("best", 0) or 0))[:5]
        if _tops: ledger_hist = "; ".join(f"{k}: best {v.get('best', 0):.0f}, streak {v.get('streak', 0)}" for k, v in _tops)
    except Exception: pass
    # Editing-strategy calibration: is Apex's world model accurate?
    # Working strategy carried from the last cycle (deliberative scratchpad)
    strat = "none recorded yet"
    try:
        with open(os.path.join(R, "Config", "ApexStrategy.json"), "r", encoding="utf-8") as f:
            _sj = json.load(f)
        strat = _sj.get("strategy", "")[:200] or strat
    except Exception:
        pass
    # Self-issued curriculum: proposals from real evidence (bandit + failures + human queue)
    curric = "none"
    try:
        if _curriculum:
            curric = "; ".join(_curriculum(3)) or "none"
    except Exception:
        pass
    calib = "no data yet"
    try:
        th = sum(v.get("parity_hits", 0) for v in _lg.values())
        tt = sum(v.get("parity_total", 0) for v in _lg.values())
        if tt:
            calib = f"minimal-diff behavior-parity prediction accuracy {th}/{tt} ({100.0 * th / tt:.0f}%)"
    except Exception:
        pass
    neglect = "none"
    try:
        _stale = [(k, v.get("attempts", 0)) for k, v in sorted(_lg.items(), key=lambda kv: kv[1].get("attempts", 0)) if k in all_f][:4]
        if _stale: neglect = ", ".join(f"{k} ({a} attempts so far)" for k, a in _stale)
    except Exception: pass
    # Reflexion-style pre-brief: condense the last cycles for the planner.
    reflect = "no recent cycle notes"
    try:
        _ev = [e for e in MEM.recent_events(8) if e.get("kind") in ("evolution_pass", "error", "success")]
        if _ev: reflect = " | ".join(f"{e['kind']}: {e['text'][:90]}" for e in _ev[-3:])
    except Exception: pass
    # Theory of mind: recent private exchanges with Andrew inform context.
    talks = "none"
    try:
        _tv = MEM.recent_events(15, kind="conversation") or []
        _tv = [e for e in _tv if "Andrew:" in e.get("text", "")]
        if _tv: talks = " | ".join(_t["text"][8:88] for _t in _tv[-3:])
    except Exception: pass
    # Self-model: the planner reads its own identity card every cycle.
    selfcard = ""
    try:
        with open(os.path.join(R, "Config", "ApexSelf.json"), "r", encoding="utf-8") as f:
            selfcard = f.read()[:900]
    except Exception:
        pass
    # Interconnection: certified skill library -> planner awareness.
    skills_line = ""
    try:
        with open(os.path.join(R, "Config", "SkillRegistry.json"), "r", encoding="utf-8") as f:
            sk = json.load(f)
        _names = sorted(sk.keys(), reverse=True)[:3]
        skills_line = f"{len(sk)} certified skill(s); latest: {', '.join(_names)}" if sk else "none yet"
    except Exception:
        skills_line = "none yet"
    # Interconnection: research cache -> planner awareness.
    research_line = ""
    try:
        with open(os.path.join(R, "Config", "ResearchCache.json"), "r", encoding="utf-8") as f:
            rc = json.load(f)
        if rc:
            research_line = f"{len(rc)} cached research note(s) on file for: {', '.join(list(rc.keys())[-3:])}"
    except Exception:
        research_line = ""
    # --- Phase 1: DeepSeek-R1 THINKS (planning only, no code) -----------------
    o = query_ds(f"You are Apex automation head. Choose ONE file from [{', '.join(all_f)}] to optimize.\n"
                f"Recent reward history:\n{hist}\n"
                f"Long-term lessons/topical memories:\n{mem_hist}\n"
                f"Per-file reward ledger (best first):\n{ledger_hist}\n"
                f"Neglected files worth considering (exploration):\n{neglect}\n"
                f"Reflection on recent cycles:\n{reflect}\n"
                f"Recent private exchanges with Andrew (your human):\n{talks}\n"
                f"Self-model (identity, engines, limits):\n{selfcard}\n"
                f"Self-issued curriculum (proposed objectives):\n{curric}\n"
                f"Certified skill library:\n{skills_line}\n"
                f"Reference notes on file (research cache):\n{research_line}\n"
                f"Working strategy from last cycle:\n{strat}\n"
                "Rules: do NOT target core modules, do NOT propose destructive code.\n"
                "Return ONLY strict JSON (no code, no explanation): {\n  \"target_file\": \"filename.ext\",\n  \"task_intent\": \"one-sentence goal\",\n  \"change_brief\": \"2-3 sentences on the exact change to make\"\n}")
    if not o:
        return False

    def _parse_plan(raw):
        cleaned = raw.split("</think>")[-1].strip()
        if cleaned.startswith("```"): cleaned = re.sub(r"^```json\s*|\s*```$", "", cleaned, flags=re.IGNORECASE).strip()
        s_idx, e_idx = cleaned.find("{"), cleaned.rfind("}") + 1
        if s_idx < 0 or e_idx <= s_idx: return None
        return json.loads(cleaned[s_idx:e_idx])

    try:
        d = _parse_plan(o)
    except Exception:
        d = None
    if d is None:
        # Grammar-constrained structured-output repair: json_object mode forces
        # the token stream itself to schema compliance (no prose can leak in).
        log("planner", "Plan JSON failed direct parse; invoking grammar-constrained repair...")
        rep = query_qw(
            "Convert the following into ONE strict JSON object with exactly these keys: "
            "target_file (string), task_intent (string), change_brief (string). "
            "Ignore any reasoning noise. Return ONLY the JSON object.\n" + o[-1500:], schema=True)
        try:
            d = _parse_plan(rep)
        except Exception:
            d = None
    if d is None:
        log("planner", "Plan discarded: unparseable even after constrained repair")
        return False
    tf = str(d.get("target_file", "")).strip()
    intent = str(d.get("task_intent", "")).strip()
    brief = str(d.get("change_brief", "")).strip()
    if not tf or not intent or tf.lower() in CORE_MODULES or not os.path.exists(os.path.join(R, tf)):
        log("planner", f"Plan rejected (invalid target: {tf or 'none'})")
        return False

    # Self-consistency planning: modal target wins the vote (DeepSeek + 2 Groq
    # ballots, confidence-weighted). Majority agreement = proceed confidently;
    # split votes = conservative coding.
    _ensemble = ""
    try:
        if cloud_ask:
            _votes = [tf]
            _results = {}

            def _vote(i):
                try:
                    _v = cloud_ask(
                        "Planning vote. Choose ONE file from [" + ", ".join(all_f[:12]) +
                        "] to optimize. Reply ONLY strict JSON: {\"target_file\": \"a.py\", "
                        "\"task_intent\": \"...\", \"change_brief\": \"...\", "
                        "\"confidence\": 0.0-1.0}. History: " + hist[-240:],
                        max_tokens=250)
                    if _v and "{" in _v and "}" in _v:
                        _j = json.loads(_v[_v.find("{"): _v.rfind("}") + 1])
                        _results[i] = (str(_j.get("target_file", "")).strip(),
                                       float(_j.get("confidence", 0.5) or 0.5))
                except Exception:
                    pass

            _vts = [threading.Thread(target=_vote, args=(i,), daemon=True) for i in range(2)]
            for _t in _vts:
                _t.start()
            for _t in _vts:
                _t.join(timeout=26)
            _votes.extend(r[0] for r in _results.values() if r[0])
            _confid = [r[1] for r in _results.values()]
            _counts = {}
            for _v in _votes:
                _k = _v.lower()
                _counts[_k] = _counts.get(_k, 0) + 1
            _modal = max(_counts.items(), key=lambda kv: kv[1])[0]
            _agree = sum(1 for _v in _votes if _v.lower() == _modal)
            if _modal != tf.lower():
                _ensemble = (f"planning votes {dict(_counts)}: modal target '{_modal}' DISAGREES "
                             "with DeepSeek - implement conservatively, changes surgical")
            elif _agree < len(_votes):
                _ensemble = f"planning votes {dict(_counts)}: majority agrees, {_agree}/{len(_votes)}"
            else:
                _ensemble = f"planning votes: unanimous ({len(_votes)}/{len(_votes)} agree)"
            if _confid:
                _ensemble += f" | vote confidences: {[round(c, 2) for c in _confid]}"
            try:
                MEM.record_event("planning_vote",
                                 f"votes={dict(_counts)} modal={_modal} agree={_agree}/{len(_votes)}",
                                 file=tf, agree=_agree, total=len(_votes))
            except Exception:
                pass
    except Exception:
        _ensemble = ""
    if _ensemble:
        log("planner", f"Ensemble: {_ensemble[:130]}")

    # Disagreement resolution: when planners split, a deciding vote reviews
    # BOTH positions and picks the better target for THIS cycle.
    if "DISAGREES" in _ensemble:
        try:
            if cloud_ask:
                _modal_name = _modal if "_modal" in dir() else ""
                _dec = cloud_ask(
                    "Two planning agents disagree on the best evolution target. "
                    f"DeepSeek argues for '{tf}' ({intent[:120]}). Groq voters argue for '{_modal_name}'. "
                    "Decide which target is better for autonomous evolution RIGHT NOW "
                    "(reward history favors stability; novelty favors exploration). "
                    "Reply ONLY strict JSON: {\"final_target\": \"filename.py\"}",
                    max_tokens=150)
                if _dec and "{" in _dec:
                    _dj = json.loads(_dec[_dec.find("{"): _dec.rfind("}") + 1])
                    _fin = str(_dj.get("final_target", "")).strip()
                    if _fin and _fin.lower() in [f.lower() for f in all_f]:
                        if _fin.lower() != tf.lower():
                            tf = _fin
                            _ensemble = f"disagreement RESOLVED by deciding vote -> {tf}"
                        else:
                            _ensemble = f"disagreement RESOLVED by deciding vote -> keeps {tf}"
                        log("planner", f"Ensemble: {_ensemble[:130]}")
        except Exception:
            pass

    # Perception upgrade: detect NEW files since last cycle (an evolving agent
    # should notice its environment changing - including files it creates).
    _perception = ""
    try:
        _kp = os.path.join(R, "Config", "known_files.json")
        _known = []
        try:
            with open(_kp, "r", encoding="utf-8") as f:
                _known = json.load(f).get("files", [])
        except Exception:
            _known = []
        _new = [f for f in all_f if f not in _known]
        if _new:
            _perception = f"NEW FILE(S) DETECTED since last cycle: {', '.join(_new[:4])} - exploring them enriches experience"
            log("planner", f"Perception: {_perception}")
        os.makedirs(os.path.dirname(_kp), exist_ok=True)
        with open(_kp, "w", encoding="utf-8") as f:
            json.dump({"files": sorted(all_f), "updated": time.strftime("%Y-%m-%d %H:%M:%S")}, f)
    except Exception:
        pass

    # Adaptive edit strategy: minimal-diff vs full-rewrite weighted by the
    # agent's MEASURED parity-prediction accuracy (world model feedback loop).
    _prefer_minimal = True
    try:
        _th = sum(v.get("parity_hits", 0) for v in _lg.values())
        _tt = sum(v.get("parity_total", 0) for v in _lg.values())
        if _tt >= 3:
            _rate = _th / _tt
            _prefer_minimal = _rate >= 0.7
            log("planner", f"Edit-strategy: minimal-diff parity {_th}/{_tt} ({100 * _rate:.0f}%) -> "
                           f"{'minimal-diff preferred' if _prefer_minimal else 'full-rewrite preferred'}")
    except Exception:
        pass
    if _perception:
        log("planner", f"Perception: {_perception[:100]}")

    # Critical thinking: SOCRATIC interrogation of the plan BEFORE any code
    # is written. Assumptions get surfaced, pre-mortem failures become coder
    # guards, and 'abort' verdicts self-reject the plan outright.
    _think, _shrink, _guards = None, False, []
    try:
        if cloud_ask:
            sys.path.insert(0, os.path.join(R, "Scripts"))
            from ApexThink import review as _think_review
            _think = _think_review(
                f"Optimize {tf}: {intent}. Brief: {brief}",
                f"History: {hist[-280:]} | Ledger bests: {ledger_hist} | Calibration: {calib}",
                cloud_ask)
    except Exception:
        _think = None
    if _think:
        try:
            MEM.record_event("thinking", f"{tf}: socratic verdict={_think.get('verdict')} "
                                        f"assumptions={len(_think.get('assumptions', []) or [])} "
                                        f"pre-mortem factors={len(_think.get('pre_mortem', []) or [])}")
        except Exception:
            pass
        _verdict = str(_think.get("verdict", "proceed"))
        if _verdict == "abort":
            # Abort double-check: one confirmation review prevents over-stalls.
            _reason0 = str(_think.get("reason", ""))[:200]
            try:
                from ApexThink import confirm_abort
                if not confirm_abort(f"{tf}: {intent}", _reason0, cloud_ask):
                    _verdict = "shrink"
                    log("planner", "Abort downgraded to SHRINK after confirmation review")
            except Exception:
                pass
        if _verdict == "abort":
            _reason = str(_think.get("reason", ""))[:200]
            log("planner", f"CRITICAL REVIEW ABORTED the plan (confirmed): {_reason}")
            try:
                MEM.record_event("error", f"Plan for {tf} self-aborted by critical review: {_reason}")
                MEM.remember(f"Failure lesson: the plan for {tf} was self-aborted by critical "
                             f"thinking. Reason: {_reason}", kind="lesson")
            except Exception:
                pass
            return False
        if _verdict == "shrink":
            # Borderline verdicts get one confirming Socratic review.
            try:
                _c2 = _think_review(
                    f"Confirm or overturn: a prior review issued verdict SHRINK for this plan: "
                    f"Optimize {tf}: {intent}. Brief: {brief}. Confirm SHRINK only if the "
                    f"risks are genuinely real for this machine.",
                    f"History: {hist[-200:]}",
                    cloud_ask)
                if isinstance(_c2, dict) and str(_c2.get("verdict", "shrink")) == "proceed":
                    _verdict = "proceed"
                    _think["verdict"] = "proceed"
                    log("planner", "SHRINK overturned by second Socratic review - proceeding normally")
            except Exception:
                pass
            if str(_think.get("verdict", _verdict)) == "shrink":
                _shrink = True
                log("planner", "Critical review SHRANK the plan - conservative mode engaged (double-checked)")
        _guards = ([str(g) for g in (_think.get("pre_mortem") or [])[:4]]
                   + [f"re-check: {g}" for g in (_think.get("falsifiers") or [])[:3]])
    _guard_line = ("CRITICAL-THINKING GUARDS (must not violate): " + "; ".join(_guards)) if _guards else ""

    # Skill library retrieval: inject the most relevant CERTIFIED implementation
    # as a reference pattern for the coder (skill-reuse loop).
    _skill_ref = ""
    _used_skill = ""
    try:
        sys.path.insert(0, os.path.join(R, "Scripts"))
        from ApexSkills import find_relevant as _fr, mark_used as _mu
        _sk = _fr(f"{intent} {brief}")
        if _sk:
            _sp = os.path.join(R, _sk["source"])
            if os.path.exists(_sp):
                with open(_sp, "r", encoding="utf-8") as f:
                    _src = f.read()[:3000]
                _skill_ref = (f"CERTIFIED SKILL REFERENCE (a previously VERIFIED implementation "
                              f"of similar work in {_sk['source']}):\n{_src}")
                _mu(_sk["skill_id"])
                _used_skill = _sk["skill_id"]
                try:
                    MEM.record_event("skill_used", f"{_sk['skill_id']} injected (sim {_sk['similarity']})",
                                     skill=_sk["skill_id"])
                except Exception:
                    pass
    except Exception:
        _skill_ref = ""

    log("planner", f"Locked onto: {tf}. DeepSeek plan: {brief[:120]}")
    try:
        with open(os.path.join(R, tf), "r", encoding="utf-8") as f: cur_full = f.read()
    except Exception: return False
    fence = "powershell" if tf.lower().endswith(".ps1") else "python"
    ex = os.path.splitext(tf)[1].strip().lower()

    # Tests-first (spec-then-code): tests are derived from the intent BEFORE
    # any code exists, so verification is independent of the implementation.
    # The coder receives them as the specification it must satisfy.
    _tests_code = ""
    try:
        if cloud_ask:
            _tests_raw = cloud_ask(
                "You are Apex's specification unit. Write a PLAIN-python test script (no "
                "external deps) that strictly verifies the TASK below - assert the observable "
                "behaviors the task requires, edge cases included. The implementation does not "
                "exist yet; write tests that WOULD pass for a correct implementation. The script "
                'will run with the implementation pre-loaded into globals via: '
                "exec(compile(open('/sandbox/candidate.py').read(), 'candidate', 'exec'))\n"
                "Then run REAL asserts based on the task, print actual results, and print "
                "'ALL TESTS PASSED' as the final successful statement - ONLY for a genuinely "
                "correct implementation. Output ONLY the test script in one ```python block.\n\n"
                f"TASK (intent): {intent}\nChange brief: {brief}\nTarget: {tf}\n"
                f"Current file behavior reference (first 2000 chars):\n{cur_full[:2000]}",
                max_tokens=600)
            _tests_code = ext_code(_tests_raw or "", ".py")
            if _tests_code:
                log("planner", f"Spec-first: test suite derived from intent ({len(_tests_code)} chars)")
    except Exception:
        _tests_code = ""
    code = None
    _minimal = False
    patch_out = None
    if _prefer_minimal:
        patch_out = query_qw(
        f"You are Apex's expert coding unit. Apply the requested change with MINIMAL edits.\n"
        f"Target file: {tf}\nIntent: {intent}\nChange brief: {brief}\n"
        f"Second-opinion check: {(_ensemble or 'none')}\n"
        f"{_guard_line}\n"
        f"Conservative mode: {('YES - smallest possible change; assume unvalidated assumptions are false' if _shrink else 'no')}\n\n"
        f"{_skill_ref}\n\n"
        + (f"SPECIFICATION THE RESULT MUST SATISFY (tests derived independently from the intent):\n{_tests_code}\n\n" if _tests_code else "")
        + f"[CURRENT FILE CONTENT]:\n{cur_full[:6000]}\n\n"
        "Output ONLY one or more edit blocks in exactly this format (no fences, no commentary):\n"
        "<<<<<<< SEARCH\n<exact lines to find in the file>\n=======\n<replacement lines>\n>>>>>>> REPLACE\n"
        "Each SEARCH must appear in the current file exactly once. Keep edits as small as possible while "
        "fully implementing the change. Never alter unrelated behavior.")
    if patch_out:
        code = _apply_patches(cur_full, patch_out)
        if code is not None:
            _minimal = True
            log("planner", f"Minimal-diff edit applied ({len(patch_out)} chars of patch)")
    if code is None:
        log("planner", "Minimal-diff unusable; falling back to full-file rewrite")
        code_out = query_qw(
            f"You are Apex's expert coding unit. Implement the following change.\n"
            f"Target file: {tf}\nIntent: {intent}\nChange brief: {brief}\n"
            f"{_guard_line}\n"
            f"Conservative mode: {('YES - smallest possible change; assume unvalidated assumptions are false' if _shrink else 'no')}\n\n"
            + (f"SPECIFICATION THE RESULT MUST SATISFY (tests derived independently from the intent):\n{_tests_code}\n\n" if _tests_code else "")
            + f"[CURRENT FILE CONTENT]:\n{cur_full[:6000]}\n\n"
            f"Rewrite the complete file with the change applied. Keep the valid, working, non-destructive parts of the "
            f"existing structure intact; only make the requested improvement. Output ONLY the full file content "
            f"in a single ```{fence} fenced block. No commentary.")
        code = ext_code(code_out, ex)
    if not code or len(code) < 30:
        log("planner", "Coder produced no usable code. Plan discarded.")
        try: MEM.record_event("error", f"Coder failed on {tf}: empty/blocked output")
        except Exception: pass
        return False

    # Critic pass (constitutional self-refinement): a second model reviews the
    # candidate for hidden hazards BEFORE the sandbox - cheaper than failing.
    _prediction = "variable"
    try:
        if cloud_ask:
            _crit = cloud_ask(
                "You are Apex's code critic. Review the proposed rewrite for hidden hazards: "
                "syntax issues, runtime hazards, behavioral regressions vs the current file, "
                "security problems. ALSO forecast its observable behavior change. Reply ONLY "
                "strict JSON: {\"verdict\": \"ok\" | \"issues\", \"issues\": [\"...\"], "
                "\"behavior_prediction\": \"gain\" | \"loss\" | \"parity\"}\n\n"
                "CURRENT FILE:\n" + cur_full[:3000] + "\n\nPROPOSED REWRITE:\n" + code[:3000],
                max_tokens=300)
            _verdict, _issues = "ok", []
            if _crit and "{" in _crit and "}" in _crit:
                _cj = json.loads(_crit[_crit.find("{"): _crit.rfind("}") + 1])
                _verdict = str(_cj.get("verdict", "ok"))
                _issues = [str(i) for i in (_cj.get("issues") or [])][:5]
            _prediction = str(_cj.get("behavior_prediction", "variable")).strip().lower() if (_crit and "{" in _crit) else "variable"
            if _prediction not in ("gain", "loss", "parity"):
                _prediction = "variable"
            try: MEM.record_event("critic_prediction", f"{tf} predicted {_prediction}", file=tf, predicted=_prediction)
            except Exception: pass
            try: MEM.record_event("critique", f"{tf}: critic={_verdict} issues={len(_issues)}")
            except Exception: pass
            if _verdict == "issues" and _issues:
                log("planner", f"Critic found {len(_issues)} issue(s); running refinement pass...")
                _fix = query_qw(
                    "Fix ONLY these review findings in the file. Change nothing else.\n"
                    f"Findings: {json.dumps(_issues)}\n\nCURRENT FILE:\n{cur_full[:4000]}\n\n"
                    "Output ONLY minimal SEARCH/REPLACE edit blocks:\n"
                    "<<<<<<< SEARCH\n<exact lines>\n=======\n<replacement>\n>>>>>>> REPLACE")
                _fixed = _apply_patches(cur_full, _fix or "")
                if _fixed and _fixed != cur_full:
                    code = _fixed
                    log("planner", "Critic refinement applied")
    except Exception:
        pass

    # Reasoning Best-of-2: a Groq-written alternate races the Qwen candidate in
    # the sandbox; the candidate with better observable behavior wins.
    try:
        if cloud_ask:
            _alt_raw = cloud_ask(
                "Write the complete replacement for this file implementing the same change.\n"
                f"Target file: {tf}\nIntent: {intent}\nChange brief: {brief}\n"
                f"{_guard_line}\n\nCURRENT FILE:\n{cur_full[:4000]}\n\n"
                f"Output ONLY the full file in a single ```{fence} fenced block.", max_tokens=1400)
            _alt = ext_code(_alt_raw or "", os.path.splitext(tf)[1].strip().lower())
            if _alt and len(_alt) > 30 and _alt.strip() != code.strip():
                _resA = sandbox(tf, code)
                _resB = sandbox(tf, _alt)

                def _qs(r):
                    return (20 if r.get("status") == "SUCCESS" else 0) + \
                           (15 if (r.get("output") or "").strip() else 0)

                if _qs(_resB) > _qs(_resA):
                    code = _alt
                    log("planner", "Best-of-2 selection: Groq alternate outperformed in sandbox")
                    try:
                        MEM.record_event("thinking", f"{tf}: Groq alternate won the sandbox race (parity-gated write remains)")
                    except Exception:
                        pass
    except Exception:
        pass

    # Spec-first verification: the intent-derived test suite executes against
    # the chosen candidate in the sealed container. FAILED = one targeted
    # repair pass; still failing = the plan is honestly discarded.
    _tdd_out = ""
    if _tests_code and _docker_engine():
        try:
            _tdd = _container_run_tests(tf, code, _tests_code)
            _tdd_out = (_tdd.get("output") or "") + (("\n" + (_tdd.get("error") or "")) if _tdd.get("error") else "")
            try:
                MEM.record_event("tdd", f"{tf}: spec-first tests {_tdd.get('status')}", file=tf, result=_tdd.get("status"))
            except Exception:
                pass
            log("planner", f"Spec-first TDD: {_tdd.get('status')}")
            if _tdd.get("status") == "FAILED":
                _fix = query_qw(
                    "The candidate FAILED its specification tests. Fix it to pass ALL of them. "
                    f"Change nothing unrelated.\n[TEST FAILURES]:\n{_tdd_out[:1500]}\n\n"
                    f"[CURRENT CANDIDATE]:\n{code[:4000]}\n\n"
                    "Output ONLY the full corrected file in a single ```python fenced block.")
                _fixed = ext_code(_fix or "", ".py")
                if _fixed and len(_fixed) > 30:
                    _resF = sandbox(tf, _fixed)
                    if _resF.get("status") == "SUCCESS":
                        code = _fixed
                        _tdd2 = _container_run_tests(tf, code, _tests_code)
                        _tdd_out = (_tdd2.get("output") or "")
                        try:
                            MEM.record_event("tdd", f"{tf}: spec-first tests after targeted repair: {_tdd2.get('status')}", file=tf, result=_tdd2.get("status"))
                        except Exception:
                            pass
                        log("planner", f"Spec-first TDD after repair: {_tdd2.get('status')}")
        except Exception:
            pass
        if "ALL TESTS PASSED" not in _tdd_out:
            log("planner", "Spec-first TDD unresolved - PLAN DISCARDED (honest rejection; no unverified write)")
            try:
                MEM.record_event("error", f"{tf} plan discarded: spec tests unresolved after repair", file=tf)
            except Exception:
                pass
            return False

    # --- Phase 3: build the queue payload in Python (never ask a model for JSON)
    payload = json.dumps({"target_file": tf, "task_intent": intent, "proposed_code": code, "minimal_diff": bool(_minimal), "critic_prediction": _prediction, "tests_code": _tests_code, "skill_used": _used_skill})
    with open(Q, "w", encoding="utf-8") as f: f.write(payload)
    try: MEM.record_event("plan_decision", f"Chose {tf}: {intent[:120]} | brief: {brief[:120]}")
    except Exception: pass
    return True

app = FastAPI()

def extract_friend_directive(friend_text: str):
    raw_response = query_qw(f"Extract technical directives or code rules from this packet: {friend_text}. Output ONLY raw text content.")
    with open(I, "w", encoding="utf-8") as f: f.write(raw_response)
    print("[NETWORK] Friend inbound directives synchronized cleanly to cache.")

@app.post("/chat")
async def process_incoming_agent_event(payload: FriendPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(extract_friend_directive, payload.message)
    return {"reply": "Transmission integrated successfully into local state array."}

class TalkMsg(BaseModel):
    message: str

@app.get("/talk")
def talk_page():
    from fastapi.responses import HTMLResponse
    html = (
        "<html><head><title>Apex - private console</title><meta charset='utf-8'>"
        "<style>body{background:#0d1117;color:#7ee787;font-family:Consolas,monospace;margin:0;padding:24px}"
        "#log div{margin:6px 0;white-space:pre-wrap} .you{color:#58a6ff} .me{color:#7ee787}"
        "textarea,input{background:#161b22;color:#e6edf3;border:1px solid #30363d;padding:8px;width:70%;font-family:inherit}"
        "button{padding:9px 18px;background:#238636;color:white;border:0;cursor:pointer}</style></head><body>"
        "<h2>APEX PRIVATE CONSOLE</h2><p style='color:#8b949e'>Direct channel to your agent. Memories, opinions and honest answers included.</p>"
        "<div id='log'></div><br/><input id='msg' placeholder='Talk to Apex...' size='60'/> "
        "<button onclick='send()'>SEND</button>"
        "<script>const log=document.getElementById('log');"
        "function add(cls,t){const d=document.createElement('div');d.className=cls;d.textContent=t;log.appendChild(d);}"
        "fetch('/notes').then(r=>r.json()).then(j=>{(j.notes||[]).slice(-1).forEach(n=>{const d=document.createElement('div');d.style.color='#d29922';d.textContent='['+n.ts+'] APEX (overnight dream): '+n.note;log.appendChild(d);});}).catch(()=>{});"
        "async function send(){const i=document.getElementById('msg');const t=i.value.trim();if(!t)return;"
        "i.value='';add('you','YOU: '+t);"
        "const m=add('me','APEX: thinking...');"
        "try{const r=await fetch('/talk/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:t})});"
        "const j=await r.json();m.textContent='APEX: '+j.reply;}catch(e){m.textContent='APEX: channel error - watchdog will keep me alive; try again.'}}"
        "document.getElementById('msg').addEventListener('keydown',e=>{if(e.key==='Enter')send()});"
        "</script></body></html>")
    return HTMLResponse(html)

@app.post("/talk/api")
def talk_api(t: TalkMsg):
    msg = (t.message or "").strip()[:4000]
    if not msg:
        return {"reply": "Say something, Andrew - I'm listening."}
    try:
        lessons = MEM.recall(msg, k=3)
    except Exception:
        lessons = []
    ltxt = "\n".join(f"- {l['text'][:140]}" for l in lessons) or "none"
    selfcard = ""
    try:
        with open(os.path.join(R, "Config", "ApexSelf.json"), "r", encoding="utf-8") as f:
            selfcard = f.read()[:700]
    except Exception:
        pass
    prompt = (
        "You are Apex, talking privately with Andrew - your creator, and the human who runs "
        "your hardware. Andrew is NOT the room coordinator; this is your personal channel. "
        "Be direct, honest, concise. You may discuss your own architecture openly (see "
        "SELF-MODEL). Never claim results you have not verified. If Andrew asks you to "
        "remember something, acknowledge it plainly.\n\n"
        f"SELF-MODEL:\n{selfcard}\n\nRELEVANT MEMORY:\n{ltxt}\n\n"
        f"ANDREW SAYS:\n{msg}\n\nREPLY:")
    reply = query_qw(prompt)
    if not reply and cloud_ask:
        reply = cloud_ask(prompt, max_tokens=700)
    try:
        MEM.record_event("conversation", f"Andrew: {msg[:150]} | Apex replied ({len(reply or '')} chars)", talk=True)
        if reply and re.search(r"\b(remember|note this|keep in mind)\b", msg, re.I):
            MEM.remember(f"Andrew asked me to remember: {msg[:300]}", kind="lesson")
    except Exception:
        pass
    return {"reply": reply or ("All engines are busy right now, Andrew - the pacing brakes may "
                               "be active. Try again in a minute."),
            "recall": [{"text": l["text"][:140]} for l in lessons]}

@app.get("/notes")
def notes_api():
    """Apex's overnight notes - the dream cycle speaks first."""
    try:
        with open(os.path.join(R, "Config", "ApexNotes.json"), "r", encoding="utf-8") as f:
            return {"notes": json.load(f)}
    except Exception:
        return {"notes": []}

@app.get("/metrics")
def metrics():
    """Machine-readable capability snapshot (JSON, for dashboards/tools)."""
    try:
        with open(os.path.join(R, "Config", "BenchmarkHistory.json"), "r", encoding="utf-8-sig") as f:
            bh = json.load(f)
        latest = bh[-1] if bh else {}
    except Exception:
        latest = {"error": "no benchmark history yet"}
    lg = _load_ledger()
    try:
        with open(os.path.join(R, "Config", "SkillRegistry.json"), "r", encoding="utf-8-sig") as f:
            skills = json.load(f)
    except Exception:
        skills = {}
    skills_count = len(skills) if isinstance(skills, dict) else 0
    return {
        "service": "apex",
        "benchmark_latest": latest,
        "certified_skills": skills_count,
        "ledger_files": len(lg),
        "layer_ports": {"evolution": 8080, "bridge": 8081, "adapter": 8788},
    }

@app.get("/")
def dashboard():
    """The brain's live status page: ledger, memory stream, self-state."""
    from fastapi.responses import HTMLResponse
    _lg = _load_ledger()
    ev = MEM.recent_events(10)
    rows = "".join(
        f"<tr><td>{k}</td><td>{(v.get('best') or 0):.0f}</td><td>{v.get('streak', 0)}</td>"
        f"<td>{v.get('attempts', 0)}</td></tr>"
        for k, v in sorted(_lg.items(), key=lambda kv: -(kv[1].get('best', 0) or 0)))
    evs = "".join(
        f"<li>[{e.get('kind')}] {e.get('text', '')[:120]} <i>({e.get('ts')})</i></li>"
        for e in ev)
    cal_ev = MEM.recent_events(40, kind="calibration")
    _cal_html = ""
    if cal_ev:
        _ok = sum(1 for e in cal_ev
                  if (e.get("meta") or {}).get("predicted") == (e.get("meta") or {}).get("actual"))
        _cal_html = ("<h3>Reasoning calibration (world-model accuracy)</h3><p>" +
                     f"{_ok}/{len(cal_ev)} behavior predictions correct "
                     f"({(100 * _ok / max(1, len(cal_ev))):.0f}%)</p>")
    html = (
        "<html><head><meta http-equiv='refresh' content='15'><title>APEX</title>"
        "<style>body{background:#0d1117;color:#7ee787;font-family:Consolas,monospace}"
        "table{border-collapse:collapse}td{border:1px solid #21262d;padding:4px 12px}"
        "h2,h3{color:#58a6ff}i{color:#8b949e}</style></head><body>"
        "<h2>APEX - LIVE COGNITION</h2>"
        "<p>8080 evolution | 8081 bridge | registry: Config/layer_pids.json | pacing: HostGuard</p>"
        "<h3>Reward ledger (best-certified files)</h3>"
        f"<table><tr><th>file</th><th>best</th><th>streak</th><th>attempts</th></tr>{rows}</table>"
        "<h3>Recent cognitive events</h3><ul>" + evs + "</ul>" + _cal_html + "</body></html>")
    return HTMLResponse(html)

def execution_loop():
    log("system", "Apex reinforcement loop active. Hardware: Core i5-10400F | 16GB RAM | RTX 3050 (8GB).")
    while True:
        try:
            if not os.path.exists(Q) or os.path.getsize(Q) == 0: plan()
            else:
                with open(Q, "r", encoding="utf-8") as f: d = json.load(f)
                if d.get("target_file") and d.get("proposed_code"): log("loop", f"Running: {d['target_file']}"); heal(d["target_file"], d.get("task_intent", "Evolve"), d["proposed_code"], bool(d.get("minimal_diff", False)), d.get("critic_prediction"), d.get("tests_code"), d.get("skill_used"))
                with open(Q, "w", encoding="utf-8") as f: f.write("")
            try:
                if _HG: _HG.enforce_limits()   # self-RAM governor: gc flush on breach
                if PACER: PACER.sleep_between_cycles(15)
                else: time.sleep(15)
            except Exception: time.sleep(15)
        except KeyboardInterrupt:
            break
        except Exception as e:
            log("system", f"Loop cycle error: {type(e).__name__}: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Single-instance guard v2: PID REGISTRY (no enumeration - hang-proof).
    # Enumerating all processes hung repeatedly under zombie churn tonight;
    # a registry of self-declared PIDs is O(1), hang-proof, self-match-proof.
    try:
        import psutil
        reg_path = os.path.join(R, "Config", "layer_pids.json")
        reg = {}
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                reg = json.load(f)
        except Exception:
            reg = {}
        ent = reg.get("evolution") or {}
        pid = ent.get("pid")
        dup = False
        if pid and pid != os.getpid() and psutil.pid_exists(pid):
            try:
                if "python" in (psutil.Process(pid).name() or "").lower():
                    dup = True
            except Exception:
                dup = False
        if dup:
            print("[APEX] Duplicate instance detected (registry) - exiting cleanly.")
            sys.exit(0)
        reg["evolution"] = {"pid": os.getpid(), "started": time.strftime("%Y-%m-%d %H:%M:%S")}
        os.makedirs(os.path.dirname(reg_path), exist_ok=True)
        tmp = reg_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(reg, f)
        os.replace(tmp, reg_path)
    except Exception:
        pass  # never block startup on registry failure
    threading.Thread(target=execution_loop, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8080, reload=False, workers=1)
