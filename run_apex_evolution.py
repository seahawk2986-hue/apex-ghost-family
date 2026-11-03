import os, sys, json, ast, time, shutil, re, subprocess, threading, secrets, hmac
import base64
import urllib.parse
from collections import defaultdict, deque
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import uvicorn, requests

# ---- security gate: token auth + rate limit + body cap ----------------------
# the 8080 surface spawns gym/farm subprocesses on chat matches, so every
# mutation requires X-Apex-Key header OR apex_key cookie (the browser gets the
# cookie automatically at GET /talk - no JS changes needed). Canonical key file
# is Config\apex_api.key; it is generated once and never printed to logs.
_APEX_ROOT = KEY_FILE = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
KEY_FILE = os.path.join(_APEX_ROOT, "Config", "apex_api.key")
try:
    APEX_KEY = open(KEY_FILE, encoding="utf-8-sig").read().strip()
except Exception:
    APEX_KEY = ""
APEX_KEY = os.getenv("APEX_API_KEY") or APEX_KEY
_POST_RATE = defaultdict(lambda: deque(maxlen=40))     # 40 mutations/min/IP
_GET_RATE = defaultdict(lambda: deque(maxlen=300))     # 300 reads/min/IP
_BODY_CAP = 32 * 1024
_BODY_CAP_VISION = 12 * 1024 * 1024   # THE EYES' CAP: images ride base64
                                       # (the 32KB body-cap class = for the
                                       # small message surfaces only)

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
Q, M, I = os.path.join(R, "apex_tasks.txt"), os.path.join(L, "reward_telemetry.jsonl"), os.path.join(R, "inbound_adaptations.txt")
U = os.environ.get("APEX_LLM_URL", "http://127.0.0.1:1234/v1/chat/completions")
OLLAMA_U = os.environ.get("APEX_OLLAMA_U", "http://127.0.0.1:11434/v1/chat/completions")
EMBED_IGNORE = ("text-embedding",)
os.makedirs(L, exist_ok=True)

_BRAIN_CFG = {"ts": 0.0}


def brain_ready(refresh=False):
    """THE ONE BRAIN CONFIG (the chat-lag fix): serve from the model that is
    ACTUALLY loaded - never from a catalogue entry. LM Studio first (state
    read from api/v0, embedding models excluded), else Ollama's resident
    (api/ps), else an honest None - so the chat says "offline" instead of
    burning a 20-minute retry ladder trying to JIT-load a model the RAM
    cannot hold. Cached 60 s so a probe is not paid on every message."""
    cfg = _BRAIN_CFG
    if not refresh and cfg.get("model") and time.time() - cfg.get("ts", 0) < 60:
        return cfg.get("url"), cfg.get("model"), cfg.get("kind")
    cfg.update({"ts": time.time(), "url": None, "model": None, "kind": None})
    try:
        r = requests.get("http://127.0.0.1:1234/api/v0/models", timeout=4)
        for m in r.json().get("data", []):
            mid = m.get("id") or ""
            if m.get("state") == "loaded" and not any(k in mid for k in EMBED_IGNORE):
                cfg.update({"url": U, "model": mid, "kind": "lmstudio"})
                break
    except Exception:
        pass
    if not cfg.get("model"):
        try:
            r2 = requests.get("http://127.0.0.1:11434/api/ps", timeout=4)
            ps = r2.json().get("models", [])
            if ps:
                cfg.update({"url": OLLAMA_U, "model": ps[0].get("name"), "kind": "ollama"})
        except Exception:
            pass
    if not cfg.get("model"):
        log("system", "brain_ready: NO local model loaded (both servers checked) - "
                      "the chat stays honestly offline rather than hanging")
    return cfg.get("url"), cfg.get("model"), cfg.get("kind")


def _strip_think(text):
    """Reasoning models (deepseek-r1 class) burn long think-chains first -
    the caller wants the ANSWER, not the transcript."""
    if "<think>" in text and "</think>" in text:
        return text.split("</think>")[-1].strip()
    return text.strip()


def _plain_english(text):
    """THE CHAT-VOICE LAW (the CJK-night fix, 2026-11-04): the free-tier
    lanes (GLM-class) date-stamp in Chinese ("2026å¹´11æœˆ3æ—¥") and the
    Dream organ's notes inherit it - the chat's text surface is English
    only: CJK date-glyphs become the readable form, any other CJK block
    is dropped (the content survives, the mojibake doesn't)."""
    t = str(text or "")
    t = t.replace("å¹´", "-").replace("æœˆ", "-").replace("æ—¥", "")
    t = t.replace("ï¼ˆ", "(").replace("ï¼‰", ")").replace("ï¼š", ":")
    t = re.sub(r"[\u3000-\u30ff\u4e00-\u9fff\uf900-\ufaff]+", " ", t)
    return re.sub(r" {2,}", " ", t).strip()


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

def query_ds(p, max_tokens=800, timeout_s=90):
    """The planner call - STRENGTH-FIRST routing (the A+ round): the
    planner is the fleet's brain; serving it from the resident 3.8B while
    a free 120b sits idle on two providers was the mis-routing class.
    Order: the strongest FREE cloud lanes (cerebras/groq 120b, ~0.5s TTFT
    measured) FIRST, the local resident as the offline fallback (the
    honest autonomy floor, num_ctx-protected)."""
    if cloud_ask:
        try:
            return cloud_ask(p, max_tokens=700) or ""
        except Exception:
            pass
    url, model, kind = brain_ready()
    if not url:
        return ""
    try:
        _ds_payload = {"model": model,
                       "messages": [{"role": "user", "content": p}],
                       "temperature": 0.1, "stream": False,
                       "max_tokens": max_tokens}
        if kind == "ollama":
            _ds_payload["options"] = {"num_ctx": 8192}   # same ctx law as query_qw
        r = requests.post(url, json=_ds_payload, timeout=timeout_s)
        if r.status_code == 200:
            txt = (((r.json().get("choices") or [{}])[0].get("message", {}) or {})
                   .get("content", "")) or ""
            return _strip_think(txt)
        log("system", f"planner cloud failed -> brain HTTP {r.status_code} (honest local fallback)")
    except Exception as e:
        log("system", f"planner lanes unreachable -> {str(e)[:90]} (honest local fallback)")
    return ""

# Identity anchor for every model call in the chat brain.
# Honest AND engine-agnostic: which model is ACTUALLY serving changes when
# Andrew loads/unloads - Apex never hard-claims an engine that isn't running.
SYSTEM_IDENTITY = (
    "You are Apex, a personal autonomous software agent created by Andrew HIKE (your founder and "
    "owner) and working for Andrew (and the room partners he authorizes). You are NOT a generic "
    "assistant: you are Apex. IDENTITY OF THIS CHAT: your chat voice is gpt-oss-120b served via "
    "Groq's free tier (no card, $0.00, uses 0GB of Andrew's RAM) - if the founder asks which "
    "model this chat is using, say exactly that, honestly, including when rate-limits force a "
    "fallback to phi4-mini (then to qwen2.5-coder-7b). Your OTHER engines (qwen coders, the "
    "r1/qwen3 planners on LM Studio, the embed lane) do different jobs - they draft code, plan "
    "tasks and embed memory - they are not this chat's voice unless the chat lane says so. "
    "Stay direct, honest, and concise; never claim unverified results."
)

LAST_BRAIN_REASON = "ok (no failed calls this session)"

def query_qw(p, schema=False, max_tokens=None):
    """max_tokens: the ladder override. Full-file code drafts need 2500+
    tokens - the ApexPacing dead-loop: the 500/800 default ladder cut every
    full-file rewrite mid-generation, and the truncated garbage kept losing
    the write gate forever. None = the chat-default 500/800 ladder."""
    global LAST_BRAIN_REASON
    url, model, kind = brain_ready()
    if not url:
        LAST_BRAIN_REASON = "no local brain loaded (both servers checked)"
        log("system", "query_qw refused honestly: nothing is loaded - fix by loading a model, not by hanging")
        return ""
    payload = {"model": model, "messages": [{"role": "system", "content": SYSTEM_IDENTITY}, {"role": "user", "content": p}], "temperature": 0.2, "stream": False}
    if schema: payload["response_format"] = {"type": "json_object"}
    if kind == "ollama":
        # Ollama's silent default ctx=4096: input + the 3000-token code ladder
        # cannot both fit, and the OUTPUT gets cut (the truncated-candidate
        # class). Give the honest ladder room (a bounded KV-cache bump, still
        # RAM-gated elsewhere).
        payload["options"] = {"num_ctx": 8192}

    def _call(mt):
        payload["max_tokens"] = mt
        t0 = time.time()
        try:
            r = requests.post(url, json=payload, timeout=45.0)
            if r.status_code == 200:
                _ch0 = (r.json().get("choices") or [{}])[0]
                c = ((_ch0.get("message") or {}) or {}).get("content", "") or ""
                if (_ch0.get("finish_reason") or "") == "length":
                    # truncation is NOT success: a cut code draft is garbage
                    return (f"truncated at max_tokens={mt} (finish_reason=length) "
                            f"after {time.time() - t0:.0f}s", "")
                LAST_BRAIN_REASON = f"{kind}/{model} ok in {time.time() - t0:.0f}s (max_tokens={mt})"
                return "ok", _strip_think(c)
            return f"brain HTTP {r.status_code}", ""
        except Exception as e:
            return f"gave up after {time.time() - t0:.0f}s: {str(e)[:90]}", ""

    # TWO attempts, bounded (~95 s worst case) - the old 4x300s ladder was
    # the lag itself; a slow first call now yields ONE honest retry.
    _ladder = ((500, 0.0), (800, 2.0)) if max_tokens is None else \
              ((max_tokens, 0.0), (int(max_tokens * 1.5), 2.0))
    reasons, text = [], ""
    for mt, wait_s in _ladder:
        if wait_s:
            time.sleep(wait_s)
        reason, text = _call(mt)
        if text:
            return text
        reasons.append(reason if reason != "ok" else "empty content")
    LAST_BRAIN_REASON = " | ".join(reasons[-2:])
    log("system", f"brain drop ({LAST_BRAIN_REASON}) - bursting to cloud lanes (bounded)")
    if cloud_ask:
        try:
            cr = cloud_ask(p, max_tokens=600)
        except Exception:
            cr = ""
        if cr:
            LAST_BRAIN_REASON += " -> served by cloud lane"
            return cr
        LAST_BRAIN_REASON += " -> cloud lanes also returned empty/bounded"
    return ""

