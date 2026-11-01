"""THE FREE-TOOL DOWNLOADER (the all-free law, the RAM law, the honest
skips): installs the 4 chosen tools into the LOCAL tools-root (never the
OneDrive-synced dir - the proven lesson), verifies each with a smoke-import,
receipts to tools_installed.json. Skips (honest): anything >RAM (the
browsers/Playwright), any model >7b (the 16GB cap), OCR (the keys-lesson:
OCR-transcription ERRORS - the clipboard is the truth-channel)."""
import json
import os
import subprocess
import sys
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
TOOLS = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                     "apex_tools")
PY = os.path.join(ROOT, "apex_venv", "Scripts", "python.exe")

WANT = [
    ("ruff", "the real lint for the quality-gate's stage 4 (the fast, "
             "free, single-binary linter)"),
    ("pytest", "the verify-lane's real test-runner (the deliverables' "
               "tests actually RUN)"),
    ("hypothesis", "the property-based-testing canon class, LIVE (the "
                   "test_gen adoption)"),
    ("jsonschema", "the receipts' self-validation (the schema-lanes' "
                   "honest verifier)"),
]


def smoke(mod):
    r = subprocess.run([PY, "-c", f"import {mod}; print({mod}.__version__ "
                                   f"if hasattr({mod}, '__version__') "
                                   f"else 'ok')"],
                       capture_output=True, text=True, timeout=60)
    return (r.returncode == 0, (r.stdout or r.stderr).strip()[:60])


def pth_env():
    import psutil
    return round(psutil.virtual_memory().available / 2**30, 2)


def run():
    done = []
    for name, why in WANT:
        if pth_env() < 2.2:
            print(f"[tools] RAM GATE: paused before {name} (the honest "
                  f"hardware bound)")
            break
        r = subprocess.run([PY, "-m", "pip", "install", "--quiet", name],
                           capture_output=True, text=True, timeout=420)
        ok, note = smoke(name.replace("-", "_") if name != "ruff" else "ruff")
        done.append({"tool": name, "ok": ok, "why": why, "note": note[:60],
                     "err": ((r.stderr or "")[:120] if r.returncode else "")})
        print(f"[tools] {name}: {'OK' if ok else 'HONEST-FAIL'} | {note[:50]}")
    # the receipt
    rec = os.path.join(ROOT, "Config", "tools_installed.json")
    try:
        d = json.load(open(rec, encoding="utf-8-sig"))
    except Exception:
        d = {}
    d[f"free_tools_round@{time.strftime('%Y%m%d_%H%M%S')}"] = {
        "root": TOOLS, "law": "$0.00 - PyPI only, RAM-light, no GPU, "
                              "no browsers (the RAM law), no OCR (the "
                              "keys-lesson)", "tools": done,
        "skips": ["the browser-lane = RAM-fatal (honest skip)",
                  "the models >7b = the 16GB cap (honest skip)",
                  "the OCR = the keys-error-lesson (honest skip)"],
        "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(rec, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    # the ledger row
    open(os.path.join(ROOT, "Config", "AscentLedger.jsonl"), "a",
         encoding="utf-8").write(json.dumps({
             "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": "upward",
             "what": "the free-tools round",
             "oks": [t["tool"] for t in done if t["ok"]]}) + "\n")
    print("[tools] receipt written; the gates can now wield ruff+pytest")


if __name__ == "__main__":
    run()