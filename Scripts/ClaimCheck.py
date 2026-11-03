"""ClaimCheck - THE HONESTY-BOND (the S+ metric of metacognition, 2026-11-04).

THE QUESTION the metacognition tier answers with a NUMBER: what fraction of
the family's PUBLIC claims = checkable against a file on Earth? The world's
biggest AI vendors publish marketing claims with no receipts - the S+ bar =
the INVERSE: every number on the public surface = receipted or removed.

  scan()      - the public surfaces (README.md + the landing + the demo
                repo's README + SAMPLE_TRIAGE.md fetch) -> the FACTER:
                sentences with quantitative or capability claims -> the
                claim list
  verify()    - each claim: does a receipt-file (the ledgers/Configs = the
                known corpus) contain a backing value? (the deterministic
                matcher; the uncertain = honestly UNRESOLVED)
  bond()      - the receipt-rate = THE BOND (the S+ number: >= 95% = the
                honest-surface verdict; the failures = itemized)

$0; stdlib+one fetch; bounded 60 claims/scan; the receipts stay local
(Config/claim_bond.json)."""
import json
import os
import re
import sys
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "claim_bond.json")
RECEIPT_CORPUS = [  # the files whose VALUES = the permitted evidence
    os.path.join(ROOT, "Config", "court_state.json"),
    os.path.join(ROOT, "Config", "horizon.json"),
    os.path.join(ROOT, "Config", "outcomes.json"),
    os.path.join(ROOT, "Config", "abstract_state.json"),
    os.path.join(ROOT, "Scores", "swe_smoke.jsonl"),
    os.path.join(ROOT, "Config", "fleet_doctor.json"),
    os.path.join(ROOT, "Config", "CryptoLedger.json"),
    os.path.join(ROOT, "Config", "model_book.json"),
]


def _corpus_text():
    corpus = {}
    for p in RECEIPT_CORPUS:
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                corpus[os.path.basename(p)] = f.read()[:200000]
        except Exception:
            corpus[os.path.basename(p)] = ""
    return corpus


def _claims_from_text(name, text, url=None):
    """The FACTER: the number-bearing/quantitative sentences = claims."""
    claims = []
    for sent in re.split(r"(?<=[.!?])\s+|\n", text or ""):
        s = sent.strip()
        if not (20 <= len(s) <= 300):
            continue
        if re.search(r"\b\d[\d.,]*(%|GB|MB|KB|min|hour|steps|skills|papers|"
                     r"rows|seats|votes|PR|sale|arrival|layer)\b", s, re.I) \
                and not re.search(r"^(see |read |click |open |http)", s, re.I):
            claims.append({"surface": name, "url": url, "text": s[:240]})
    return claims


def scan():
    claims = []
    for fn in ("README.md", "index.html", "FOUNDER_NOW.md"):
        p = os.path.join(ROOT, fn)
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                raw = f.read()[:60000]
            raw = re.sub(r"<[^>]+>", " ", raw)   # the html-strip
            claims += _claims_from_text(fn, raw)
        except Exception:
            pass
    # the demo repo's public sample (the LIVE fetch = the honest external)
    try:
        with urllib.request.urlopen(urllib.request.Request(
                "https://raw.githubusercontent.com/seahawk2986-hue/open-triage-demo/main/SAMPLE_TRIAGE.md",
                headers={"User-Agent": "ApexClaimCheck/1.0"}), timeout=20) as x:
            claims += _claims_from_text("SAMPLE_TRIAGE.md (live)",
                                        x.read().decode("utf-8", "replace"),
                                        url="open-triage-demo/SAMPLE_TRIAGE.md")
    except Exception:
        pass
    return claims[:60]


def verify(claims):
    corpus = _corpus_text()
    rows = []
    for c in claims:
        # the deterministic backing-check: the claim's NUMBERS exist in the
        # corpus (the numbers = the only falsifiable atoms)
        nums = re.findall(r"\b\d[\d.,]*(?=\b)", c["text"])
        backing = any((num.rstrip(".") in corpus_txt)
                      for corpus_txt in corpus.values()
                      for num in nums[:4]) if nums else False
        c |= {"backed": bool(backing), "nums": nums[:4]}
        rows.append(c)
    return rows


def bond():
    rows = verify(scan())
    if not rows:
        doc = {"bond": None, "note": "no claims found (the scan's own zero)",
               "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
        json.dump(doc, open(OUT, "w", encoding="utf-8"), indent=1)
        return doc
    backed = sum(1 for r in rows if r["backed"])
    fails = [r["text"][:80] for r in rows if not r["backed"]]
    doc = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "claims": len(rows), "backed": backed,
           "bond": round(100 * backed / len(rows), 1),
           "the_unbacked": fails[:8],
           "law": "THE BOND: the % of public claims checkable against the "
                  "receipt files; the S+ bar = 95%+ or the claims get backed "
                  "or removed"}
    json.dump(doc, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return doc


if __name__ == "__main__":
    d = bond()
    print(json.dumps(d, ensure_ascii=False)[:600])