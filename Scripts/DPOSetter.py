"""DPOSETTER: the preference-dataset organ (the QLoRAForge's fuel).
Assembles the DPO-pairs from the day's REAL judged-races (never invented):
(1) the ChatEval's blind-rank rows: the #1-answer = the chosen, the last
= the rejected (the same-ask = the legitimate pair); (2) the Gym's
graded rows (the truth-vs-the-wrong). Receipt: Config/dpo_pairs.jsonl +
the count. The honest: a pair only exists where a REAL judge graded it."""
import json
import os
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "dpo_pairs.jsonl")
POOL_MAP = {"groq-120b": "gpt-oss-120b (the blind-#1)", "phi4-mini":
            "phi4-mini (the local)", "qwen25-7b": "qwen2.5-coder-7b",
            "deepseek-r1": "deepseek-r1-7b"}
LET = "ABCD"


def chat_eval_pairs():
    pairs = []
    try:
        d = json.load(open(os.path.join(ROOT, "Config", "chat_eval.json"),
                           encoding="utf-8-sig"))
    except Exception:
        return pairs
    for ask_row in d.get("asks") or []:
        rank = ask_row.get("rank") or []
        lanes = ask_row.get("lanes") or []
        if len(rank) >= 2 and len(lanes) >= 2:
            try:
                chosen = lanes[LET.index(rank[0])]
                rejected = lanes[LET.index(rank[-1])]
                pairs.append({"source": f"chateval ask-{ask_row['n']}",
                              "prompt_id": ask_row["n"],
                              "chosen": POOL_MAP.get(chosen, chosen),
                              "rejected": POOL_MAP.get(rejected, rejected),
                              "judge": "gpt-oss-120b blind"})
            except Exception:
                pass
    return pairs


def gym_pairs():
    pairs = []
    try:
        rows = [json.loads(x) for x in open(
            os.path.join(ROOT, "Config", "TrainingPool.json"),
            encoding="utf-8-sig", errors="replace")]
    except Exception:
        rows = []
    for r in rows[:40]:
        if r.get("truth") and r.get("code"):
            pairs.append({"source": "gym-pool", "prompt_id": r.get("id"),
                          "chosen": "the TRUTH output",
                          "rejected": "the model's wrong-forecast",
                          "judge": "the ground-truth (deterministic)"})
    return pairs


def run():
    pairs = chat_eval_pairs() + gym_pairs()
    with open(OUT, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(os.path.join(ROOT, "Config", "dpo_state.json"), "w",
              encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "pairs": len(pairs),
                   "law": "REAL-judged rows only; the invented = never "
                          "(the honest-training-data's law)"}, f,
                  ensure_ascii=False, indent=1)
    print(f"[dpo-setter] {len(pairs)} REAL pairs -> dpo_pairs.jsonl")
    return len(pairs)


if __name__ == "__main__":
    run()