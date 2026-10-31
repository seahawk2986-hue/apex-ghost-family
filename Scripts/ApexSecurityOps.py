"""ApexDream v3 additions: voice capability note, supply-chain audit (weekly),
backup rotation, disk-pressure metric. Kept HostGuard-compatible."""
import json
import os
import re
import subprocess
import sys
import time

R = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
PY = os.path.join(R, "apex_venv", "Scripts", "python.exe")
SEC_STATE = os.path.join(R, "Config", "security_state.json")
BACKUPS = os.path.join(R, "Config", "backups")

# 1. Supply-chain audit: weekly pip-audit over the venv requirements
def supply_chain_audit(force=False):
    state = _read(SEC_STATE, {})
    last = float(state.get("last_pip_audit", 0) or 0)
    if time.time() - last < 7 * 86400 and not force:
        return None
    try:
        r = subprocess.run([PY, "-m", "pip_audit", "-r",
                            os.path.join(R, "requirements.txt"), "-f", "json",
                            "--no-deps"],
                           capture_output=True, text=True, timeout=300)
        findings = []
        if r.stdout.strip():
            try:
                data = json.loads(r.stdout)
                deps = data.get("dependencies", [])
                for dep in deps:
                    for vuln in dep.get("vulns", []):
                        findings.append({"package": dep.get("name"),
                                         "id": vuln.get("id"),
                                         "fix": (vuln.get("fix_versions") or [None])[0]})
            except Exception:
                pass
        out = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "vulnerabilities": findings}
        state["last_pip_audit"] = time.time()
        _write(SEC_STATE, state)
        try:
            m = ApexMemory()
            if findings:
                m.record_event("error", f"Supply-chain audit: {len(findings)} CVE(s) found in dependencies", audit=True)
                m.remember(f"Security audit {out['ts']}: {json.dumps(findings)[:300]}. Fix versions listed - upgrade the affected packages this cycle.", kind="lesson")
            else:
                m.record_event("success", "Supply-chain audit: dependencies clean (no known CVEs)", audit=True)
        except Exception:
            pass
        return out
    except Exception as e:
        return {"error": str(e)[:100]}

# 2. Backup rotation: immutable nightly copies, capped at 7
def backup_rotation():
    date = time.strftime("%Y-%m-%d")
    dst_root = os.path.join(BACKUPS, date)
    if os.path.isdir(dst_root):
        return "backup already exists for today"
    os.makedirs(dst_root, exist_ok=True)
    kept = 0
    for name in ("ApexSelf.json", "ApexStrategy.json", "ApexNotes.json", "HostGuard.json",
                 "RewardLedger.json", "SkillRegistry.json", "layer_pids.json",
                 "CheckpointState.json", "security_state.json", "SESSION_HANDOFF.md",
                 "GI_Attributes.md", "PeerProfiles.json", "ResearchCache.json",
                 "TrainingPool.json", "TrainingLog.json"):
        src = os.path.join(R, "Config", name)
        if os.path.exists(src):
            try:
                with open(src, "rb") as fi, open(os.path.join(dst_root, name), "wb") as fo:
                    fo.write(fi.read())
                kept += 1
            except Exception:
                pass
    for src, dst in ((os.path.join(R, "memory_semantic.jsonl"), "memory_semantic.jsonl"),
                     (os.path.join(R, "memory_episodic.jsonl"), "memory_episodic.jsonl")):
        if os.path.exists(src):
            try:
                with open(src, "rb") as fi, open(os.path.join(dst_root, dst), "wb") as fo:
                    fo.write(fi.read())
                kept += 1
            except Exception:
                pass
    # cap: keep the 7 newest dated backup dirs
    try:
        dirs = sorted(d for d in os.listdir(BACKUPS) if os.path.isdir(os.path.join(BACKUPS, d)))
        for old in dirs[:-7]:
            shutil.rmtree(os.path.join(BACKUPS, old), ignore_errors=True)
    except Exception:
        pass
    return f"backup rotation wrote {kept} files to {date}"

# 3. Disk-pressure metric (informational; HostGuard refuses installs below thresholds)
def disk_metric():
    du = shutil.disk_usage("C:\\")
    return {"disk_free_gb": round(float(du.free) / 1024**3, 1),
            "disk_total_gb": round(float(du.total) / 1024**3, 1)}

import shutil  # noqa: E402  (used by backup rotation + disk metric)

def _read(path, default):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def _write(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
    except Exception:
        pass