"""THE PRIVACY SCRUB (2026-11-04, the public-repo emergency fix).

The founder's PayPal receiving address was found hardcoded in SIX
git-tracked files (public at github.com/seahawk2986-hue/apex-ghost-family).
This scrub:
  1. appends PAYOUT_DEST=<founder's address> to .env (gitignored by design,
     verified) so every consumer reads the destination from the env-file;
  2. replaces every literal occurrence in repo content with an .env
     reference (redaction receipt stamped);
  3. verifies: ZERO occurrences remain outside .env / local backups.

HONEST CAVEAT (printed, not hidden): git HISTORY still contains the old
literals - history rewrite (filter-repo + force-push) or receiving-address
rotation stays a founder-only action (the family never rewrites history
silently).

Sources/practice: the family's own law "keys + personal endpoints live in
.env, never in repo content" (FOUNDER_NOW.md #4) + GitHub's secret-scanning
guidance (docs.github.com/code-security/secret-scanning) - the doc'd
reason tracked files with personal endpoints need scrubbing ONCE and
history review AFTER.
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
ENV_PATH = os.path.join(ROOT, ".env")
EMAIL = "paypal:ENV:PAYOUT_DEST (redacted from repo content 2026-11-04)"          # the founder's own receiving address
REPL = "paypal:ENV:PAYOUT_DEST (redacted from repo content 2026-11-04)"
SKIP = ("venv", "Lib", "Lib", "__pycache__", ".ruff_cache", "Backup_Archive",
        "backup_pre-", ".git", ".opencode", ".github", "site-packages",
        "repos", "node_modules", "tool_events", "checkpoints", "scratch")

def _skip(d):
    d = d.lower()
    return any(s.lower() in d for s in SKIP)

# --- 1. .env carries the real destination (append-only, never printed) -------
have_env = False
if os.path.isfile(ENV_PATH):
    with open(ENV_PATH, encoding="utf-8-sig") as f:
        have_env = any(ln.strip().startswith("PAYOUT_DEST=") for ln in f)
if not have_env:
    dest = None
    for cand in (os.path.join(ROOT, "Scripts", "PayoutDoor.py"),
                 os.path.join(ROOT, "Scripts", "CryptoEconomy.py"),
                 os.path.join(ROOT, "Scripts", "JobPortfolio.py"),
                 os.path.join(AD, "service_catalog.json")):
        if os.path.isfile(cand):
            try:
                with open(cand, encoding="utf-8-sig") as f:
                    t = f.read()
                i = t.find(EMAIL)
                if i != -1:
                    dest = EMAIL       # recovered from the existing repo content
                    break
            except Exception:
                continue
    with open(ENV_PATH, "a", encoding="utf-8") as f:
        f.write("\nPAYOUT_DEST=" + (dest or "paypal:SET-ME-BY-THE-FOUNDER") + "\n")

# --- 2. scrub every literal out of repo content ------------------------------
scrubbed = {}
for base in (ROOT, AD):
    for dp, dns, fns in os.walk(base):
        dns[:] = [d for d in dns if not _skip(d)]
        for fn in fns:
            if fn == os.path.basename(ENV_PATH) or not fn.lower().endswith(
                    (".py", ".json", ".jsonl", ".md", ".html", ".txt", ".ps1")):
                continue
            p = os.path.join(dp, fn)
            try:
                if os.path.getsize(p) > 1_500_000:
                    continue
                with open(p, encoding="utf-8-sig") as f:
                    t = f.read()
            except Exception:
                continue
            if EMAIL in t:
                nt = t.replace("paypal:" + EMAIL, REPL).replace(EMAIL, REPL)
                if nt != t:
                    with open(p, "w", encoding="utf-8", newline="") as f:
                        f.write(nt)
                    scrubbed[os.path.relpath(p, base) +
                             ("" if base == ROOT else " (adapter)")] = True

# --- 3. verify: zero literals left outside .env + local backups ---------------
left = []
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if not _skip(d)]
    for fn in fns:
        p = os.path.join(dp, fn)
        if p == ENV_PATH or fn.endswith((".db", ".png", ".zip", ".npy", ".pyc",
                                         ".exe", ".pyd", ".dll", ".pth", ".log")):
            continue
        try:
            if os.path.getsize(p) > 1_500_000:
                continue
            if EMAIL in open(p, encoding="utf-8-sig", errors="ignore").read():
                left.append(p)
        except Exception:
            continue
for dp, dns, fns in os.walk(AD):
    dns[:] = [d for d in dns if not _skip(d)]
    for fn in fns:
        p = os.path.join(dp, fn)
        if fn.endswith((".db", ".png", ".zip", ".npy", ".pyc", ".exe", ".pyd",
                        ".dll", ".pth", ".log")):
            continue
        try:
            if os.path.getsize(p) > 1_500_000:
                continue
            if EMAIL in open(p, encoding="utf-8-sig", errors="ignore").read():
                left.append(p + " (adapter)")
        except Exception:
            continue

with open(os.path.join(ROOT, "Logs", "privacy_scrub_receipt.jsonl"), "a",
          encoding="utf-8") as f:
    import time
    f.write('{"ts": "%s", "scrubbed_files": %d, "remaining": %d, '
            '"history_note": "git history retains old literals; founder-only rewrite"}\n'
            % (time.strftime("%Y-%m-%d %H:%M:%S"), len(scrubbed), len(left)))

print("[scrubbed]: %d file(s)" % len(scrubbed))
for k in scrubbed:
    print("   ", k)
print("[verified]: remaining occurrences OUTSIDE .env/Backups:", len(left))
for p in left:
    print("   LEFT:", p)
print("[receipt]: Logs/privacy_scrub_receipt.jsonl")