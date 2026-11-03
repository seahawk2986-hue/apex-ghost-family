"""THE LEDGER TRIM (2026-11-04) - no unbounded file in the honest family.

THE WEAKNESS IT KILLS: two append-only ledgers grew unbounded
(swarm_findings.jsonl 7.9MB; comb_passes.jsonl 52MB - 13x OVER ITS OWN
4MB CAP because DeepComb's rotator only runs when DeepComb itself runs).
The trim: every nightly dream beat, any ledger above its cap is archived
(Logs/, kept byte-exact) and rewritten with the newest `cap` rows.

Bounds: the archive lands in Logs/ (gitignored); the rewrite keeps the
newest rows so the readers (VetLine, _swarm_roi, FeedGrain) see no gap.
Runs after ApexDream's consolidation; never blocks the dream (guarded)."""
import io
import os
import shutil
import sys
import time

if getattr(sys.stdout, "apex_wrapped", False) is False:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stdout.apex_wrapped = True   # one process, one wrapper (double-wrap
                                     # = the GC closes the shared buffer)

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
LOGS = os.path.join(REPO, "Logs")

TARGETS = [
    (os.path.join(AD, "swarm_findings.jsonl"), 4000),
    (os.path.join(REPO, "Config", "comb_passes.jsonl"), 4000),
]


def trim():
    out = []
    for path, cap in TARGETS:
        try:
            if not os.path.isfile(path):
                continue
            size = os.path.getsize(path)
            with open(path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            # cap by ROWS and by SIZE (the comb ledger = few ~1MB rows: row-cap
            # alone would never trip on a 52MB/38-row file)
            if len(lines) <= cap and size <= 6_000_000:
                out.append(f"{os.path.basename(path)}: {len(lines)} rows "
                           f"({size / 2 ** 20:.1f}MB, under caps - untouched)")
                continue
            stamp = time.strftime("%Y%m%d_%H%M%S")
            arch = os.path.join(LOGS, f"{os.path.basename(path)}.{stamp}.old")
            tmp = path + ".tmp"
            # keep the NEWEST rows bound by BOTH counts: <= cap rows AND
            # <= 6MB of raw bytes (the comb ledger's ~1MB rows need it)
            kept, cum = [], 0
            for ln in reversed(lines):
                cum += len(ln) + 1
                if cum > 6_000_000 or len(kept) >= cap:
                    break
                kept.append(ln)
            kept.reverse()
            with open(tmp, "w", encoding="utf-8") as f:
                f.writelines(kept)
            shutil.move(path, arch)
            os.replace(tmp, path)
            out.append(f"{os.path.basename(path)}: {len(lines)} rows "
                       f"({size / 2 ** 20:.1f}MB) -> kept newest {len(kept)} "
                       f"({cum / 2 ** 20:.1f}MB), archived {arch}")
        except Exception as e:
            out.append(f"{os.path.basename(path)}: SKIP ({type(e).__name__}: {str(e)[:60]})")
    for ln in out:
        print("[trim]:", ln)
    try:
        with open(os.path.join(REPO, "memory_episodic.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps({"id": os.urandom(6).hex(),
                                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "kind": "trim", "text": "; ".join(out)[:400],
                                "meta": {}, "imp": 0.5}, ensure_ascii=False) + "\n")
    except Exception:
        pass


import json  # noqa: E402 (kept last so the module never half-loads earlier deps)

if __name__ == "__main__":
    trim()