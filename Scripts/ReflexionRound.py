"""REFLEXION ROUND (Part VIII W2, verified 2303.11366): verbal reinforcement
after weak rounds - one bounded brain call reflecting on the round ledger,
stored in episodic memory, merged into the next brief. Reflexion: 91%
HumanEval pass@1 BEATING GPT-4 with NO weight updates - reflection as the
cheapest learning channel. Hardware: ONE call, 300 tokens, RAM-gated,
fail-closed to honest-zero."""
import json
import os
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
OUT = os.path.join(ROOT, "Config", "reflexion.jsonl")
BRIEF = os.path.join(AD, "swarm_state.json")


def ram_free():
    try:
        import psutil
        return psutil.virtual_memory().available / 2 ** 30
    except Exception:
        return 0.0


def loaded_model():
    """The actually-loaded chat brain, TWO-server aware (the migration drift
    fix): LM Studio (api/v0 state=loaded, embeddings excluded) first, then
    Ollama's resident models (api/ps) - else None, honest. Never LOADS."""
    try:
        for m in json.load(urllib.request.urlopen(
                "http://127.0.0.1:1234/api/v0/models", timeout=4)).get("data", []):
            if m.get("state") == "loaded" and "text-embedding" not in (m.get("id") or ""):
                return m["id"]
    except Exception:
        pass
    try:
        ps = json.load(urllib.request.urlopen(
            "http://127.0.0.1:11434/api/ps", timeout=4)).get("models", [])
        if ps:
            return ps[0].get("name")
    except Exception:
        pass
    return None


def brain(prompt, model, max_tokens=300):
    req = urllib.request.Request(
        "http://127.0.0.1:1234/v1/chat/completions",
        data=json.dumps({"model": model, "messages":
                         [{"role": "user", "content": prompt}],
                         "temperature": 0.4, "stream": False,
                         "max_tokens": max_tokens}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        txt = ((((json.load(r).get("choices")) or [{}])[0].get("message", {})
                or {}).get("content", "")) or ""
    if "</think>" in txt and "</think>" in txt:
        return txt.split("</think>")[-1].strip()
    return txt.strip()


def run():
    if ram_free() < 2.2:
        print("[reflexion] RAM below 2.2GB - skipped honestly")
        return None
    try:
        asc = [json.loads(x) for x in open(
            os.path.join(ROOT, "Config", "AscentLedger.jsonl"),
            encoding="utf-8-sig") if x.strip()][-6:]
    except Exception:
        asc = []
    try:
        hb = json.load(open(os.path.join(AD, "ghost_heartbeat.json"),
                            encoding="utf-8-sig"))
    except Exception:
        hb = {}
    facts = json.dumps({"recent_ledger": asc[-3:], "round_done": hb.get("round_done"),
                        "findings": hb.get("findings")})[:2200]
    model = loaded_model()
    if not model:
        print("[reflexion] no loaded brain - honest skip")
        return None
    print(f"[reflexion] brain: {model} | ledger tail: {len(asc)} rows")
    refl = brain(
        f"You are the Apex ghost family's reflection organ. Here are the last "
        f"round facts: {facts}\n\nReflect in <=120 words: (1) what the facts say "
        f"went weakly, (2) the THREE most concrete adjustments for the next round, "
        f"(3) one sentence of honest encouragement. Facts only, no slogans.", model)
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "model": model,
           "reflection": refl, "facts_digest": facts[:300]}
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    # W2 memory merge: the latest reflection rides the state for the next brief
    try:
        st = json.load(open(BRIEF, encoding="utf-8-sig"))
    except Exception:
        st = {}
    st["last_reflexion"] = {"ts": row["ts"], "text": (refl or "")[:500]}
    with open(BRIEF + ".tmp", "w", encoding="utf-8") as f:
        json.dump(st, f, indent=1)
    os.replace(BRIEF + ".tmp", BRIEF)
    print("[reflexion] stored -> Config/reflexion.jsonl + state.last_reflexion "
          "(the next brief carries it)")
    print("[reflexion] REFLECTION:", (refl or "(empty - honest)")[:400])
    return refl


if __name__ == "__main__":
    run()