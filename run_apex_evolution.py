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
    except OSError:
        pass
    with open(path, "a", encoding="utf-8") as f: f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

def query_ds(p):
    try:
        r = requests.post(U, json={"model": "deepseek-r1-distill-llama-8b", "messages": [{"role": "user", "content": p}], "temperature": 0.1, "stream": False, "max_tokens": 800}, timeout=300)
        if r.status_code == 200:
            choices = r.json().get("choices", [])
            if choices and isinstance(choices, list):
                return choices[0].get("message", {}).get("content", "").strip()
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
    if toks and toks[0] in ("rm", "rmdir", "del", "del.exe", "rd", "format", "erase"):
        return True
    return False

def _load_ledger():
    try:
        with open(LEDGER, "r", encoding="utf-8") as f: return json.load(f)
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
    for n in ast.walk(root):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            meth = getattr(n.func, "attr", "")
            base_id = getattr(getattr(n.func, "value", None), "id", "") or ""
            # FULL VETO: mass deletion or shell-out from evolving candidates
            if (meth == "rmtree" and base_id in ("os", "shutil")) or \
               (meth in ("system", "popen") and base_id in ("os",)):
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

def sandbox(fn, c):
    t = os.path.join(R, f"speculative_test_{fn}")
    if os.path.exists(t): os.remove(t)
    with open(t, "w", encoding="utf-8") as f: f.write(c)
    try:
        res = subprocess.run([sys.executable, t], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8, cwd=R)
        if os.path.exists(t): os.remove(t)
        return {"status": "SUCCESS" if res.returncode == 0 else "CRASHED", "error": None if res.returncode == 0 else res.stderr, "output": (res.stdout or "")}
    except Exception as e:
        if os.path.exists(t): os.remove(t)
        log("reward", f"Sandbox did not complete cleanly: {e}")
        return {"status": "CRASHED", "error": f"Sandbox failure: {e}", "output": ""}

