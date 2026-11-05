"""SecretSentinel - the spill dog (2026-11-04, security-repair organ).

LAW-COMPLIANT: stdlib only; nothing deleted; nothing printed that could be
a secret itself (only file, line number, and the PATTERN CLASS that matched).

Circuit:
  (a) LIVE-TREE: scan every tracked text file for secret-shaped values;
      .env itself is exempt (its whole job is holding them, and it is
      gitignored - already verified by the fleet's audits).
  (b) SPILL-ZONE: inventory every Apex-related .zip in Downloads WITHOUT
      extraction; flag any .env / *.key / *token* * inside. One wrong
      'Compress-Apex' click = the founder's keys leaving the machine.
  (c) RECEIPT: append Config/secret_sentinel.jsonl (atomic-ish append),
      console line is honest whether clean or not.

Exit code 2 = a live-tree spill was found (usable by a future gate).
"""
import json, os, re, sys, time, zipfile, glob

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
DL = r"C:\Users\seaha\Downloads"
RECEIPT = os.path.join(ROOT, "Config", "secret_sentinel.jsonl")

# pattern classes -> (name, regex). Values are NEVER printed.
PATTERNS = [
    ("groq-key",      r"gsk_[A-Za-z0-9]{20,}"),
    ("openrouter-key",r"sk-or-v1-[A-Za-z0-9]{20,}"),
    ("gemini-key",    r"AIza[A-Za-z0-9_-]{30,}"),
    ("nim-key",       r"nvapi-[A-Za-z0-9_-]{20,}"),
    ("github-pat",    r"gh[pousr]_[A-Za-z0-9]{30,}"),
    ("hf-token",      r"hf_[A-Za-z0-9]{30,}"),
    ("cerebras-key",  r"csk-[A-Za-z0-9]{30,}"),
    ("bearer hdr",    r"[Bb]earer\s+[A-Za-z0-9_\-=.]{28,}"),
    ("paypal-addr",   r"(paypal\.me|money\.paypal\.com)/[A-Za-z0-9_.\-]{3,}"),
    ("ffl-env-line",  r"^\s*(PAYOUT_DEST|OPENROUTER_API_KEY|GROQ_API_KEY|"
                      r"NVIDIA_API_KEY|GEMINI_API_KEY|HF_TOKEN)\s*="),
]
COMPILED = [(n, re.compile(p)) for n, p in PATTERNS]
TEXT_EXT = (".py", ".json", ".md", ".yml", ".yaml", ".txt", ".ini", ".cfg",
            ".cmd", ".bat", ".ps1", ".html", ".js", ".ts", ".csv", "")
SKIP_DIRS = {".git", "training_venv", "venv", "node_modules", "Attic",
             "__pycache__", ".opencode", "apex_venv"}

def live_tree_scan():
    hits = []
    for dirp, subds, files in os.walk(ROOT):
        subds[:] = [d for d in subds if d not in SKIP_DIRS]
        for fn in files:
            if fn == ".env" or fn.endswith(".env"):   # the holder is legal
                continue
            if any(fn.endswith(e) for e in (".jsonl",)) and fn.endswith("sentinel.jsonl"):
                continue
            p = os.path.join(dirp, fn)
            if fn == ".env.example" or fn.endswith(".env.example"):
                continue   # template: its env-lines are placeholders, not keys
            if os.path.getsize(p) > 4_000_000:
                continue
            if not (fn.endswith(TEXT_EXT) or fn == ".gitignore"):
                continue   # text-only scan; binaries (weights, zips) are
                           # not spill-carriers of KEY VALUES we can match
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for i, ln in enumerate(f, 1):
                        for name, cx in COMPILED:
                            if cx.search(ln):
                                hits.append((p.replace(ROOT, "."), i, name))
            except OSError:
                continue
    return hits

def spill_zone_scan():
    """List zip entries (no extraction). Return (zip, [risky entries])."""
    out = []
    zips = [z for z in glob.glob(os.path.join(DL, "*.zip"))
            if "apex" in os.path.basename(z).lower()]
    for z in zips:
        try:
            risky = [n for n in zipfile.ZipFile(z).namelist()
                     if os.path.basename(n).lower() in (".env",) or
                     os.path.basename(n).lower().endswith(".key") or
                     "token" in os.path.basename(n).lower()]
        except Exception as ex:
            risky = [f"<unreadable: {type(ex).__name__}>"]
        if risky:
            out.append((os.path.basename(z), risky))
    return zips, out

def main():
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    tree_hits = live_tree_scan()
    zips, spill = spill_zone_scan()
    rec = {"ts": ts, "tree_scanned": True, "tree_spills": len(tree_hits),
           "zips_inventoried": len(zips), "zips_with_secrets": len(spill),
           "detail": [{"where": "tree", "file": f, "line": i, "class": n}
                      for f, i, n in tree_hits][:50] +
                      [{"where": "zip", "zip": z, "entries": [e if isinstance(e, str) else e
                                                              for e in es][:20]}
                       for z, es in spill][:20]}
    # receipts: never include a matched VALUE; the classes above are classes
    with open(RECEIPT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    if tree_hits:
        for f_, i, n in tree_hits[:15]:
            print(f"[TREE-SPILL] {f_}:{i} -> {n}")
    if spill:
        for z, es in spill:
            print(f"[ZIP-SPILL] {z}: {len(es)} risky entries "
                  f"(namelist only, nothing extracted)")
    if not tree_hits and not spill:
        print(f"[sentinel {ts}]: clean - tree 0 spills, {len(zips)} apex zips "
              f"inventoried, none carry secrets (honest)")
    sys.exit(2 if tree_hits else 0)

if __name__ == "__main__":
    main()
