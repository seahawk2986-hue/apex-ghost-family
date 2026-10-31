"""Apex security baseline: integrity pinning + secrets-leak scan + backups.

    python SecurityBaseline.py            -> full audit (pins, leaks, backups)
    python SecurityBaseline.py --verify   -> exit 1 on any drift or leak
    python SecurityBaseline.py --respin   -> re-pin after a deliberate code change

Pins sha256 of the agent's critical scripts - silent self-modification (or a
poisoned edit) trips the alarm instead of sliding through. Scans every log the
system writes for cloud-key shapes. Zips Config into rolling backups (last 5).
"""
import hashlib
import json
import os
import re
import sys
import time
import zipfile

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
ADAPTER = r"C:\Users\seaha\Apex-Adapter"
BASELINE = os.path.join(ROOT, "Config", "security_baseline.json")
BACKUP_DIR = os.path.join(ROOT, "Config", "backups")

PINNED = [
    os.path.join(ROOT, "run_apex_evolution.py"),
    os.path.join(ADAPTER, "v2_job_engine.py"),
    os.path.join(ADAPTER, "companion.py"),
    os.path.join(ROOT, "Scripts", "SeekGrowth.py"),
    os.path.join(ROOT, "Scripts", "ApexCloudLanes.py"),
    os.path.join(ROOT, "Scripts", "SwarmOrchestrator.py"),
    os.path.join(ROOT, "Scripts", "SkillLibrary.py"),
    os.path.join(ROOT, "Scripts", "ApexGuard.py"),
    os.path.join(ADAPTER, "adapter_token.txt"),
]

SECRET_SHAPES = [
    re.compile(r"gsk_[A-Za-z0-9]{16,}"),               # Groq
    re.compile(r"sk-or-[A-Za-z0-9-]{16,}"),            # OpenRouter
    re.compile(r"sk-[A-Za-z0-9]{20,}"),                # OpenAI-style
    re.compile(r"AKIA[0-9A-Z]{16}"),                   # AWS
    re.compile(r"Bearer [A-Za-z0-9_\-\.]{25,}"),       # generic bearer
    re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),            # Google
    re.compile(r"(?:GROQ_API_KEY|OPENROUTER_API_KEY|GEMINI_API_KEY|SERPER_API_KEY|CLOUDFLARE_API_TOKEN)\s*[=:]\s*[A-Za-z0-9_\-]{16,}"),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_logs():
    findings = []
    log_files = []
    for d in (os.path.join(ROOT, "Logs"), os.path.join(ADAPTER, "Logs")):
        try:
            log_files += [os.path.join(d, f) for f in os.listdir(d)
                          if os.path.isfile(os.path.join(d, f)) and os.path.getsize(os.path.join(d, f)) < 60 * 1024 * 1024]
        except OSError:
            pass
    for extra in (os.path.join(ADAPTER, "swarm_findings.jsonl"),
                  os.path.join(ROOT, "memory_episodic.jsonl")):
        if os.path.isfile(extra):
            log_files.append(extra)
    for p in log_files:
        try:
            with open(p, "rb") as f:
                data = f.read(40 * 1024 * 1024).decode("utf-8", "ignore")
        except (OSError, MemoryError):
            continue
        for i, line in enumerate(data.splitlines()):
            for rx in SECRET_SHAPES:
                if rx.search(line):
                    findings.append({"file": os.path.basename(p), "line": i + 1,
                                     "shape": rx.pattern[:40], "ctx": line[:120]})
                    break
            if len(findings) > 20:
                return findings
    return findings


def backups():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if os.listdir(BACKUP_DIR):
        olds = sorted(os.listdir(BACKUP_DIR), reverse=True)
        for name in olds[4:]:
            try:
                os.remove(os.path.join(BACKUP_DIR, name))
            except OSError:
                pass
    stamp = time.strftime("%Y%m%d_%H%M%S")
    zpath = os.path.join(BACKUP_DIR, f"config_backup_{stamp}.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        cfg = os.path.join(ROOT, "Config")
        for root, _dirs, files in os.walk(cfg):
            if "backups" in root:
                continue
            for f in files:
                fp = os.path.join(root, f)
                try:
                    z.write(fp, os.path.relpath(fp, ROOT))
                except OSError:
                    pass
    return zpath


def main(mode="audit"):
    result = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "mode": mode}
    if mode in ("audit", "respin"):
        pins = {}
        for p in PINNED:
            try:
                pins[os.path.basename(p)] = sha256(p)
            except OSError:
                pins[os.path.basename(p)] = "MISSING"
        result["pins"] = pins
        with open(BASELINE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1)
        result["backed_up"] = backups()
        result["leaks"] = scan_logs()
    else:  # verify
        try:
            base = json.load(open(BASELINE, encoding="utf-8-sig"))
        except Exception:
            print("VERIFY FAILED: no baseline - run without --respin first")
            return 1
        drift = []
        for name, pin in base.get("pins", {}).items():
            matches = [p for p in PINNED if os.path.basename(p) == name]
            if not matches:
                drift.append({"file": name, "reason": "pinned file disappeared"})
                continue
            try:
                cur = sha256(matches[0])
                if cur != pin:
                    drift.append({"file": name, "reason": "content changed"})
            except OSError:
                drift.append({"file": name, "reason": "unreadable"})
        result["drift"] = drift
        leaks = scan_logs()
        result["leaks"] = leaks
    ok = (not result.get("drift")) and (not result.get("leaks"))
    print(json.dumps(result, indent=1)[:1800])
    if mode == "verify":
        print("VERIFY:", "PASS - no drift, no leaked secrets in logs" if ok
              else "FAIL - see drift/leaks above")
        return 0 if ok else 1
    print("AUDIT: baseline written + backup taken")
    return 0


if __name__ == "__main__":
    mode = "verify" if "--verify" in sys.argv else ("respin" if "--respin" in sys.argv else "audit")
    sys.exit(main(mode))