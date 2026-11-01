"""COMB-LEDGER TRIM: the 102MB honest-trim (the census = kept; the noise
= dropped; the receipt-value = preserved at KB-size)."""
import json
import os
import time

P = r"Config\comb_passes.jsonl"
before = os.path.getsize(P)
rows = []
for ln in open(P, encoding="utf-8", errors="replace"):
    try:
        rows.append(json.loads(ln))
    except Exception:
        pass
for r in rows:
    if isinstance(r.get("bugs"), list) and len(r["bugs"]) > 30:
        r["bugs"] = r["bugs"][:30] + [
            {"note": f"+{len(r['bugs']) - 30} more (trimmed for size)"}]
census = {}
for r in rows:
    for b in r.get("bugs", []):
        k = (os.path.basename(str(b.get("file", "?"))),
             str(b.get("bug", ""))[:60])
        if not str(b.get("note", "")):
            census[k] = census.get(k, 0) + 1
summary = {
    "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "summary": True,
    "source_passes": len(rows),
    "lesson": "the comb-combed-sites-packages-lesson: the ledger itself "
              "bloated to 102MB (the stray Lib\\ noise) - trimmed, the "
              "comb hardened (see DeepComb.py exclusions)",
    "top_bugs": [{"file": f, "bug": b, "x": c} for (f, b), c in
                 sorted(census.items(), key=lambda kv: -kv[1])[:50]],
}
out = rows[-8:] + [summary]
with open(P, "w", encoding="utf-8") as f:
    f.write("\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n")
after = os.path.getsize(P)
print(f"[trim] {before / 2**20:.1f}MB -> {after / 2**20:.3f}MB "
      f"({len(rows)} passes -> kept last 8 + the 50-bug census-summary)")