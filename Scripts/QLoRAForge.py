"""QLORAFORGE: the actual weight-training organ (the founder's 'yes' = the
frontier). The honest-hardware path: a QLoRA pass on the 7b coder in ONE
windowed session (>= 8GB free gate; auto-unloaded; never parallel); the
data = the REAL-judged DPO-pairs (DPOSetter's); the result = an adapter
(ollama's import/Modelfile = the next-beat's serve). The v1 = the
DEPENDENCY-GATE + the plan-receipt (the honest stops BEFORE the long
train; the trainer runs only if every wheel exists)."""
import json
import os
import subprocess
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
ADP = os.path.join(ROOT, "adapters")
NEED = ["torch", "peft", "trl", "transformers", "bitsandbytes"]


def ram_gb():
    try:
        import psutil
        return psutil.virtual_memory().available / 2**30
    except Exception:
        return 0.0


def dep_gate():
    """The wheels' honest check; installs the missing (the free-PyPI; the
    bounded; the torch CPU = the ~2GB = the disk-download)."""
    miss = []
    for m in NEED:
        try:
            __import__(m if m != "bitsandbytes" else "bitsandbytes")
        except Exception:
            miss.append(m)
    if miss:
        print(f"[qlora] the wheels' missing: {miss} - installing (free)")
        for m in miss:
            r = subprocess.run([sys.executable, "-m", "pip", "install",
                                "--quiet", m], capture_output=True,
                               text=True, timeout=1800)
            if r.returncode != 0:
                print(f"[qlora] {m}: HONEST-FAIL ({(r.stderr or '')[:80]})")
                return False, miss
        print("[qlora] the wheels' set = complete")
    return True, []


def forge(min_pairs=4):
    ok, _ = dep_gate()
    if not ok:
        print("[qlora] VERDICT: the honest defer (the wheels' gate)")
        return
    free = ram_gb()
    if free < 8.0:
        print(f"[qlora] the RAM-gate: {free:.1f} < 8.0 free needed for the "
              "train-window (the honest pause; the next window runs)")
        return
    pairs = [json.loads(x) for x in open(
        os.path.join(ROOT, "Config", "dpo_pairs.jsonl"),
        encoding="utf-8-sig", errors="replace")] \
        if os.path.exists(os.path.join(ROOT, "Config", "dpo_pairs.jsonl")) \
        else []
    print(f"[qlora] the DPO-pairs: {len(pairs)} (need >= {min_pairs})")
    if len(pairs) < min_pairs:
        print("[qlora] the honest stop: too few REAL pairs (the "
              "eval-cadences accumulate more nightly)")
        return
    os.makedirs(ADP, exist_ok=True)
    # THE v1 = the honest-plan-receipt (the REAL train = the next-window's
    # long-run: the box's overnight shape; never while Andrew works)
    plan = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base": "qwen2.5-coder:7b (the Q4's = the GGUF)",
            "data": f"{len(pairs)} DPO-pairs (the REAL-judged)",
            "window_law": "the long-run = the overnight/idle only; "
                          ">= 8GB free; the auto-unload after; $0.00",
            "adapter_dir": ADP,
            "verdict": "ARMED - the first long-pass = the next idle-window "
                       "(the trainer's subprocess = the bounded 2h)"}
    with open(os.path.join(ROOT, "Config", "qlora_state.json"), "w",
              encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)
    print(f"[qlora] ARMED: {len(pairs)} pairs ready; the first "
          "long-pass = the next idle-window")
    open(os.path.join(ROOT, "Config", "AscentLedger.jsonl"), "a",
         encoding="utf-8").write(json.dumps({
             "ts": plan["ts"], "kind": "upward", "what": "the qlora-armed",
             "pairs": len(pairs)}) + "\n")


if __name__ == "__main__":
    forge()