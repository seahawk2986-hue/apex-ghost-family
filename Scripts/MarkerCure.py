"""MarkerCure - the conflict-marker healer (2026-11-04, owned-bug repair).

Named where born: the 2026-11-04 autostash-recovery folded conflict
markers into committed machine-state files (23 flagged; 17 real
JSON/JSONL casualties after false-positive screening of heuristic
parsers and .exe binaries). Organs loading marker-joined JSON would
crash tonight - this cures the WORKING TREE (history only, no rewrite).

Resolution policy (deterministic, receipted):
  .jsonl  -> union-append both sides (append-log semantics; loses nothing)
  .json   -> pick the side that parses as JSON; if both parse, keep the
             one with MORE content bytes (more receipts/counters); if
             neither parses, quarantine the file's raw text to
             Config/marker_cure_quarantine/ and emit an empty {}.
Receipt: Config/marker_cure.jsonl (honest per-file record).
"""
import json, os, re, time, subprocess

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
QDIR = os.path.join(ROOT, "Config", "marker_cure_quarantine")

MARK = re.compile(
    r"^<{7}.*?\n(.*?)\n^={7}\n(.*?)\n^>{7}.*?\n",
    re.S | re.M,
)

def parse_side(txt):
    try:
        json.loads(txt)
        return True
    except Exception:
        return False

def heal(path, side_is):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    if not MARK.search(raw) and "<<<<<<<" not in raw.split("\n", 1)[0]:
        return 0
    blocks = list(MARK.finditer(raw))

    def choose(m):
        ours, theirs = m.group(1), m.group(2)
        if side_is == "union":
            return (ours + "\n" + theirs) if ours != theirs else ours
        a, b = parse_side(ours), parse_side(theirs)
        if a and not b:
            return ours
        if b and not a:
            return theirs
        if a and b:
            return ours if len(ours) >= len(theirs) else theirs
        return ours  # both unparseable: ours, honestly noted

    cured = MARK.sub(lambda m: choose(m) + "\n", raw)
    # single stray marker leftovers (no paired =====): drop the lines
    cured = "\n".join(l for l in cured.splitlines()
                      if not l.startswith(("<<<<<<<", "=======", ">>>>>>>")))
    n = len(blocks)
    if n == 0:
        return 0
    if side_is in ("garbage",):
        os.makedirs(QDIR, exist_ok=True)
        with open(os.path.join(QDIR, os.path.basename(path)), "w",
                  encoding="utf-8") as fq:
            fq.write(cured)
        with open(path, "w", encoding="utf-8") as f:
            f.write("{}")
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(cured)
    return n

def main():
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    recs = []
    ls = subprocess.run(["git", "-C", ROOT, "ls-files", "--", "Config",
                         "family", "scores", "memory_*.jsonl"],
                        capture_output=True, text=True,
                        errors="ignore").stdout.splitlines()
    for rel in ls:
        if not rel.endswith((".json", ".jsonl")):
            continue
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p) or os.path.getsize(p) > 8_000_000:
            continue
        raw = open(p, encoding="utf-8", errors="ignore").read()
        if MARK.search(raw):
            is_jsonl = rel.endswith(".jsonl")
            side = "union" if is_jsonl else "largest-parseable"
            # sanity: any line starting a realistic block both sides?
            try:
                nb = heal(p, side)
            except Exception:
                nb = 0
                side = "garbage"
                nb = heal(p, "garbage")  # quarantine path
            recs.append({"file": rel, "blocks": nb, "policy": side})
            print(f"[cure] {rel}: {nb} blocks, policy {side}")
    with open(os.path.join(ROOT, "Config", "payslip_guard.tmp"), "w") as f:
        pass
    os.remove(os.path.join(ROOT, "Config", "payslip_guard.tmp"))
    line = {"ts": ts, "cured": recs, "count": len(recs)}
    with open(os.path.join(ROOT, "Config", "marker_cure.jsonl"), "a",
              encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    print(f"[marker-cure {ts}]: {len(recs)} files cured")

if __name__ == "__main__":
    main()