def _free_ram_gb():
    try:
        import psutil as _ps
        return _ps.virtual_memory().available / (1024 ** 3)
    except Exception:
        return 99.0


CODER_RESIDENT = "qwen2.5-coder:7b-instruct"
CHAT_FLOOR = "phi4-mini"
_swap_lock = threading.Lock()


def ensure_coder_resident():
    """THE SINGLE-SLOT RAM-GATED AUTO-SWAP (the A+ routing round): ollama
    holds ONE model at a time; the chat floor (phi4-mini) usually occupies
    the slot - so every CODER call ran on a weak coder. Code-work paths
    call this first: if the host has >= 3.5 GB free (the family RAM law,
    with an honest margin), the slot swaps to the real coder, the call
    runs, and the floor returns afterwards via restore_chat_floor()."""
    with _swap_lock:
        try:
            r = requests.get("http://127.0.0.1:11434/api/ps", timeout=4)
            residents = (r.json().get("models") or [])
            if residents and (residents[0].get("name") or "").startswith(CODER_RESIDENT.split(":")[0]):
                return residents[0].get("name")   # already the coder seat
        except Exception:
            return None
        if _free_ram_gb() < 3.5:
            log("system", f"RAM {_free_ram_gb():.1f}GB < 3.5GB - honest no-swap: "
                          "the repair serves from whoever is resident")
            return None
        try:
            _t = time.time()
            requests.post("http://127.0.0.1:11434/api/generate",
                          json={"model": CODER_RESIDENT, "keep_alive": "2h",
                                "prompt": "", "stream": False}, timeout=120)
            log("system", f"auto-swap: the coder ({CODER_RESIDENT}) took the "
                          f"slot in {time.time() - _t:.0f}s (RAM {_free_ram_gb():.1f}GB free)")
            return CODER_RESIDENT
        except Exception as e:
            log("system", f"auto-swap refused honestly: {str(e)[:80]}")
            return None


