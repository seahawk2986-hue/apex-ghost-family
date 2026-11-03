"""THE CANONICAL COUNTS - the honesty spine (2026-11-04).

The weakness: three public surfaces said three different skill counts
(245 / 404 / 435) - for a brand whose product IS "every number checkable".
The strength: ONE counter computes every public number from the canonical
stores, stamps its receipt, and re-stamps the surfaces so they can only
agree. Any later divergence = a print-first drift alarm.

Canonical definitions (each number states its own definition, print-first):
  skills_library  = entries in Config/SkillLibrary.json  (SHA-tracked, MIT-sourced)
  skills_certified= entries in Config/SkillRegistry.json (the harder certifier)
  papers_canon    = distinct listing-rows deduped by title/url across the canon
                    files (papers_2026_*.jsonl + GIPapers200 + MemoryCanon100
                    + VoicePapers50 + canon_pages.jsonl)

Runs: manual + wired into ApexDream nightly (surfaces can't drift again).
$0, stdlib-only, sub-second (16GB/i5 envelope, no inference).
Source: the family's law "every number checkable against the repo files"
(README) + the honesty print-first law (family_seed_packet.rules).
"""
import glob
import io
import json
import os
import re
import sys
import time

if hasattr(sys.stdout, "reconfigure") and not getattr(sys.stdout, "_apex_reconfigured", False):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout._apex_reconfigured = True   # reconfigure the EXISTING wrapper
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr._apex_reconfigured = True   # NEVER replace sys.stdout: the GC
                                           # closes the original = the shared buffer dies

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
OUT = os.path.join(ROOT, "Config", "canonical_counts.json")


def _dedup_rows(path, acc):
    try:
        with open(path, encoding="utf-8-sig", errors="ignore") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    j = json.loads(ln)
                    key = str(j.get("title") or j.get("url") or j.get("id")
                              or ln[:96]).lower()
                except Exception:
                    key = ln[:96].lower()
                acc.add(key)
    except FileNotFoundError:
        pass


def compute():
    def jload(p):
        try:
            return json.load(open(p, encoding="utf-8-sig"))
        except Exception:
            return None
    lib = jload(os.path.join(ROOT, "Config", "SkillLibrary.json")) or {}
    reg = jload(os.path.join(ROOT, "Config", "SkillRegistry.json")) or {}
    papers = set()
    files = sorted(glob.glob(os.path.join(ROOT, "Config", "papers_2026_*.jsonl"))) \
        + [os.path.join(ROOT, "Config", fn) for fn in
           ("GIPapers200.jsonl", "MemoryCanon100.jsonl", "VoicePapers50.jsonl",
            "canon_pages.jsonl")]
    for path in files:
        _dedup_rows(path, papers)
    shop = jload(os.path.join(ROOT, "Config", "polar_shop.json")) or {}
    return {
        "skills_library": len(lib.get("skills", [])) if isinstance(lib, dict) else 0,
        "skills_certified": len(reg) if isinstance(reg, dict) else 0,
        "papers_canon": len(papers),
        "canon_files": len(files),
        "shop_state": shop.get("state"),
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "definitions": {
            "skills_library": "SHA-tracked MIT-sourced entries (SkillLibrary.json)",
            "skills_certified": "registry-certified skills (SkillRegistry.json)",
            "papers_canon": "distinct listing-rows, deduped by title/url",
        },
    }


def pages(counts):
    """Re-stamp every public surface from the canonical numbers (idempotent).
    Each entry: (path, [(pattern, replacement)]) - replacement may be a
    callable receiving the match (for keeping a prefix)."""
    lib, cert = counts["skills_library"], counts["skills_certified"]
    papers = counts["papers_canon"]
    specs = [
        (os.path.join(ROOT, "README.md"),
         [(r"(\*\*Live stats \(from our public ledgers\):\*\*\s+)\d+",
           lambda m: m.group(1) + str(lib)),
          (r"canon-[\d,]+ papers", f"canon-{papers:,} papers"),
          (r"skills-[\d,]+%20(?:verified|tracked)%20",
           lambda m: f"skills-{lib}%20tracked%20"),
          (r"canon-[\d,]+%20papers",
           lambda m: "canon-" + f"{papers:,}" + "%20papers")],
         "README live-stats + canon badge"),
        (os.path.join(ROOT, "index.html"),
         [(r"<b>[\d,]+</b> verified skills", f"<b>{lib}</b> tracked skills")],
         "index verified-skills stat"),
        (os.path.join(ROOT, "jobs_page.html"),
         [(r"skills: [\d,]+ ver[^,<)\]]*[,<)\]]",
           f"skills: {lib} SHA-tracked (certified: {cert}) ")],
         "root jobs board"),
        (os.path.join(AD, "jobs_page.html"),
         [(r"skills: [\d,]+ ver[^,<)\]]*[,<)\]]",
           f"skills: {lib} SHA-tracked (certified: {cert}) ")],
         "served jobs board"),
    ]
    done = []
    for path, subs, desc in specs:
        try:
            t0 = open(path, encoding="utf-8-sig").read()
        except Exception as e:
            done.append(f"{desc}: SKIP ({str(e)[:40]})")
            continue
        t = t0
        for pat, rep in subs:
            if re.search(pat, t):
                t = re.sub(pat, rep, t, count=1)
        if t != t0:
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8", newline="") as f:
                f.write(t)
            os.replace(tmp, path)
            done.append(f"{desc}: STAMPED from canon")
        else:
            done.append(f"{desc}: already agrees")
    return done


def read():
    """The one access point for other surfaces (/receipts, dashboards)."""
    try:
        return json.load(open(OUT, encoding="utf-8-sig"))
    except Exception:
        return compute()


if __name__ == "__main__":
    c = compute()
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=1)
    os.replace(tmp, OUT)
    print("[canonical]:", json.dumps(
        {k: c[k] for k in ("skills_library", "skills_certified", "papers_canon")}))
    print("[stamped]:")
    for line in pages(c):
        print("   ", line)
    with open(os.path.join(ROOT, "Logs", "canon_counts_receipts.jsonl"), "a",
              encoding="utf-8") as f:
        f.write('{"ts": "%s", "counts": %s}\n' % (c["generated"], json.dumps(
            {k: c[k] for k in ("skills_library", "skills_certified", "papers_canon")})))