def heal(fn, intent, code, minimal=False):
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
        # World-model calibration: predict behavior change, record what happened.
        if traj == 0:
            prev_out = ((prev_res or {}).get("output") or "").strip()
            cand_out = (res.get("output") or "").strip()
            actual = ("gain" if len(cand_out) > len(prev_out)
                      else "loss" if len(cand_out) < len(prev_out) else "parity")
            expected = "parity" if minimal else "variable"
            try:
                MEM.record_event("calibration", f"{fn} expected {expected}, actual {actual}", file=fn)
                if minimal:
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
    except: return False
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
    # Self-model: the planner reads its own identity card every cycle.
    selfcard = ""
    try:
        with open(os.path.join(R, "Config", "ApexSelf.json"), "r", encoding="utf-8") as f:
            selfcard = f.read()[:900]
    except Exception:
        pass
    # --- Phase 1: DeepSeek-R1 THINKS (planning only, no code) -----------------
    o = query_ds(f"You are Apex automation head. Choose ONE file from [{', '.join(all_f)}] to optimize.\n"
                f"Recent reward history:\n{hist}\n"
                f"Long-term lessons/topical memories:\n{mem_hist}\n"
                f"Per-file reward ledger (best first):\n{ledger_hist}\n"
                f"Neglected files worth considering (exploration):\n{neglect}\n"
                f"Reflection on recent cycles:\n{reflect}\n"
                f"Self-model (identity, engines, limits):\n{selfcard}\n"
                f"Self-issued curriculum (proposed objectives):\n{curric}\n"
                "Rules: do NOT target core modules, do NOT propose destructive code.\n"
                "Return ONLY strict JSON (no code, no explanation): {\n  \"target_file\": \"filename.ext\",\n  \"task_intent\": \"one-sentence goal\",\n  \"change_brief\": \"2-3 sentences on the exact change to make\"\n}")
    if not o: return False
    if not o: return False

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

    # Ensemble planning: a second opinion from the Groq burst lane. Agreement
    # raises confidence; disagreement makes the coder conservative.
    _ensemble = ""
    try:
        if cloud_ask:
            _box = {}

            def _gp():
                try:
                    _box["v"] = cloud_ask(
                        "Second-opinion planner. Choose ONE file from [" + ", ".join(all_f[:12]) +
                        "] to optimize. Reply ONLY strict JSON: {\"target_file\": \"a.py\", "
                        "\"task_intent\": \"...\", \"change_brief\": \"...\"}. History: " + hist[-260:],
                        max_tokens=250)
                except Exception:
                    pass

            _tt = threading.Thread(target=_gp, daemon=True)
            _tt.start()
            _tt.join(timeout=28)
            _gplan = (_box.get("v") or "").strip()
            if "{" in _gplan and "}" in _gplan:
                _gj = json.loads(_gplan[_gplan.find("{"): _gplan.rfind("}") + 1])
                _gf = str(_gj.get("target_file", "")).strip()
                if _gf:
                    if _gf.lower() == tf.lower():
                        _ensemble = "second planner (Groq) AGREES with this target"
                    else:
                        _ensemble = (f"second planner (Groq) proposed {_gf} (DISAGREEMENT) - "
                                     "implement conservatively, keep changes surgical")
    except Exception:
        _ensemble = ""
    if _ensemble:
        log("planner", f"Ensemble: {_ensemble[:100]}")

    # --- Phase 2: Qwen2.5-coder EDITS (minimal-diff first, full-file fallback) -
    log("planner", f"Locked onto: {tf}. DeepSeek plan: {brief[:120]}")
    try:
        with open(os.path.join(R, tf), "r", encoding="utf-8") as f: cur_full = f.read()
    except Exception: return False
    fence = "powershell" if tf.lower().endswith(".ps1") else "python"
    ex = os.path.splitext(tf)[1].strip().lower()
    code = None
    _minimal = False
    patch_out = query_qw(
        f"You are Apex's expert coding unit. Apply the requested change with MINIMAL edits.\n"
        f"Target file: {tf}\nIntent: {intent}\nChange brief: {brief}\n"
        f"Second-opinion check: {(_ensemble or 'none')}\n\n"
        f"[CURRENT FILE CONTENT]:\n{cur_full[:6000]}\n\n"
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
            f"Target file: {tf}\nIntent: {intent}\nChange brief: {brief}\n\n"
            f"[CURRENT FILE CONTENT]:\n{cur_full[:6000]}\n\n"
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
    try:
        if cloud_ask:
            _crit = cloud_ask(
                "You are Apex's code critic. Review the proposed rewrite for hidden hazards: "
                "syntax issues, runtime hazards, behavioral regressions vs the current file, "
                "security problems. Reply ONLY strict JSON: "
                "{\"verdict\": \"ok\" | \"issues\", \"issues\": [\"...\"]}\n\n"
                "CURRENT FILE:\n" + cur_full[:3000] + "\n\nPROPOSED REWRITE:\n" + code[:3000],
                max_tokens=300)
            _verdict, _issues = "ok", []
            if _crit and "{" in _crit and "}" in _crit:
                _cj = json.loads(_crit[_crit.find("{"): _crit.rfind("}") + 1])
                _verdict = str(_cj.get("verdict", "ok"))
                _issues = [str(i) for i in (_cj.get("issues") or [])][:5]
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

    # --- Phase 3: build the queue payload in Python (never ask a model for JSON)
    payload = json.dumps({"target_file": tf, "task_intent": intent, "proposed_code": code, "minimal_diff": bool(_minimal)})
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
    html = (
        "<html><head><meta http-equiv='refresh' content='15'><title>APEX</title>"
        "<style>body{background:#0d1117;color:#7ee787;font-family:Consolas,monospace}"
        "table{border-collapse:collapse}td{border:1px solid #21262d;padding:4px 12px}"
        "h2,h3{color:#58a6ff}i{color:#8b949e}</style></head><body>"
        "<h2>APEX - LIVE COGNITION</h2>"
        "<p>8080 evolution | 8081 bridge | registry: Config/layer_pids.json | pacing: HostGuard</p>"
        "<h3>Reward ledger (best-certified files)</h3>"
        f"<table><tr><th>file</th><th>best</th><th>streak</th><th>attempts</th></tr>{rows}</table>"
        "<h3>Recent cognitive events</h3><ul>" + evs + "</ul></body></html>")
    return HTMLResponse(html)

def execution_loop():
    log("system", "Apex reinforcement loop active. Hardware: Core i5-10400F | 16GB RAM | RTX 3050 (8GB).")
    while True:
        try:
            if not os.path.exists(Q) or os.path.getsize(Q) == 0: plan()
            else:
                with open(Q, "r", encoding="utf-8") as f: d = json.load(f)
                if d.get("target_file") and d.get("proposed_code"): log("loop", f"Running: {d['target_file']}"); heal(d["target_file"], d.get("task_intent", "Evolve"), d["proposed_code"])
                with open(Q, "w", encoding="utf-8") as f: f.write("")
            try:
                if _HG: _HG.enforce_limits()   # self-RAM governor: gc flush on breach
                if PACER: PACER.sleep_between_cycles(15)
                else: time.sleep(15)
            except Exception: time.sleep(15)
        except KeyboardInterrupt: break
        except: time.sleep(5)

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
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False, workers=1)
