"""LocalMindGym - THE SERVING-BRAIN REPORT (2026-11-04, GI round).

THE MEASURED GAP: the family's gyms graded REMOTE teacher brains, the
Blind Court grades the fleet answerer - but the brain a customer actually
MEETS when the 120b lanes are rate-walled (the local floor, phi4-mini via
Ollama) was NEVER graded on anything. Its quality was assumed. When
reasoning_calibration measures 0.34 and the founder's standing directive
names reasoning the weakest dimension, "assume the floor is fine" = the
wrong kind of faith.

THE ORGAN (novel, honest, local):
  - re-grades the SEALED court pockets (the same 27, zero contamination)
    against the LOCAL serving brain via Ollama's own API;
  - the SHARED AnswerNorm ruler (the gym's and the court's grading agree);
  - nightly + bounded (~3 min, one model in memory at a time, RAM-gated:
    skips honestly below 2.5 GB free);
  - writes Config/local_mind.json + one episodic row; /receipts renders it.
The strength: when Apex falls back to the floor, it now KNOWS what that
fallback's real capability is - and says the number out loud.
$0; stdlib only."""
import io
import json
import os
import sys
import time
import urllib.request

if getattr(sys.stdout, "apex_wrapped", False) is False:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.stdout.apex_wrapped = True

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
HOLDOUT = os.path.join(REPO, "Config", "court_holdout.json")
OUT = os.path.join(REPO, "Config", "local_mind.json")
sys.path.insert(0, os.path.join(REPO, "Scripts"))
import AnswerNorm  # noqa: E402


def _free_gb():
    try:
        import psutil
        return psutil.virtual_memory().available / 2 ** 30
    except Exception:
        return 0.0


def _ollama(model, prompt, max_tokens=128):
    body = json.dumps({"model": model, "stream": False,
                       "messages": [{"role": "user", "content": prompt}],
                       "keep_alive": "5m",
                       "options": {"num_predict": max_tokens,
                                   "temperature": 0}}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/chat", data=body,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.load(r)
    return (d.get("message") or {}).get("content", "") or ""


def grade_brain(model="phi4-mini:latest", prompt_prefix=""):
    if _free_gb() < 2.5:
        print(f"[local-gym]: RAM free {_free_gb():.2f} GB < 2.5 - the honest "
              "skip (the floor cannot even be resident)")
        return None
    try:
        hold = json.load(open(HOLDOUT, encoding="utf-8-sig"))
    except Exception:
        print("[local-gym]: no sealed pocket - run RealityCourt.seal first")
        return None
    sys.path.insert(0, os.path.join(REPO, "Scripts"))
    import RealityCourt as RC
    hits = n = 0
    per_fam = {}
    for p in (hold.get("pockets") or []):
        raw = ""
        try:
            raw = _ollama(model, prompt_prefix + p["question"][:600], 96)
        except Exception:
            continue
        if not raw:
            continue
        hit = RC._grade(p["question"], p["truth"], raw)
        f0 = p.get("family", "?")
        pf = per_fam.setdefault(f0, [0, 0])
        pf[1] += 1
        pf[0] += 1 if hit else 0
        hits += hit
        n += 1
    if not n:
        print("[local-gym]: the floor refused everything (the honest zero)")
        return None
    doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "brain": model,
           "acc": round(100.0 * hits / n, 1), "n": n,
           "per_family": {k: f"{h}/{t}" for k, (h, t) in per_fam.items()},
           "law": "the SAME sealed pocket + the SAME ruler as the court"}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    os.replace(tmp, OUT)
    try:
        with open(os.path.join(REPO, "memory_episodic.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps({"id": os.urandom(6).hex(), "ts": doc["ts"],
                                "kind": "local_mind",
                                "text": f"LOCAL-MIND: {model} scored "
                                f"{doc['acc']}% on the sealed pocket (n={n})",
                                "meta": {}, "imp": 0.8},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass
    print(f"[local-gym]: the SERVING floor {model} = {doc['acc']}% on the "
          f"sealed holdout (n={n}) | per-family: {doc['per_family']}")
    return doc


if __name__ == "__main__":
    grade_brain()