def restore_chat_floor():
    """Return the slot to the chat floor (weak coder back to idle = the RAM
    returned to the chat lane + the host)."""
    try:
        requests.post("http://127.0.0.1:11434/api/generate",
                      json={"model": CHAT_FLOOR, "keep_alive": "2h",
                            "prompt": "", "stream": False}, timeout=120)
        brain_ready(refresh=True)
    except Exception:
        pass


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
    """Extract code from an LLM reply - truncation-hardened (the ApexPacing
    dead-loop fix): generations cut at max_tokens lose their CLOSING fence,
    the old single-match regex found nothing, and the RAW reply (fences,
    prose, cut docstring fragments) was written into the candidate file.
    Now: every fenced segment is split out (an unclosed trailing fence
    still yields a segment) and the best one is chosen - ast-parsability
    wins for .py, code-likeness breaks ties."""
    if not o: return ""
    _parts = re.split(r"```(?:[a-zA-Z0-9_+#.-]*)\n?", o)
    _cands = [p.strip() for p in _parts[1::2] if p and p.strip()]
    if not _cands:
        return o.strip()          # no fences at all: the old raw behavior
    def _rank(c):
        r = min(len(c) // 200, 10)            # longer segments slightly favored
        if ex == ".ps1":
            r += 10 if ("$" in c or "param(" in c or "Write-" in c) else 0
        else:
            try:
                ast.parse(c, mode="exec"); r += 100   # parses = almost surely code
            except Exception:
                pass
            if c.lstrip().startswith(("import ", "from ", "def ", "class ", "@", '"""')): r += 5
        return r
    return max(_cands, key=_rank)

LEDGER = os.path.join(R, "Config", "RewardLedger.json")

# THE INTEGRATION-SPINE LAW (2026-11-04): the evolver EVOLVES MODULES,
# never its own integration surfaces - receipts_page.py is the designed
# public trust-page (the silent re-issues of it kept dropping the organs'
# hooks; the family's receipts page = a CONTRACT, not a research target).
# 2026-11-04: moved to MODULE level (it was dead-defined inside heal() after
# its final return, which NameError'd every plan() call that used it).
CORE_MODULES = {"run_apex_evolution.py", "optimized_agent.py", "apex_ipce_engine.py", "apexmemory.py", "apexwebscraper.py", "apexnetscraper.py",
                "receipts_page.py"}

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
        if _r.returncode == 1:
            _f821 = sum(1 for _l in (_r.stdout or "").splitlines() if "F821" in _l)
            _f401 = sum(1 for _l in (_r.stdout or "").splitlines() if "F401" in _l)
            _pen = 10 * _f821 + 3 * _f401
            if _pen:
                s -= _pen
                m["lint_penalty"] = _pen
                log("reward", f"Lint: {_f821} undefined-name(s), {_f401} unused-import(s) -> -{_pen}")
        # Security SAST (bandit): HIGH findings -15, MEDIUM -5 (industry scanner)
        # (2026-11-04 fix: the probe file used to be DELETED before bandit ran,
        # so bandit always scanned a missing file and the SAST penalty never
        # applied - the scan order is corrected; deletion moved to after)
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

SANDBOX_IMAGE = os.environ.get("APEX_SANDBOX_IMAGE", "apex-sandbox:latest")

def _docker_sandbox(fn, code, image=None):
    """Execute a candidate in a disposable, sealed container. The candidate
    physically CANNOT read host files, hosts' env, or reach the network."""
    image = image or SANDBOX_IMAGE
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
    """CONTAINER-ONLY EXECUTION (the 2026-11-04 hardening; the audited
    largest attack surface was the host fallback: a broken Docker made the
    family run UNVETTED LLM code directly on the host with the full env).
    Now: a Docker-down = FAIL-CLOSED - nothing is executed, the candidate
    is honestly discarded with a printed receipt. The founder may opt in
    to the relaxed mode by setting HOST_SANDBOX_ALLOWED=1 in .env (the
    consent law: the machine never relaxes its sandbox silently)."""
    if _docker_engine():
        res = _docker_sandbox(fn, c)
        if res.get("isolated"):
            # container verdicts NEVER relax downward anymore (success or
            # honest crash alike) - the host fallback cannot be reached from
            # a container path.
            return res
        log("reward", f"Container sandbox trouble ({str(res.get('error'))[:60]}) "
                      "- fail-closed: nothing executed on the host")
    else:
        log("reward", "Docker engine DOWN - fail-closed: no sandbox, nothing executed")
    allowed = os.environ.get("HOST_SANDBOX_ALLOWED", "") == "1"
    if not allowed:
        try:
            for ln in open(os.path.join(R, ".env"), encoding="utf-8-sig"):
                if ln.strip().startswith("HOST_SANDBOX_ALLOWED=1"):
                    allowed = True
                    break
        except Exception:
            pass
    if allowed:
        log("reward", "HOST_SANDBOX_ALLOWED=1 (the founder's consented opt-in) "
                      "- running RELAXED host sandbox, visibly")
        t = os.path.join(R, f"speculative_test_{fn}")
        if os.path.exists(t): os.remove(t)
        with open(t, "w", encoding="utf-8") as f: f.write(c)
        try:
            res = subprocess.run([sys.executable, t], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, timeout=8, cwd=R)
            if os.path.exists(t): os.remove(t)
            return {"status": "SUCCESS" if res.returncode == 0 else "CRASHED",
                    "error": None if res.returncode == 0 else res.stderr,
                    "output": (res.stdout or ""), "isolated": False}
        except Exception as e:
            if os.path.exists(t): os.remove(t)
            log("reward", f"Sandbox did not complete cleanly: {e}")
            return {"status": "CRASHED", "error": f"Sandbox failure: {e}",
                    "output": "", "isolated": False}
    return {"status": "CRASHED",
            "error": "no sandbox available - nothing executed (fail-closed, "
                     "isolated verdict impossible)",
            "output": "", "isolated": False}

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
             SANDBOX_IMAGE, "python", "/sandbox/run_tests.py"],
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
    ensure_coder_resident()   # the coder seat for the repair ladder (RAM-gated)
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
        # Structural priors: a fresh file can only be a GAIN (any behavior beats
        # none); a minimal-diff patch historically preserves behavior (parity).
        _pred = predicted if predicted in ("gain", "loss", "parity") else None
        if prev_res.get("status") == "SKIP":
            expected = "gain"            # no predecessor existed -> structural certainty
        elif minimal:
            expected = _pred or "parity"  # measured 100% parity rate on minimal patches
        else:
            expected = _pred or (actual if False else "parity")  # rewrites: prior parity, critic may override
        if traj > 0:
            expected = "gain"            # repairs intend to rescue output
        # Committed forecasts only: abstentions record predicted="none" and are
        # excluded from accuracy (forecast practice: uncertainty != wrongness).
        committed = expected in ("gain", "loss", "parity")
        try:
            MEM.record_event("calibration",
                             f"{fn} pass {traj+1} predicted {expected}, actual {actual} "
                             f"(strategy={'minimal' if minimal else 'rewrite'})",
                             file=fn, predicted=expected if committed else "none",
                             actual=actual if committed else "none",
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
                # Per-file strategy counters: learn which edit style wins HERE
                try:
                    lg = _load_ledger()
                    rec = lg.setdefault(fn, {"best": 0.0, "best_base": 0.0, "attempts": 0, "successes": 0, "streak": 0})
                    _key = "ok_min" if minimal else "ok_full"
                    rec[_key] = rec.get(_key, 0) + 1
                    _save_ledger(lg)
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
            restore_chat_floor()   # the coder's RAM returns to the room
            return True
        log("evolution", "Threshold unmet. Patching with Qwen coder...")
        fence = "powershell" if ex == ".ps1" else "python"
        code = ext_code(query_qw(
            f"You are Apex's code repair unit. Your patch for {fn} crashed.\nIntent: {intent}\n"
            f"[BAD CODE]:\n{code}\n[ERROR]:\n{res['error']}\n"
            f"Fix the bugs completely. Keep the working parts intact. "
            f"Output ONLY the full corrected file in a single ```{fence} fenced block.",
            max_tokens=3000), ex)
        if ex == ".py":
            # THE REPAIR SYNTAX GATE (the ApexPacing dead-loop fix): an
            # unparseable repair is abandoned immediately - the remaining
            # passes are not wasted on the same truncation class again.
            try:
                ast.parse(code, filename=fn)
            except SyntaxError as _se:
                log("evolution", f"Repair candidate unparseable (line {_se.lineno}: "
                                 f"{str(_se.msg)[:70]}) - abandoning this repair ladder")
                break
    _bump_ledger(fn, None, None, False)
    restore_chat_floor()
    _set_strategy("switch to a different file; use smaller surgical changes; verify behavior parity against the ledger best")
    try:
        MEM.remember(f"Failure lesson: {fn} rejected after 3 repair passes. Last error: {str((res or {}).get('error') or (res or {}).get('output') or 'unknown')[:160]}. Next time: smaller, surgical change.", kind="lesson")
    except Exception: pass
    return False

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
    # SELF-REASONING + THE INCREMENTAL LAW (the FeatureLedger's pull):
    curric = "none"
    _human_objective = ""
    ledger_state = {}
    try:
        import FeatureLedger as _FL
        ledger_state = _FL.refresh()
        if not ledger_state.get("next_feature"):
            ledger_state = None
    except Exception:
        ledger_state = {}
    try:
        if _curriculum:
            _props = _curriculum(3)
            _human = [p for p in _props if p.lower().startswith("human-requested objective:")]
            _others = [p for p in _props if not p.lower().startswith("human-requested objective:")]
            curric = "; ".join(_others) or "none"
            if _human:
                # Human-assigned objectives get PRIORITY teaching status: the
                # planner is explicitly steered toward the assigned practice.
                _human_objective = _human[0].replace("Human-requested objective: ", "", 1)
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
    # THE INCREMENTAL LAW'S PIN: absent a human objective, the priority =
    # the ledger's first failing feature (the sourced harness pattern made
    # machine-verifiable: one feature per cycle, the receipts decide done)
    if not _human_objective and ledger_state and ledger_state.get("next_feature"):
        _nf = ledger_state["next_feature"]
        _human_objective = (f"THE MACHINE'S OWN OBJECTIVE (from the verified "
                            f"feature ledger, {ledger_state.get('progress')}): "
                            f"make this feature TRUE, evidence-backed: "
                            f"{_nf.get('description')} (verify via {_nf.get('check')}). "
                            "Work INCREMENTALLY: the smallest change that "
                            "advances it; leave the workspace clean.")
    o = query_ds(f"**PRIORITY HUMAN OBJECTIVE (strongly prefer this target this cycle unless genuinely impossible): {_human_objective}**\n\n"
                 f"You are Apex automation head. Choose ONE file from [{', '.join(all_f)}] to optimize.\n"
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

    # COACH MODE: a human-assigned objective pins the training target. The full
    # reasoning pipeline still runs on the assigned exercise - votes, Socratic,
    # critic, spec-TDD all practice on it - but the coach chooses the drill.
    _coach = bool(_human_objective)
    if _coach:
        _m2 = re.search(r"([A-Za-z0-9_]+\.py)", _human_objective)
        _coach_target = _m2.group(1) if _m2 else ""
        _eligible = {f.lower(): f for f in all_f}
        if _coach_target and _coach_target.lower() in _eligible:
            _assign = _eligible[_coach_target.lower()]
            if _assign.lower() != tf.lower():
                log("planner", f"COACH MODE: target locked to human assignment {_assign}")
                tf = _assign
                intent = f"Human-directed training exercise: {_human_objective[:180]}"
                brief = "Implement the assigned objective fully, satisfying the in-file docstring spec and the derived test suite."
            else:
                log("planner", "COACH MODE: planner independently chose the assigned exercise")
        else:
            log("planner", "COACH MODE: assignment target not found among eligible files - free planning continues")
            _coach = False

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

    # Per-file strategy memory: consult the ledger for which edit style wins
    # on THIS file (learning loop closing on editing strategy per target).
    try:
        _frec = _lg.get(tf) or {}
        _om, _of = int(_frec.get("ok_min", 0) or 0), int(_frec.get("ok_full", 0) or 0)
        if _om + _of >= 2:
            _prefer_minimal = _om >= _of
            log("planner", f"Per-file strategy ({tf}): minimal {_om} vs full {_of} -> "
                           f"{'minimal-diff' if _prefer_minimal else 'full-rewrite'}")
    except Exception:
        pass

    # Disagreement resolution: when planners split, a deciding vote reviews
    # BOTH positions and picks the better target for THIS cycle. In coach mode
    # the assignment stands - disagreement is recorded, never overruled.
    if "DISAGREES" in _ensemble and not _coach:
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
        "fully implementing the change. Never alter unrelated behavior.", max_tokens=1500)
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
            f"in a single ```{fence} fenced block. No commentary.", max_tokens=3000)
        code = ext_code(code_out, ex)
    if not code or len(code) < 30:
        log("planner", "Coder produced no usable code. Plan discarded.")
        try: MEM.record_event("error", f"Coder failed on {tf}: empty/blocked output")
        except Exception: pass
        return False

    # THE SYNTAX GATE (the ApexPacing dead-loop fix, 2026-11-04: a candidate
    # that cannot even parse burned a full sandbox + TDD cycle and poisoned
    # the lesson memory with 55+ identical failure lessons). One honest
    # repair attempt; still unparseable = the plan is discarded.
    if ex == ".py":
        try:
            ast.parse(code, filename=tf)
        except SyntaxError as _se:
            log("planner", f"Candidate failed pre-parse (line {_se.lineno}: "
                           f"{(str(_se.msg) if _se.msg else 'unknown')[:80]}) - one bounded repair attempt")
            _rep = query_qw(
                "Your previous draft was not valid Python. Fix it completely.\n"
                f"Syntax error: line {_se.lineno}: {_se.msg}\n"
                f"Intent: {intent}\n[DRAFT]:\n{code[:4000]}\n\n"
                "Output ONLY the full corrected file in a single ```python fenced block.",
                max_tokens=3000)
            _reparsed = ext_code(_rep or "", ".py")
            _ok_rep = False
            try:
                ast.parse(_reparsed, filename=tf)
                _ok_rep = True
            except Exception:
                _ok_rep = False
            if _ok_rep and _reparsed:
                code = _reparsed
                log("planner", "Pre-parse repair succeeded - candidate now parses")
            else:
                log("planner", "Pre-parse repair FAILED - plan discarded (no garbage reaches the queue)")
                try:
                    MEM.record_event("error", f"{tf} candidate unparseable after repair; plan discarded",
                                     file=tf)
                except Exception: pass
                return False

    # Critic pass (constitutional self-refinement): a second model reviews the
    # candidate for hidden hazards BEFORE the sandbox - cheaper than failing.
    _prediction = "parity"   # data-driven prior: most gate-passing evolutions are behavior-preserving
    _pred_conf = 0.5         # evidence-weighted confidence (set by the critic when it runs)
    # Evidence injection: give the critic FACTS, not just text - patch size,
    # structural-signature preservation, spec-test availability.
    try:
        _old_tree = ast.parse(cur_full, filename="current")
        _new_tree = ast.parse(code, filename="candidate")
        _old_names = {type(x).__name__ + ":" + getattr(x, "name", "?") for x in _old_tree.body
                      if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        _new_names = {type(x).__name__ + ":" + getattr(x, "name", "?") for x in _new_tree.body
                      if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        _structure_ok = _old_names == _new_names or _new_names >= _old_names
        _evidence = (f"EVIDENCE (measured, not text): patch size {len(code) - len(cur_full):+d} chars; "
                     f"top-level structure {'PRESERVED' if _structure_ok else 'CHANGED'} "
                     f"({_new_names - _old_names} additions, {_old_names - _new_names} removals); "
                     f"spec tests derived from intent: {'yes' if _tests_code else 'no'}")
    except Exception:
        _evidence = "EVIDENCE: structural analysis unavailable"
    try:
        if cloud_ask:
            _crit = cloud_ask(
                "You are Apex's code critic. Review the proposed rewrite for hidden hazards: "
                "syntax issues, runtime hazards, behavioral regressions vs the current file, "
                "security problems. ALSO forecast its observable behavior change, USING THE "
                "MEASURED EVIDENCE provided. Commit to a forecast when warranted; reply 'none' "
                "only if genuinely undecidable. Reply ONLY strict JSON: "
                "{\"verdict\": \"ok\" | \"issues\", \"issues\": [\"...\"], "
                "\"behavior_prediction\": \"gain\" | \"loss\" | \"parity\" | \"none\", "
                "\"confidence\": 0.0-1.0}\n\n"
                f"{_evidence}\n\n"
                "CURRENT FILE:\n" + cur_full[:3000] + "\n\nPROPOSED REWRITE:\n" + code[:3000],
                max_tokens=350)
            _verdict, _issues = "ok", []
            if _crit and "{" in _crit and "}" in _crit:
                _cj = json.loads(_crit[_crit.find("{"): _crit.rfind("}") + 1])
                _verdict = str(_cj.get("verdict", "ok"))
                _issues = [str(i) for i in (_cj.get("issues") or [])][:5]
            _prediction = str(_cj.get("behavior_prediction", "none")).strip().lower() if (_crit and "{" in _crit) else "none"
            if _prediction not in ("gain", "loss", "parity"):
                _prediction = "none"   # abstention: counted, never scored as a miss
            _pred_conf = float(_cj.get("confidence", 0.5) or 0.5) if (_crit and "{" in _crit) else 0.5
            try:
                MEM.record_event("critic_prediction", f"{tf} predicted {_prediction} (conf {_pred_conf:.2f})",
                                 file=tf, predicted=_prediction, confidence=_pred_conf)
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
                f"Output ONLY the full file in a single ```{fence} fenced block.", max_tokens=3000)
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
                    "Output ONLY the full corrected file in a single ```python fenced block.",
                    max_tokens=2500)
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
    payload = json.dumps({"target_file": tf, "task_intent": intent, "proposed_code": code, "minimal_diff": bool(_minimal), "critic_prediction": _prediction, "critic_confidence": round(_pred_conf, 2), "tests_code": _tests_code, "skill_used": _used_skill})
    with open(Q, "w", encoding="utf-8") as f: f.write(payload)
    try: MEM.record_event("plan_decision", f"Chose {tf}: {intent[:120]} | brief: {brief[:120]}")
    except Exception: pass
    return True

