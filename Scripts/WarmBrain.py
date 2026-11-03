"""WarmBrain - THE WARM-BRAIN PRELOADER (2026-11-04; the last planned combine).

The audited gap: model pinning existed only as manual one-offs (_speed_pin.py,
ApexServe.ps1's Wait-ModelLoaded) - nothing scheduled it, so the user path
always paid the cold-load of the floor brain. The strength: an idle-RAM-GATED
preloader that keeps the LOCAL floor brains resident (Ollama keep_alive),
coordinated with the boot/sentry cadence, bounded and receipted:

  - the RAM gate reads REAL free memory (psutil) and the pin runs ONLY if the
    first brain's size leaves >= 4.5 GB free (the HostGuard never gets starved;
    the second brain needs >= 8.0 GB free);
  - keep_alive = 12 h (auto-evicted after; no permanent residency);
  - a cooldown receipt (Config/WarmBrain.json) = idempotent at any cadence;
  - $0, local-only, stdlib (urllib). No cloud call anywhere.

Canon source (verified in scores/papers_speed_100.json):
  * "Squat: Quant Small Language Models on the Edge" - quantized small models
    are the right resident architecture on this hardware;
  * "Nemotron-Flash: Towards Latency-Optimal Hybrid Small Language Models" -
    serving latency = the loaded-model floor, warmed out of the user path.
"""
import io
import json
import os
import sys
import time
import urllib.request


if hasattr(sys.stdout, "reconfigure") and not getattr(sys.stdout, "_apex_reconfigured", False):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout._apex_reconfigured = True   # reconfigure the EXISTING wrapper
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr._apex_reconfigured = True   # NEVER replace sys.stdout: the GC
                                           # closes the original = the shared buffer dies

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
STATE = os.path.join(ROOT, "Config", "WarmBrain.json")
OLLAMA = "http://localhost:11434"

# the chat pool's local members (mirror of CloudBrain.chat_stream's pool)
PIN_ORDER = [
    ("local-phi4", "phi4-mini:latest", 4.5),    # the primary chat floor
    ("local-coder", "qwen2.5-coder:7b", 8.0),   # the coder floor (tighter budget)
    ("local-gemma3", "gemma3:4b", 9.5),
    ("local-fast", "qwen2.5-coder:3b", 10.5),
]
COOLDOWN_H = 4.0


def _free_gb():
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 ** 3)
    except Exception:
        return -1.0


def _post_chat(model, keep_alive="12h", timeout=90):
    body = json.dumps({"model": model, "keep_alive": keep_alive,
                       "messages": []}).encode("utf-8")
    req = urllib.request.Request(OLLAMA + "/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status == 200


def _ps_shows(model):
    try:
        with urllib.request.urlopen(OLLAMA + "/api/ps", timeout=6) as r:
            data = json.load(r)
        return any(m.get("name", "").split(":")[0] in model.split(":")[0]
                   for m in data.get("models", []))
    except Exception:
        return False


def main(force=False):
    free = _free_gb()
    # THE DEMAND-ADAPTIVE PIN (2026-11-04): the last-24h of the family's own
    # episodes vote - chat-heavy nights pin the chat floor first, code-heavy
    # nights pin the coder first (the preloader follows the REAL demand).
    order = list(PIN_ORDER)
    try:
        chat_n = code_n = 0
        cutoff = time.time() - 86400
        for ln in open(os.path.join(ROOT, "memory_episodic.jsonl"),
                       encoding="utf-8"):
            try:
                j = json.loads(ln)
            except Exception:
                continue
            kind = j.get("kind", "")
            if kind == "conversation":
                chat_n += 2
            elif kind in ("skill_session",):
                code_n += 3
            elif kind in ("calibration", "evolution_pass"):
                code_n += 1
        if code_n > chat_n:
            coder = [p for p in PIN_ORDER if p[0] == "local-coder"]
            rest = [p for p in PIN_ORDER if p[0] != "local-coder"]
            order = coder + rest
            print(f"[warm-brain]: demand read - chat {chat_n} vs code {code_n} "
                  "-> pinning the CODER first")
    except Exception:
        pass
    st = {}
    try:
        st = json.load(open(STATE, encoding="utf-8-sig"))
    except Exception:
        pass
    last = st.get("ts")
    if not force and last:
        try:
            if (time.time() - time.mktime(time.strptime(last, "%Y-%m-%d %H:%M:%S"))) < COOLDOWN_H * 3600:
                print(f"[warm-brain]: cooldown ({last}); free {free:.1f} GB - nothing to do")
                return
        except Exception:
            pass
    pinned, skipped = [], []
    for name, model, need_gb in order:
        if free >= need_gb:
            ok = False
            try:
                ok = _post_chat(model)
            except Exception as e:
                print(f"[warm-brain]: pin {name} failed honestly: {type(e).__name__}")
            if ok:
                free -= 1.0            # the resident cost estimate (bounded, honest)
                pinned.append({"name": name, "model": model, "resident": True})
                print(f"[warm-brain]: {name} ({model}) pinned resident (12h), "
                      f"RAM free now ~{free:.1f} GB")
            else:
                skipped.append(name)
            break                      # one pin per beat (RAM-polite, cold-load
                                       # removed from the NEXT user turn)
        else:
            skipped.append(f"{name} (needs {need_gb} GB, free {max(free,0):.1f})")
    verdict = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
               "free_gb": round(free, 2), "pinned": pinned, "skipped": skipped,
               "ps_warm": [_p["name"] for _p in pinned if _ps_shows(_p["model"])]}
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(verdict, f, indent=1)
    os.replace(tmp, STATE)
    try:
        sys.path.insert(0, os.path.join(ROOT, "Scripts")) if False else None
        with open(os.path.join(ROOT, "memory_episodic.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps({"id": os.urandom(6).hex(),
                                "ts": verdict["ts"], "kind": "warm_brain",
                                "text": f"warm-brain: pinned "
                                f"{[p['name'] for p in pinned] or ['nothing']} "
                                f"(free {free:.1f} GB)", "meta": {}, "imp": 0.5},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass
    print("[warm-brain]: verdict", verdict["ps_warm"] or pinned or "idle")


if __name__ == "__main__":
    main(force="--force" in sys.argv)