"""MODELSWEEP: the safe-download organ (the hybrid-expansion). Pulls the
small-model candidates to DISK only (never RAM-loaded unless testing):
phi4-mini, gemma3:4b, deepseek-r1:7b (the reasoning-judge candidate).
Per candidate: the disk-gate -> the pull (their CDN, $0) -> the BOUNDED
load-proof (one tiny ask; the RAM-delta measured) -> register -> the auto-
unload (keep_alive=0). NEVER two loads; the 7b stays the code-keeper."""
import json
import os
import subprocess
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OLLAMA = "ollama"
CANDS = [
    ("phi4-mini:latest", "the fast-general small (the copy/summarize lane)"),
    ("gemma3:4b", "the 2025-gen small-general (the alternate-general lane)"),
    ("deepseek-r1:7b", "the REASONING distill (the deep-judge window "
                       "candidate; the thinking-tokens = slow)"),
]


def ram_gb():
    try:
        import psutil
        return psutil.virtual_memory().available / 2**30
    except Exception:
        return 0.0


def disk_gb():
    try:
        d = os.path.splitdrive(os.path.expanduser("~"))[0] or "C:"
        import shutil
        u = shutil.disk_usage(d + "\\")
        return u.free / 2**30
    except Exception:
        return 0.0


def run():
    free_d = disk_gb()
    print(f"[model-sweep] the disk-gate: {free_d:.1f}GB free "
          f"(needs >= 12GB: {'PASS' if free_d >= 12 else 'HOLD'})")
    got = []
    if free_d < 12:
        with open(os.path.join(ROOT, "Config", "model_sweep.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "verdict": "HOLD-honest (the disk gate)",
                       "free_disk_gb": round(free_d, 1)}, f,
                      ensure_ascii=False, indent=1)
        return
    for model, role in CANDS:
        if ram_gb() < 2.2:
            print(f"[model-sweep] the RAM-gate pauses before {model}")
            break
        print(f"[model-sweep] pulling {model} ({role}) - to DISK...")
        r = subprocess.run([OLLAMA, "pull", model], capture_output=True,
                           text=True, timeout=900)
        if r.returncode != 0:
            print(f"[model-sweep] {model}: HONEST-SKIP "
                  f"({(r.stderr or 'no such id')[:60]})")
            continue
        # the bounded load-proof: ONE tiny ask + the RAM-delta
        before = ram_gb()
        q = subprocess.run([OLLAMA, "run", model, "Reply ONLY the word: ok"],
                           capture_output=True, text=True, timeout=600)
        after = ram_gb()
        load_cost = max(0.0, before - after)
        ok = (q.returncode == 0 and "ok" in (q.stdout or "").lower())
        got.append({"model": model, "role": role, "served": ok,
                    "load_cost_gb": round(load_cost, 2),
                    "answer": (q.stdout or "")[:40]})
        print(f"[model-sweep] {model}: served={ok} the RAM-delta="
              f"{load_cost:.2f}GB (the auto-unload: keep_alive=0's next)")
        subprocess.run([OLLAMA, "stop", model.split(":")[0], "--keep", "0"],
                       capture_output=True, timeout=60)
        time.sleep(10)
    with open(os.path.join(ROOT, "Config", "model_sweep.json"), "w",
              encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "verdict": "PASS" if got else "HONEST-SKIP",
                   "models": got,
                   "law": "the disk-pull = free; the LOAD = RAM-gated + "
                          "verified + auto-unloaded; never 2 loads; $0.00"},
                  f, ensure_ascii=False, indent=1)
    open(os.path.join(ROOT, "Config", "AscentLedger.jsonl"), "a",
         encoding="utf-8").write(json.dumps({
             "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "upward",
             "what": "the model-sweep (the hybrid-expansion)",
             "served": [g["model"] for g in got if g["served"]]}) + "\n")


if __name__ == "__main__":
    run()