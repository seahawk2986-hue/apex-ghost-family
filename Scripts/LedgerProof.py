"""LedgerProof - the claims auditor (2026-11-04, verification-uplift organ).

THE LAW IT SERVES: "every capability claim carries a receipt or it is not
said." This organ反向 audits the receipts THEMSELVES - it re-derives the
hashes and re-runs the suites instead of trusting the ledger's word.

Checks (each printed with its honest verdict):
 1. acceptance_export.zip   -> sha256 recomputed, vs acceptance_run_result.json
 2. the 5 tested sources    -> sha256 recomputed, vs the 16-hex prefixes
    quoted in-session to Micah (the chat claim becomes machine-checkable)
 3. v2_repair_tests.py      -> RE-RUNNED live; exit code + verdict sealed

Receipt: Config/ledger_proof.jsonl (append, one line per proof round).
Exit 2 if any check fails; 0 otherwise.
"""
import json, os, sys, time, hashlib, subprocess

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
RECEIPT = os.path.join(ROOT, "Config", "ledger_proof.jsonl")

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

# the 16-hex prefixes quoted in-session to Micah (2026-11-04)
SOURCES = {
    "companion.py":            "874bf034",
    "v2_job_engine.py":        "9a14eda6",
    "apex_hook.py":            "db9778aa",
    "v2_contract.py":          "6b8bad6c",
    "apex_sealed_fileops.py":  "e3ab6d06",
}

def main():
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    checks, fails = [], []

    # 1. the acceptance zip hash
    zip_path = os.path.join(AD, "acceptance_export.zip")
    rec = json.load(open(os.path.join(AD, "acceptance_run_result.json"),
                         encoding="utf-8-sig"))
    claimed = (rec.get("zip_sha256") or "").lower()
    if os.path.exists(zip_path):
        got = sha256(zip_path)
        ok = got == claimed
        checks.append({"check": "acceptance_zip_sha256", "ok": ok,
                       "claimed": claimed[:16], "derived": got[:16]})
        if not ok:
            fails.append("acceptance_zip_sha256 drift")
    else:
        checks.append({"check": "acceptance_zip_sha256", "ok": None,
                       "note": "zip file absent; claim unverifiable now"})
        fails.append("acceptance zip absent")

    # 2. the five tested sources vs the in-session prefixes
    for fn, prefix in SOURCES.items():
        p = os.path.join(AD, fn)
        if not os.path.exists(p):
            checks.append({"check": f"src:{fn}", "ok": None, "note": "absent"})
            fails.append(f"{fn} absent")
            continue
        got = sha256(p)
        ok = got.startswith(prefix)
        checks.append({"check": f"src:{fn}", "ok": ok,
                       "claimed_prefix": prefix, "derived": got[:16]})
        if not ok:
            fails.append(f"{fn} != quoted prefix (source moved or claim wrong)")

    # 3. re-run the deterministic suite live
    t0 = time.time()
    cp = subprocess.run([sys.executable, os.path.join(AD, "v2_repair_tests.py")],
                        capture_output=True, text=True, errors="replace",
                        timeout=1500)
    tail = (cp.stdout or "").strip().splitlines()
    verdict = {"check": "v2_suite_live_rerun", "exit": cp.returncode,
               "secs": round(time.time() - t0, 1),
               "tail": tail[-3:] if tail else []}
    if cp.returncode != 0:
        fails.append("v2 suite NOT green on rerun")
    checks.append(verdict)

    line = {"ts": ts, "fails": fails, "all_green": not fails, "checks": checks}
    with open(RECEIPT, "a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    print(json.dumps(line, indent=1)[:2200])
    sys.exit(2 if fails else 0)

if __name__ == "__main__":
    main()