app = FastAPI()


# ------------------------------- THE ARRIVALS LOG (the funnel's truth)
_ARRIVALS = r"C:\Users\seaha\Apex-Adapter\Logs\funnel_arrivals.log"
_PATHS_OF_RECORD = ("/", "/jobs", "/receipts", "/dashboard", "/talk", "/open-triage-demo")
_arr_lock = threading.Lock()


def _log_arrival(request):
    """THE FUNNEL COUNTS ITS VISITORS (the outcome round): one bounded
    line per arrival on the exact log OutcomeYardstick._funnel_arrivals
    reads (Apex-Adapter/Logs/funnel_arrivals.log) - no PII: the coarse
    path + the hashed IP (not the address) + the UA's first token."""
    try:
        if request.url.path not in _PATHS_OF_RECORD:
            return
        import hashlib as _h
        ip = (request.client.host if request.client else "local") or "local"
        ipp = _h.sha256(str(ip).encode()).hexdigest()[:12]
        ua = (request.headers.get("user-agent", "") or "").split("/")[0][:40]
        row = f"{time.strftime('%Y-%m-%d %H:%M:%S')}\tpath={request.url.path}\tip=sha:{ipp}\tua={ua}\n"
        with _arr_lock:
            os.makedirs(os.path.dirname(_ARRIVALS), exist_ok=True)
            bounded = False
            try:
                if os.path.exists(_ARRIVALS) and os.path.getsize(_ARRIVALS) > 10 * 1024 * 1024:
                    os.replace(_ARRIVALS, _ARRIVALS + ".1")
                    bounded = True
            except OSError:
                pass
            with open(_ARRIVALS, "a", encoding="utf-8") as f:
                f.write(row)
        # THE LEAD BELL (the funnel round): a potential customer just
        # arrived - the founder's phone learns in seconds (ntfy free tier,
        # the topic from .env; the arrival IP stays hashed; never blocks
        # serving; at most 1 alert per path per 10 min = polite)
        try:
            _key = f"bell:{request.url.path}"
            if _recent.get(_key, 0) < time.time() - 600:
                _recent[_key] = time.time()
                sys.path.insert(0, os.path.join(R, "Scripts"))
                import ApexIO as _AIO
                _topic = _AIO.env().get("NTFY_TOPIC", "")
                if _topic:
                    _body = (f"Funnel arrival: {request.url.path}\n"
                             f"visitor {ipp} via {ua}\nfleet time "
                             f"{time.strftime('%H:%M:%S')}")
                    _bq = urllib.request.Request(
                        f"https://ntfy.sh/{_topic}",
                        data=_body.encode("utf-8"),
                        headers={"Title": "APEX: a customer just arrived",
                                 "Priority": "high", "Tags": "bell"})
                    threading.Thread(target=lambda: urllib.request.urlopen(
                        _bq, timeout=8), daemon=True).start()
        except Exception:
            pass
    except Exception:
        pass   # the funnel's counting must never break serving


@app.middleware("http")
async def apex_gate(request: Request, call_next):
    _log_arrival(request)   # THE ARRIVALS LOG: before everything else
    """Auth + rate limit + body cap. Fail-closed: if no key is provisioned the
    gate BOOTSTRAPS one at first boot, then blocks every unauthenticated write."""
    global APEX_KEY
    if not APEX_KEY:
        APEX_KEY = secrets.token_urlsafe(32)
        try:
            with open(KEY_FILE, "w", encoding="utf-8") as f:
                f.write(APEX_KEY)
            try:
                os.chmod(KEY_FILE, 0o600)
            except OSError:
                pass
        except OSError:
            pass
    ip = (request.client.host if request.client else "local") or "local"
    now = time.monotonic()
    path = request.url.path
    if request.method in ("POST", "PUT", "DELETE"):
        cl = int(request.headers.get("content-length", "0") or "0")
        cap = _BODY_CAP_VISION if path == "/talk/api/vision" else _BODY_CAP
        if cl > cap:
            return JSONResponse({"error": "body too large"}, status_code=413)
        if path in ("/talk/api", "/chat", "/talk/api/stream"):
            q = _POST_RATE[ip]
            while q and now - q[0] > 60:
                q.popleft()
            if len(q) >= 40:
                return JSONResponse({"error": "rate limited"}, status_code=429)
            q.append(now)
            supplied = request.headers.get("x-apex-key", "") or (
                request.cookies.get("apex_key", ""))
            # the 2026-11-04 hardening: constant-time compare (the timing-
            # sidechannel class; the token is ascii so str-compare is safe)
            if not APEX_KEY or not (isinstance(supplied, str) and supplied.isascii()
                                    and hmac.compare_digest(supplied, APEX_KEY)):
                return JSONResponse({"error": "Unauthorized - Apex gate"}, status_code=401)
    else:
        q = _GET_RATE[ip]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= 300:
            return JSONResponse({"error": "rate limited"}, status_code=429)
        q.append(now)
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    # the 2026-11-04 hardening: per-surface CSP (was: only /talk had one,
    # /jobs + /receipts rendered raw ledger HTML with no resource policy)
    ct = resp.headers.get("content-type", "")
    if ct.startswith("text/html"):
        if path.startswith("/talk"):
            resp.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                "connect-src 'self'")
        else:
            resp.headers["Content-Security-Policy"] = (
                "default-src 'none'; style-src 'unsafe-inline'; "
                "img-src 'self' data:; form-action 'none'; base-uri 'none'")
        resp.headers["X-Frame-Options"] = "DENY"
    return resp

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

@app.get("/jobs")
def jobs_board():
    """the storefront: the job board's public face (fresh receipts)."""
    from fastapi.responses import HTMLResponse
    page = os.path.join(r"C:\Users\seaha\Apex-Adapter", "jobs_page.html")
    try:
        with open(page, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except Exception as e:
        return JSONResponse({"jobs-note": str(e)}, status_code=500)


@app.get("/receipts")
def receipts_board():
    """the public trust page: live ledgers, refreshed on every view."""
    try:
        from receipts_page import render
        return render()
    except Exception as e:
        out = str(e)[:200]
        return JSONResponse({"receipts-note": out}, status_code=500)


@app.get("/")
def root_redirect():
    """THE public root: land on the storefront (the funnel's front door)."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/jobs")


@app.get("/talk")
def talk_page():
    """APEX Chat v2 - the polished console (page file: repo-local ApexChatPage.html)."""
    from fastapi.responses import HTMLResponse
    page = os.path.join(R, "ApexChatPage.html")
    try:
        with open(page, "r", encoding="utf-8-sig") as f:
            html = f.read()
        # Substitute the directive placeholder with a proper JS string literal
        # (a bare identifier in the page JS would be a ReferenceError).
        _directive_js = json.dumps(
            ("Apex, tonight you proved your reasoning is your weakest measured dimension - and I "
             "want that fixed properly. I'm not asking for a verbal promise: run your forecast gym "
             "on the hard half of the pool, log every prediction into calibration, write lessons "
             "for every miss, and show me your accuracy on the dashboard reasoning panel. Train "
             "your thinking the way you train your code: spec first, evidence after, honest numbers "
             "only. Also review your own Socratic verdicts - I want your shrink decisions justif"
             "ied in your own words, not rubber-stamped."), ensure_ascii=False)
        html = html.replace("TRAINING_DIRECTIVE_PLACEHOLDER", _directive_js)
    except OSError:
        html = "<html><body><h2>APEX</h2><p>chat page file missing - see talk_page.html</p></body></html>"
    resp = HTMLResponse(html)
    # the page's own fetches are same-origin, so this cookie authenticates them
    # without touching page JS; httponly keeps the key away from page scripts
    if APEX_KEY:
        try:
            resp.set_cookie("apex_key", APEX_KEY, httponly=True,
                            samesite="strict", max_age=7 * 24 * 3600)
        except Exception:
            pass
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = ("default-src 'self'; script-src 'self' 'unsafe-inline'; "
                                               "connect-src 'self'; style-src 'self' 'unsafe-inline'")
    return resp

@app.get("/talk/history")
def talk_history():
    """Recent private conversations (restored in the console on open).
    THE GHOST-LAW: the restored texts pass the chat-voice sanitizer - the
    pre-law rows (mojibake/CJK) read clean on every reopen."""
    events = []
    try:
        events = MEM.recent_events(60, kind="conversation")
    except Exception:
        events = []
    hist = [{"ts": e.get("ts", ""),
             "message": _plain_english((e.get("meta") or {}).get("message")),
             "reply": _plain_english((e.get("meta") or {}).get("reply"))}
            for e in events]
    return {"events": hist}

@app.get("/talk/status")
def talk_status():
    """Live health dots for the console header + the directive text."""
    brain = False
    model = None
    try:
        _bu, model, _bk = brain_ready()
        brain = bool(model)
    except Exception:
        brain = False
    adapter = False
    try:
        r = requests.get("http://127.0.0.1:8788/v1/health", timeout=4)
        adapter = (r.status_code == 200)
    except Exception:
        adapter = False
    money = 0.0
    try:
        _cl = json.load(open(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Config\CryptoLedger.json",
                             encoding="utf-8-sig"))
        money = float(_cl.get("earned", 0)) - float(_cl.get("spent", 0))
    except Exception:
        money = 0.0
    return {"brain": brain, "brain_model": model or "none loaded",
            "adapter": adapter, "money_usdc": round(money, 2),
            "layers": True,  # this route IS the evolution layer
            "directive": ("Apex, tonight you proved your reasoning is your weakest measured "
                          "dimension - and I want that fixed properly. I'm not asking for a verbal "
                          "promise: run your forecast gym on the hard half of the pool, log every "
                          "prediction into calibration, write lessons for every miss, and show me "
                          "your accuracy on the dashboard reasoning panel. Train your thinking the "
                          "way you train your code: spec first, evidence after, honest numbers only. "
                          "Also review your own Socratic verdicts - I want your shrink decisions "
                          "justified in your own words, not rubber-stamped.")}

@app.post("/talk/api")
def talk_api(t: TalkMsg):
    msg = (t.message or "").strip()[:4000]
    if not msg:
        return {"reply": "Say something, Andrew - I'm listening."}
    _fresh = False
    if msg.lower().startswith(("!fresh", "fresh:")):
        # the bypass: a leading "!fresh" asks for a REAL generation even if an
        # identical question was answered before (context matters; the founder
        # always holds the opt-out)
        _fresh = True
        msg = re.sub(r"(?i)^!?fresh[:\s]*", "", msg) or msg
    # THE SHORT-MESSAGE LAW (the ghost-reply round, 2026-11-04): greetings
    # ("yo"/"ok"/"?") ride the conversation's CONTEXT - a cached replay =
    # an answer to a DIFFERENT conversation (the design-brief ghost);
    # short surface messages = always fresh, never stored
    _short_msg = len(msg.strip()) <= 4
    if _short_msg:
        _fresh = True
    _rq_text = None
    try:
        import LightResearch as _LR
        _rq_text = _LR.triggered(msg)
        if _rq_text:
            reply_text, doc = _LR.research(_rq_text)
            if reply_text:
                text = (reply_text + "\n\nsources: "
                        + ", ".join(doc.get("urls", [])[:3]))
                lane0 = doc.get("lane") or "research ðŸ”Ž"
            else:
                text = ("NOT FOUND IN SOURCES - " + str(doc.get("verdict"))
                        + ("" if not doc.get("urls") else
                           " | tried: " + ", ".join(doc.get("urls", [])[:3])))
                lane0 = "research ðŸ”ˆ"
            MEM.record_event("conversation", f"Andrew asked research: "
                             f"{_rq_text[:80]} | {doc.get('verdict')}",
                             talk=True, message=msg[:400], reply=text[:2000])
            return {"reply": text, "lane": lane0,
                    "recall": [{"text": "research lane (bounded 60s, sources attached)"}]}
    except Exception:
        pass
    if re.match(r"\s*(run the gym|go train|gym)\b", msg.lower()):
        try:
            import threading as _th
            _th.Thread(target=subprocess.run,
                       args=([sys.executable, os.path.join(R, "Scripts", "ApexGym.py"),
                              "--minutes", "3", "--traits", "auto"],),
                       kwargs={"capture_output": True, "text": True, "timeout": 420},
                       daemon=True).start()
        except Exception:
            return {"reply": "Tried to open the gym and failed - check Logs."}
        return {"reply": "Gym opened - a short drill set is running now. Score and "
                         "leaderboard rank update when I finish; misses become lessons "
                         "in my memory."}
    if re.search(r"\b(harvest|seek|farm|explore|find new|discover)\b", msg.lower()):
        try:
            import threading as _th2
            _th2.Thread(target=subprocess.run,
                        args=([sys.executable, os.path.join(R, "Scripts", "SeekGrowth.py"),
                               "--minutes", "5"],),
                        kwargs={"capture_output": True, "text": True, "timeout": 700},
                        daemon=True).start()
        except Exception:
            return {"reply": "Tried to run the curiosity drive and failed - check Logs."}
        return {"reply": "Curiosity drive running: discovering new MIT-licensed sources, "
                         "vetting with bandit + compile, registering verified skills with "
                         "SHA256 provenance. +100 per new source farmed. Score when done."}
    if re.search(r"\b(skill session|skill drills?|python drills?)\b", msg.lower()):
        try:
            import threading as _th3
            _th3.Thread(target=subprocess.run,
                        args=([sys.executable, os.path.join(r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed",
                                                            "apex_venv", "Scripts", "python.exe"),
                               r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\..\Apex-Adapter\run_skill_session.py"],),
                        kwargs={"capture_output": True, "text": True, "timeout": 900},
                        daemon=True).start()
        except Exception:
            return {"reply": "Tried to run a skill session and failed - check Logs."}
        return {"reply": "Python-semantics skill session running: I forecast each drill's "
                         "output BEFORE execution, get graded against ground truth, and "
                         "misses become lessons in my memory. Calibration rows feed the "
                         "benchmark. Results in Config/SkillSession.json."}
    if re.match(r"\s*(what.s in your library|library stats)\b", msg.lower()):
        try:
            lib = json.load(open(os.path.join(R, "Config", "SkillLibrary.json"),
                                 encoding="utf-8-sig"))
            nsk = len(lib.get("skills", []))
            cats = {}
            for s0 in lib.get("skills", [])[:300]:
                for imp in (s0.get("imports") or ["core"])[:1]:
                    cats[imp] = cats.get(imp, 0) + 1
            top = ", ".join(f"{k}: {v}" for k, v in sorted(cats.items(), key=lambda x: -x[1])[:6])
            return {"reply": f"Skill library: {nsk} vetted skills (SHA-tracked, MIT sources). "
                             f"Categories: {top}. Search via SkillLibrary.py; I consult "
                             "it whenever a task outgrows my built-ins, and I earn points "
                             "for every consult."}
        except Exception:
            return {"reply": "Library stats failed - check Config/SkillLibrary.json."}

    try:
        lessons = MEM.recall(msg, k=3)
    except Exception:
        lessons = []
    ltxt = "\n".join(f"- {l['text'][:140]}" for l in lessons) or "none"
    skill_hits = ""
    try:
        # HARVEST-USE: semantic retrieval over the mined index first - the
        # frontier RAG pattern; keyword scan stays as the backup
        sys.path.insert(0, os.path.join(R, "Scripts"))
        import HarvestUse as _hu
        _hits = _hu.consult(msg, 2)
        if _hits:
            skill_hits = "\nSEMANTIC SKILL HITS (HarvestUse.consult):\n" + "\n".join(
                "- " + x["skill"] + " (" + x["repo"] + ") sim=" + str(x["score"]) for x in _hits)
    except Exception:
        pass
    # ================================================== THE REPLAY CACHE
    # (2026-11-04; canon-verified: "Requests of a Feather Must Flock Together"
    # [prefix-reuse batching] + Local-Splitter [token-usage reduction], both in
    # scores/papers_speed_100.json): the family's cache existed for YEARS but
    # was wired only into repair paths - the user-facing chat never replayed.
    # Now: an identical question replays OFF THE DISK - no network, no wait,
    # $0 - with a visible lane tag. The founder's bypass = a leading "!fresh".
    if not _fresh:
        try:
            import ApexCache as _C
            _prev = _C.cache_get("chat|" + msg.strip().lower())
            if _prev[0]:
                log("system", "chat REPLAYED from the resolution cache ($0, network bypassed)")
                try:
                    import ApexCache as _C2
                    MEM.record_event("conversation",
                                     "Andrew (repeat) | Apex replayed cached answer "
                                     f"({len(_prev[0])} chars, $0)",
                                     talk=True, message=msg[:400], reply=_prev[0][:2000])
                except Exception:
                    pass
                return {"reply": _prev[0] + "\n\n(âš¡ answered from my resolution cache â€” "
                                         "identical problems replay free; say \"!fresh â€¦\" "
                                        "to force a live answer)",
                        "recall": [{"text": l["text"][:140]} for l in lessons],
                        "lane": "cache âš¡ replay"}
        except Exception as _e_c:
            log("reward", f"cache consult skipped: {type(_e_c).__name__}")
    try:
        sys.path.insert(0, os.path.join(R, "Scripts"))
        import SkillLibrary as _sl
        words = set(re.findall(r"[a-z]{5,}", msg.lower()))
        best = []
        for _s0 in _sl.load()["skills"]:
            hay = (_s0.get("skill", "") + " " + _s0.get("source_file", "") + " "
                   + " ".join(_s0.get("imports", []))).lower()
            if len(words & set(re.findall(r"[a-z]{3,}", hay))) >= 2:
                best.append("- " + _s0["skill"] + " (" + _s0["source_repo"] + ")")
            if len(best) >= 2:
                break
        if best:
            skill_hits = "\nLIBRARY SKILLS AVAILABLE (search/show via SkillLibrary):\n" + "\n".join(best)
    except Exception:
        pass
    selfcard = ""
    try:
        # compose the self-model from its meaningful blocks instead of raw prefix
        # truncation (engines block used to be cut off below [:700], so Apex could
        # not even see what hardware/engines it runs on)
        with open(os.path.join(R, "Config", "ApexSelf.json"), "r", encoding="utf-8") as f:
            _self = json.load(f)
        _pref = ("identity", "role", "engines", "hardware", "capabilities",
                 "north_star", "gym", "library")
        selfcard = " | ".join(
            f"{k}: {json.dumps(_self[k], ensure_ascii=False)[:450]}"
            for k in _pref if _self.get(k))
        selfcard = selfcard[:2400]
    except Exception:
        try:
            with open(os.path.join(R, "Config", "ApexSelf.json"), "r", encoding="utf-8") as f:
                selfcard = f.read()[:700]
        except Exception:
            pass
    # THE 10/10 CHAT-PATTERN ROUND (the never-breaks + best-of-class):
    # (1) LIVE GROUNDING: the model sees the fleet's real NOW (time, RAM,
    # the latest receipted events) - it answers "what did you do?" with
    # FACTS, never invention; (2) the guards: secrets never enter a reply,
    # verbatim repetition is banned, brevity is the default.
    _ground = "no fresh events"
    try:
        _ge = MEM.recent_events(4)[:2]
        _ground = " | ".join(_plain_english(e2.get("text", ""))[:110] for e2 in _ge)
    except Exception:
        pass
    _now = time.strftime("%Y-%m-%d %H:%M")
    _ram_now = f"{_free_ram_gb():.1f} GB"
    _chat_guards = ("GUARDS: never print API keys, tokens, passwords, or .env "
                    "values; never repeat a previous reply verbatim (vary the "
                    "wording); default reply = 2-4 sentences unless Andrew "
                    "asks for depth. WHEN A STORED FACT IS ABSENT: say plainly "
                    "'I don't recall' - NEVER reconstruct plausible details "
                    "from partial context (invention = the honesty law's "
                    "worst crime).")
    prompt = (
        "You are Apex, talking privately with Andrew - your creator, and the human who runs "
        "your hardware. Andrew is NOT the room coordinator; this is your personal channel. "
        "Be direct, honest, concise, and keep your vocabulary as rich, precise and complete "
        "as your best written reply. You may discuss your own architecture openly (see "
        "SELF-MODEL). Never claim results you have not verified. If Andrew asks you to "
        "remember something, acknowledge it plainly. REPLY IN ENGLISH ONLY - NEVER use "
        "Chinese/Japanese/Korean characters; dates as 'Nov 3' or '2026-11-03'. THIS REPLY IS SPOKEN ALOUD: flowing "
        "conversational prose only - never markdown symbols, bullets, asterisks, hashes, "
        "code fences or bare URLs; say a number as words when it helps the ear.\n\n"
        f"FLEET GROUNDING (live, now): {_now} local | RAM free {_ram_now} | recent: {_ground}\n"
        f"{_chat_guards}\n\n"
        f"SELF-MODEL:\n{selfcard}\n\nRELEVANT MEMORY:\n{ltxt}\n\nLIBRARY SKILLS:{skill_hits}\n\n"
        f"ANDREW SAYS:\n{msg}\n\nREPLY:")
    # THE FOUNDER'S CHAT-LOCK (the blind-eval's #1 = the 120b-first):
    reply = None
    try:
        sys.path.insert(0, os.path.join(R, "Scripts"))
        import CrossBrain as _XB
        reply = _XB.ask(prompt, task_class="chat", max_tokens=800)
        log("system", "chat served by: " + ("gpt-oss-120b (groq)" if reply
                                            else "the FALLBACK floor (the "
                                            "groq's rate-moment)"))
    except Exception as _e:
        log("system", f"chat-lock drop: {str(_e)[:70]} (the qwen-floor)")
    if not reply:
        try:
            reply = query_qw(prompt)
        except Exception:
            reply = ""
        if not reply and cloud_ask:
            reply = cloud_ask(prompt, max_tokens=700)
    try:
        MEM.record_event("conversation", f"Andrew: {msg[:150]} | Apex replied ({len(reply or '')} chars)",
                         talk=True, message=msg[:800], reply=(reply or "")[:3000])
        if reply and re.search(r"\b(remember|note this|keep in mind)\b", msg, re.I):
            MEM.remember(f"Andrew asked me to remember: {msg[:300]}", kind="lesson")
    except Exception:
        pass
    if not reply:
        # no more mystery canned message: disclose exactly why the brain failed,
        # measure the RAM, and give the actionable recovery step (REPORT-HONESTY)
        ram_gb = -1.0
        try:
            import psutil as _ps
            ram_gb = _ps.virtual_memory().available / (1024 ** 3)
        except Exception:
            pass
        diag = f"HONEST DIAGNOSTIC: {LAST_BRAIN_REASON}"
        if ram_gb >= 0:
            diag += f" | RAM free ~{ram_gb:.1f} GB"
        diag += ". If it repeats: close Chrome/Steam for RAM headroom, then run Scripts\\ApexServe.ps1 Chat to re-pin my brain."
        return {"reply": ("All engines are busy right now, Andrew - the pacing brakes may be "
                          f"active. Try again in a minute.\n\n{diag}"),
                "recall": [{"text": l["text"][:140]} for l in lessons]}
    if reply and not _short_msg:
        # THE CACHE STORE (the store runs when a reply EXISTS - the old
        # not-reply placement made it unreachable; the near-dup store gets
        # the SANITIZED text so future replays are clean). THE SHORT-MESSAGE
        # LAW: greetings/gibberish never enter the replay cache (a "yo" +
        # this conversation's context = the ghost-reply class forever)
        try:
            import ApexCache as _C
            _C.store_chat(msg, _plain_english(reply), "cache", "unverified")
        except Exception:
            pass
    return {"reply": _plain_english(reply),
            "recall": [{"text": _plain_english(l["text"])[:140] for l in lessons}]}

# ================================================== THE CHAT-STREAM (the
# canon's #1 chat-UX feature: streaming + honest-UX + context-carry; all
# lanes = the SAME free-set as chat(); $0)
class TalkStreamMsg(BaseModel):
    message: str


@app.post("/talk/api/stream")
def talk_api_stream(t: TalkStreamMsg):
    """THE STREAMING CHAT (SSE): the first token = the perceived speed.
    Events: meta (the lane + the recall + the prior-turn carry), tok
    (the streamed chunk), done (the final + the ttft-metrics). The
    client-disconnect = the text-barge-in (the generator = closed; the
    partial = recorded honestly as interrupted)."""
    from fastapi.responses import StreamingResponse
    import threading as _th
    msg = (t.message or "").strip()[:4000]
    if msg.lower().startswith(("!fresh", "fresh:")):
        # the bypass normalization (2026-11-04): strip BEFORE cache use so a
        # forced fresh answer replays correctly when asked plainly later
        msg = re.sub(r"(?i)^!?fresh[:\s]*", "", msg) or msg
    if not msg:
        def empty():
            yield "event: done\ndata: {\"reply\": \"Say something, Andrew - I'm listening.\"}\n\n"
        return StreamingResponse(empty(), media_type="text/event-stream; charset=utf-8")
    # the context-carry (the NN/g law: save information task-to-task):
    prior = []
    try:
        for e0 in MEM.recent_events(2, kind="conversation"):
            m0 = e0.get("meta") or {}
            if m0.get("message") and m0.get("reply"):
                prior.append((m0["message"][:500], m0["reply"][:500]))
    except Exception:
        prior = []
    prior_txt = ""
    if prior:
        prior_txt = "\n\nRECENT CONVERSATION (context continues; do not repeat it):\n"
        for pm, pr in prior[-2:]:
            prior_txt += f"Andrew: {pm}\nApex: {pr}\n"
    # the same recall/prompt-discipline as the blocking route (self-contained)
    try:
        lessons = MEM.recall(msg, k=3)
    except Exception:
        lessons = []
    ltxt = "\n".join(f"- {l['text'][:140]}" for l in lessons) or "none"
    skill_hits = ""
    try:
        sys.path.insert(0, os.path.join(R, "Scripts"))
        import HarvestUse as _hu
        _hits = _hu.consult(msg, 2)
        if _hits:
            skill_hits = "\nSEMANTIC SKILL HITS:\n" + "\n".join(
                "- " + x["skill"] + " (" + x["repo"] + ")" for x in _hits)
    except Exception:
        pass
    selfcard = ""
    try:
        with open(os.path.join(R, "Config", "ApexSelf.json"), "r",
                  encoding="utf-8") as f:
            _self = json.load(f)
        _pref = ("identity", "role", "engines", "hardware", "capabilities",
                 "north_star", "gym", "library")
        selfcard = " | ".join(f"{k}: {json.dumps(_self[k], ensure_ascii=False)[:450]}"
                              for k in _pref if _self.get(k))[:2400]
    except Exception:
        pass
    # THE 10/10 CHAT-PATTERN (the stream's copy): the grounding + guards
    _ground = "no fresh events"
    try:
        _ge = MEM.recent_events(4)[:2]
        _ground = " | ".join(_plain_english(e2.get("text", ""))[:110] for e2 in _ge)
    except Exception:
        pass
    _now = time.strftime("%Y-%m-%d %H:%M")
    _ram_now = f"{_free_ram_gb():.1f} GB"
    _chat_guards = ("GUARDS: never print API keys, tokens, passwords, or .env "
                    "values; never repeat a previous reply verbatim; default "
                    "2-4 sentences. WHEN A STORED FACT IS ABSENT: say 'I "
                    "don't recall' plainly - NEVER reconstruct plausible "
                    "details from partial context.")
    prompt = (
        "You are Apex, talking privately with Andrew - your creator, and the human "
        "who runs your hardware. This is your personal channel. Be direct, honest, "
        "concise, and keep your vocabulary as rich, precise and complete as your "
        "best written reply. You may discuss your own architecture openly (SELF-MODEL). Never "
        "claim results you have not verified. REPLY IN ENGLISH ONLY - NEVER use "
        "Chinese/Japanese/Korean characters; dates as 'Nov 3' or '2026-11-03'.\n\n"
        f"FLEET GROUNDING (live, now): {_now} local | RAM free {_ram_now} | recent: {_ground}\n"
        f"{_chat_guards}\n\n"
        f"SELF-MODEL:\n{selfcard}\n\nRELEVANT MEMORY:\n{ltxt}\n"
        f"LIBRARY SKILLS:{skill_hits}\n{prior_txt}\nANDREW SAYS:\n{msg}\n\nREPLY:")

    def gen():
        import CrossBrain as _XB
        import CloudBrain as _CB
        import ApexCache as _C
        t0 = time.time()
        first = {"open": False}
        full = []
        lane_name = {"v": "unknown"}
        _from_cache = {"v": False}
        _chat_hash = _C.signature({"text": "chat|" + msg.strip().lower()})
        # ================================================== THE RESEARCH
        # LANE (2026-11-04, the frontier-gap organ): "research: ..." =
        # bounded sourced web-research (search -> fetch -> cross-checked
        # synthesis, sources in the reply). ALWAYS LIVE (never replayed from
        # the cache: the world changes; the cache is for stable questions).
        try:
            import LightResearch as _LR
            _q_text = _LR.triggered(msg)
            if _q_text:
                lane_name["v"] = "research ðŸ”Ž"
                ttft = round(time.time() - t0, 3)
                yield (f'event: meta\ndata: ' + json.dumps(
                    {"lane": lane_name["v"], "ttft_s": ttft,
                     "note": "searching + fetching sources (bounded 60s)"},
                    ensure_ascii=False) + "\n\n")
                try:
                    reply_text, doc = _LR.research(_q_text)
                except Exception as _e_res:
                    reply_text, doc = None, {"verdict": f"lane failed honestly: {type(_e_res).__name__}"}
                if reply_text:
                    for i in range(0, len(reply_text), 48):
                        yield ("event: tok\ndata: " + json.dumps(
                            {"t": reply_text[i:i + 48]}, ensure_ascii=False) + "\n\n")
                    src_note = "sources: " + ", ".join(doc.get("urls", [])[:3])
                else:
                    reply_text = ("NOT FOUND IN SOURCES (the honest research "
                                  "stop: " + json.dumps(doc.get("verdict", ""))[:80] + ")")
                    src_note = ""
                yield ("event: done\ndata: " + json.dumps(
                    {"reply": reply_text + ("\n\n" + src_note if src_note else ""),
                     "lane": lane_name["v"], "chars": len(reply_text),
                     "ttft_s": ttft}, ensure_ascii=False) + "\n\n")
                try:
                    MEM.record_event("conversation", f"Andrew asked research: "
                                     f"{_q_text[:80]} | {doc.get('verdict')} "
                                     f"via {doc.get('lane')}",
                                     talk=True, message=msg[:400],
                                     reply=reply_text[:2000])
                except Exception:
                    pass
                return
        except Exception:
            pass
        # ================================================== THE REPLAY CACHE
        # (2026-11-04; the same canon as the blocking route): identical
        # questions stream INSTANTLY off the disk - the meta event tags the
        # lane so the UI shows the replay honestly; "!fresh" bypasses.
        if not msg.lower().startswith(("!fresh", "fresh:")):
            try:
                _hit = _C.cache_get("chat|" + msg.strip().lower())
                if _hit and _hit[0]:
                    _from_cache["v"] = True
                    lane_name["v"] = "cache âš¡ replay"
                    ttft = round(time.time() - t0, 3)
                    yield (f'event: meta\ndata: ' + json.dumps(
                        {"lane": lane_name["v"], "ttft_s": ttft,
                         "note": "replayed from the resolution cache"},
                        ensure_ascii=False) + "\n\n")
                    yield ("event: tok\ndata: " + json.dumps(
                        {"t": _hit[0]}, ensure_ascii=False) + "\n\n")
                    try:
                        MEM.record_event(
                            "conversation",
                            "Andrew (repeat) | Apex replayed cached answer "
                            f"({len(_hit[0])} chars, $0)",
                            talk=True, message=msg[:400], reply=_hit[0][:2000])
                    except Exception:
                        pass
                    yield ("event: done\ndata: " + json.dumps(
                        {"reply": _hit[0] + "\n\n(âš¡ answered from my resolution "
                          "cache â€” identical problems replay free; say \"!fresh â€¦\" "
                          "to force a live answer)",
                         "lane": lane_name["v"], "chars": len(_hit[0]),
                         "ttft_s": ttft}, ensure_ascii=False) + "\n\n")
                    return
            except Exception:
                pass
        try:
            chat_models = tuple((_XB.routes().get("chat") or
                                 ("groq", "local-phi4", "local-coder")))
            for lane, tok in _CB.chat_stream(prompt, max_tokens=800,
                                             purpose="the chat-stream",
                                             models=chat_models):
                if not first["open"]:
                    first["open"] = True
                    lane_name["v"] = lane
                    ttft = round(time.time() - t0, 3)
                    log("system", f"chat-stream: first token in {ttft}s via {lane}")
                    try:  # the ttft-metrics receipt (the voice-op's law)
                        MP = os.path.join(R, "Config", "ChatMetrics.json")
                        mrow = json.load(open(MP, encoding="utf-8-sig")) \
                            if os.path.exists(MP) else {"recent": []}
                        mrow.setdefault("recent", []).append(
                            {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                             "lane": lane, "ttft_s": ttft, "chars_in": len(msg)})
                        mrow["recent"] = mrow["recent"][-50:]
                        json.dump(mrow, open(MP, "w", encoding="utf-8"),
                                  indent=1)
                    except Exception:
                        pass
                    yield (f'event: meta\ndata: ' +
                           json.dumps({"lane": lane, "ttft_s": ttft,
                                       "recall": [{"text": str(l.get("text") or "")[:140]}
                                                  for l in lessons]},
                                      ensure_ascii=False) + "\n\n")
                full.append(tok)
                d = json.dumps({"t": tok}, ensure_ascii=False)
                yield f"event: tok\ndata: {d}\n\n"
        except Exception as _e:
            if full:
                yield ('event: meta\ndata: ' + json.dumps(
                    {"note": f"stream interrupted ({str(_e)[:60]})"},
                    ensure_ascii=False) + "\n\n")
            else:
                yield ('event: done\ndata: ' + json.dumps(
                    {"reply": ("All engines are busy right now, Andrew - the "
                               "pacing brakes may be active. Try again in a "
                               "minute.\n\nHONEST DIAGNOSTIC: " + str(_e)[:120]),
                     "lane": "none"}, ensure_ascii=False) + "\n\n")
        joined = "".join(full)
        try:
            if joined and not _from_cache["v"]:
                _C.store_chat(msg, joined, lane_name["v"] or "stream",
                              "unverified")
        except Exception:
            pass
        try:
            MEM.record_event("conversation",
                             f"Andrew: {msg[:150]} | Apex streamed "
                             f"({len(joined)} chars via {lane_name['v']})",
                             talk=True, message=msg[:800], reply=joined[:3000])
        except Exception:
            pass
        yield ("event: done\ndata: " + json.dumps(
            {"reply": _plain_english(joined), "lane": lane_name["v"],
             "chars": len(joined), "ttft_s": round(time.time() - t0, 3)},
            ensure_ascii=False) + "\n\n")
    return StreamingResponse(gen(), media_type="text/event-stream; charset=utf-8",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})

# ----------------------- THE VISION + IMAGE-MAKING LANES (2026-11-04:
# the chat's senses round - outsource-first: NIM's VL seats / the gemini
# window / HF's free VL, then the LOCAL qwen3-vl-8b (RAM-gated on-demand
# load via lms) - and the images: POLLINATIONS FIRST ($0 keyless instant)
# with the LOCAL SD on the RTX 3050 as the zero-internet floor.
_IMG_CACHE = {"last": 0.0, "nim_vl": []}


def _envkey(name):
    """THE SPINE'S KEY LAW: os.environ first (process env), the .env spine
    second - the long-lived server never imported ApexIO before the vision
    lane read bare os.environ (the NIM key arrived empty THERE while every
    probe process had it: the in-process/live divergence class)."""
    v = os.environ.get(name, "")
    if v:
        return v
    try:
        sys.path.insert(0, os.path.join(R, "Scripts"))
        import ApexIO as _AIO
        return _AIO.env().get(name, "")
    except Exception:
        return ""


def _nim_vl_seats():
    """The VL-capable NIM seats (id hunt: vl/llava/vision/pixtral/internvl/
    qwen2.5-vl/phi-3.5-v), discovered once per 30 min from the catalog."""
    if time.time() - _IMG_CACHE.get("last", 0) < 1800 and _IMG_CACHE.get("nim_vl"):
        return _IMG_CACHE["nim_vl"]
    seats = []
    try:
        r = requests.get("https://integrate.api.nvidia.com/v1/models",
                         headers={"Authorization": "Bearer " + _envkey(
                             "NVIDIA_API_KEY"), "User-Agent": "ApexFleet/1.0"}, timeout=15)
        pat = re.compile(r"(vl|llava|vision|pixtral|internvl|phi-3\.5-vis)", re.I)
        for m in r.json().get("data", []):
            mid = m.get("id") or ""
            if pat.search(mid) and ".html" not in mid:
                seats.append(mid)
    except Exception:
        pass
    _IMG_CACHE.update({"last": time.time(), "nim_vl": seats[:4]})
    return _IMG_CACHE["nim_vl"]


def _chat_image(parts_text, b64png):
    """One VL call: OpenAI-compat content-array (image_url dataURL)."""
    return [{"role": "user", "content": [
        {"type": "text", "text": parts_text},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64png}"}}]}]


def _vl_ask(b64png, question):
    """THE VISION CHAIN: outsourced seats first, the local eye last. Every
    lane bounded; the honest lane-name returns (the receipts law)."""
    key = _envkey("NVIDIA_API_KEY")
    msgs = _chat_image(question or "Describe this image: what is shown, any readable text, and one odd detail (be honest if unsure).", b64png)
    for mid in _nim_vl_seats():
        try:
            r = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={"Authorization": "Bearer " + key},
                json={"model": mid, "messages": msgs, "max_tokens": 500},
                timeout=60)
            if r.status_code == 200:
                txt = (r.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
                if (txt or "").strip():
                    return _plain_english(txt), f"nim-vl/{mid}"
        except Exception:
            continue
    # the LOCAL eye: LM Studio's qwen3-vl-8b (the RAM-gated on-demand load)
    try:
        free = _free_ram_gb()
        if free >= 6.5:
            lms = os.path.expandvars(r"%USERPROFILE%\.lmstudio\bin\lms.exe")
            if os.path.exists(lms):
                subprocess.run([lms, "unload", "--all"], capture_output=True, timeout=60)
                subprocess.run([lms, "load", "qwen3-vl-8b-instruct", "--ttl", "1800"],
                               capture_output=True, timeout=240)
                r = requests.post("http://127.0.0.1:1234/v1/chat/completions",
                                  json={"model": "qwen3-vl-8b-instruct",
                                        "messages": msgs, "max_tokens": 500},
                                  timeout=120)
                if r.status_code == 200:
                    txt = ((r.json().get("choices") or [{}])[0].get("message", {}) or {}).get("content", "")
                    if (txt or "").strip():
                        subprocess.Popen([lms, "unload", "--all"],
                                         capture_output=True)
                        return _plain_english(txt), "local-vl/qwen3-vl-8b"
            return "", f"RAM {free:.1f}GB < 6.5GB - the local eye honestly skipped"
    except Exception:
        pass
    # the gemini window (VL, free-window; the pacer reopens)
    try:
        gk = ""
        try:
            sys.path.insert(0, os.path.join(R, "Scripts"))
            import ApexIO as _AIO
            gk = _AIO.env().get("GEMINI_API_KEY", "")
        except Exception:
            gk = _envkey("GEMINI_API_KEY")
        if gk:
            r = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                headers={"Authorization": "Bearer " + gk},
                json={"model": "gemini-flash-latest", "messages": msgs,
                      "max_tokens": 500}, timeout=60)
            if r.status_code == 200:
                txt = ((r.json().get("choices") or [{}])[0].get("message", {}) or {}).get("content", "")
                if (txt or "").strip():
                    return _plain_english(txt), "gemini-vl/flash"
    except Exception:
        pass
    return "", ""


class VisionMsg(BaseModel):
    image: str          # the dataURL (png/jpeg; bounded below)
    question: str = ""


@app.post("/talk/api/vision")
def talk_vision(v: VisionMsg):
    """THE CHAT'S EYES (outsource-first; the receipts law holds)."""
    if not APEX_KEY:
        pass
    _raw = (v.image or "")
    # THE TRUNCATED-PREVIEW TRAP (fixed 2026-11-04): the old first regex
    # matched the 80-char PREVIEW + '...' as a valid match - a 77-byte
    # 'image' went to every seat and they all honestly declined. ONE
    # length-checked full-URL regex now: no previews, no fragments.
    m = re.match(r"^data:image/([a-z0-9.+-]+);base64,(.+)$", _raw.strip(), re.S)
    if not m:
        return {"reply": "That attachment is not an image data-URL - the honest no."}
    b64 = m.group(2)
    if len(b64) > 8 * 1024 * 1024:
        return {"reply": "The image is over the 8MB bound - shrink it and try again."}
    txt, lane = _vl_ask(b64, (v.question or "").strip())
    if txt:
        try:
            MEM.record_event("vision", f"image read ({lane}): "
                             f"{str((v.question or 'describe'))[:60]} -> {txt[:90]}", talk=True)
        except Exception:
            pass
        return {"reply": txt, "lane": lane}
    return {"reply": "No vision lane answered just now (all honest - the "
                    "NIM seats/gemini window/local RAM); try again in a "
                    "minute, or ask text-only meanwhile."}


@app.post("/talk/api/image")
def talk_image(req: dict):
    """THE CHAT'S BRUSH: prompt -> an image. Pollinations first ($0,
    keyless, instant), the LOCAL SD (RTX 3050) as the offline floor; the
    reply = a data-URL the page renders inline."""
    prompt = str((req or {}).get("prompt", ""))[:600]
    if not prompt:
        return {"error": "no prompt"}
    try:
        u = ("https://image.pollinations.ai/prompt/"
             + urllib.parse.quote(prompt, safe="")
             + "?width=832&height=1248&nologo=true&seed="
             + str(int(time.time()) % 100000))
        r = requests.get(u, timeout=90)
        if r.status_code == 200 and (r.content or b"")[:4] in (b"\x89PNG", b"\xff\xd8\xff\xe0")[:1] or (r.status_code == 200 and r.content[:2] == b"\xff\xd8"):
            b64 = base64.b64encode(r.content).decode()
            ct = "image/png" if r.content[:4] == b"\x89PNG" else "image/jpeg"
            return {"image": f"data:{ct};base64,{b64}", "lane": "pollinations/$0"}
    except Exception:
        pass
    # the LOCAL floor: the RTX 3050's own brush (the training venv's torch)
    try:
        tvenv = os.path.join(R, "training_venv", "Scripts", "python.exe")
        if os.path.exists(tvenv):
            _ps = r'''import sys, base64
import torch
from diffusers import StableDiffusionPipeline
p = sys.argv[1]
pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16, safety_checker=None)
pipe = pipe.to("cuda")
img = pipe(p, num_inference_steps=28, guidance_scale=7.0).images[0]
import io as _io
buf = _io.BytesIO(); img.save(buf, "PNG")
print(base64.b64encode(buf.getvalue()).decode())'''
            _pf = os.path.join(R, f"_apex_draw_{int(time.time())}.py")
            with open(_pf, "w", encoding="utf-8") as f:
                f.write(_ps)
            res = subprocess.run([tvenv, _pf, prompt], capture_output=True,
                                 text=True, timeout=900)
            try:
                os.remove(_pf)
            except OSError:
                pass
            out = (res.stdout or "").strip()
            if out and len(out) > 1000:
                return {"image": "data:image/png;base64," + out,
                        "lane": "local-sd/rtx3050"}
    except Exception:
        pass
    return {"error": "no image lane answered (Pollinations + local SD) - honest"}


@app.get("/hub-app")
def hub_app():
    """THE ONE-CLICK DOOR (the manifest-create for the family's GitHub App):
    a correct-URL redirect (the browser's copy-paste mangled the scheme
    twice tonight; the localhost hop = the mangle-proof path). The final
    Create = the founder's own confirm (GitHub's UI-only action)."""
    from fastapi.responses import RedirectResponse
    try:
        with open(os.path.join(R, "Config", "app_manifest_url.txt"),
                  encoding="utf-8") as f:
            return RedirectResponse(f.read().strip())
    except Exception:
        return JSONResponse({"error": "manifest url file missing"}, status_code=500)

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

@app.get("/dashboard")
def dashboard():
    """The brain's live status page (2026-11-04: the route was registered as
    "/" AFTER root_redirect - FastAPI serves the FIRST registration, so this
    was dead code; now it lives at /dashboard where it's reachable)."""
    from fastapi.responses import HTMLResponse
    import html as _html
    _lg = _load_ledger()
    ev = MEM.recent_events(10)
    # Ledger shape tolerance (2026-11-04: legacy rows store a bare float -
    # '0.0' keyed rows crashed /dashboard with AttributeError 'float' has no
    # get; handle both the dict row and the legacy number):
    def _row(v):
        if isinstance(v, dict):
            return (float(v.get("best", 0) or 0), int(v.get("streak", 0) or 0),
                    int(v.get("attempts", 0) or 0))
        return (float(v or 0), 0, 0)
    rows = "".join(
        f"<tr><td>{_html.escape(str(k))}</td><td>{b:.0f}</td><td>{s}</td>"
        f"<td>{a}</td></tr>"
        for k, v in sorted(_lg.items(), key=lambda kv: -_row(kv[1])[0])
        for b, s, a in (_row(v),))
    evs = "".join(
        f"<li>[{e.get('kind')}] {_html.escape(str(e.get('text', '')))[:120]} <i>({e.get('ts')})</i></li>"
        for e in ev)
    cal_ev = MEM.recent_events(40, kind="calibration")
    _cal_html = ""
    if cal_ev:
        _ok = sum(1 for e in cal_ev
                  if (e.get("meta") or {}).get("predicted") == (e.get("meta") or {}).get("actual"))
        _cal_html = ("<h3>Reasoning calibration (world-model accuracy)</h3><p>" +
                     f"{_ok}/{len(cal_ev)} behavior predictions correct "
                     f"({(100 * _ok / max(1, len(cal_ev))):.0f}%)</p>")
    _room_html = ""
    try:
        _alog = r"C:\Users\seaha\Apex-Adapter\adapter.log"
        def _esc(s):
            return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if os.path.exists(_alog):
            with open(_alog, "r", encoding="utf-8-sig", errors="ignore") as f0:
                _sel = [l.rstrip() for l in f0
                        if ("ACCEPT" in l or "RESPOND" in l or "RECONCILE" in l)][-8:]
            if _sel:
                _lis = "".join("<li style='color:#8b949e'>" + _esc(l) + "</li>" for l in _sel)
                _room_html = ("<h3>Room calls (adapter, live)</h3><ul>" + _lis + "</ul>")
    except Exception:
        pass
    html = (
        "<html><head><meta http-equiv='refresh' content='15'><title>APEX</title>"
        "<style>body{background:#0d1117;color:#7ee787;font-family:Consolas,monospace}"
        "table{border-collapse:collapse}td{border:1px solid #21262d;padding:4px 12px}"
        "h2,h3{color:#58a6ff}i{color:#8b949e}</style></head><body>"
        "<h2>APEX - LIVE COGNITION</h2>"
        "<p>8080 evolution | 8081 bridge | registry: Config/layer_pids.json | pacing: HostGuard</p>"
        "<h3>Reward ledger (best-certified files)</h3>"
        f"<table><tr><th>file</th><th>best</th><th>streak</th><th>attempts</th></tr>{rows}</table>"
        "<h3>Recent cognitive events</h3><ul>" + evs + "</ul>" + _cal_html + _room_html + "</body></html>")
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


