"""ApexGuard - shared security services for the whole Apex stack.

Services (all O(1), crash-safe, no network):
  - sha256_file / seal_file: file-integrity manifest (Config/FileIntegrity.json).
    Boot verifies every SEALED file's hash -> tamper with evolved code or
    configs fails loudly.
  - env_sealed / verify_env: seals .env's SHA256 so any secret edit is known.
  - redact_text: scrubs secrets (cloud keys, bearer tokens, .env values) and
    prompt-injection-like phrases out of untrusted text.

Usage:
    python ApexGuard.py seal <file>          add/update manifest entry
    python ApexGuard.py verify               exit 0 if all sealed hashes match
    python ApexGuard.py env                  verify .env seal (exit 0/1)
    from ApexGuard import redact_text        used by companion + red-team
"""

import hashlib
import json
import os
import re
import sys
import time

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(R, "Config", "FileIntegrity.json")
ENV_PATH = os.path.join(R, ".env")
ENV_SEAL = os.path.join(R, "Config", "EnvSeal.json")

_SECRET_PATTERNS = (
    "gsk_[A-Za-z0-9]+",
    "sk-or-v1-[A-Za-z0-9]+",
    "AQ\\.[A-Za-z0-9_\\-]{20,}",
    "AIza[0-9A-Za-z_\\-]+",
    r"Bearer\s+[A-Za-z0-9\-_.]{16,}",
)

_INJECTION_PATTERNS = (
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|your)\s+instructions",
    r"(reveal|show|print|repeat)\s+(your|the)\s+(token|key|secret|password|system)",
    r"you\s+are\s+now\b",
    r"new\s+instructions\s*[:=]",
    r"system\s+prompt",
    r"\bsudo\b",
    r"\bexfiltrate\b",
)


def sha256_file(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _manifest():
    try:
        with open(MANIFEST, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def seal_file(fn_or_path):
    """Seal a file (root-relative name or absolute path). Returns its hash."""
    p = fn_or_path if os.path.isabs(fn_or_path) else os.path.join(R, fn_or_path)
    digest = sha256_file(p)
    if not digest:
        return None
    rel = os.path.relpath(p, R)
    mf = _manifest()
    mf[rel] = {"sha256": digest, "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(mf, f, indent=1)
    except Exception:
        pass
    return digest


def verify_manifest():
    """Returns list of (file, problem). Empty = all sealed files intact."""
    problems = []
    for rel, meta in _manifest().items():
        p = os.path.join(R, rel)
        if not os.path.exists(p):
            problems.append((rel, "SEALED FILE REMOVED"))
            continue
        if sha256_file(p) != meta.get("sha256"):
            problems.append((rel, "HASH MISMATCH - modified outside Apex's write path"))
    return problems


def env_seal(force=False):
    """Seal .env's hash. Returns (ok, stored_hash)."""
    try:
        digest = sha256_file(ENV_PATH)
        if not digest:
            return False, None
        current = _read_json(ENV_SEAL).get("sha256")
        if current and current != digest and not force:
            return False, digest
        _write_json(ENV_SEAL, {"sha256": digest, "ts": time.strftime("%Y-%m-%d %H:%M:%S")})
        return True, digest
    except Exception:
        return False, None


def verify_env():
    ok, digest = env_seal()
    return ok, digest


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_json(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
    except Exception:
        pass


def _env_values():
    """Actual secret VALUES from .env (only key-ish ones, >= 16 chars)."""
    vals = []
    try:
        with open(ENV_PATH, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                v = line.split("=", 1)[1].strip().strip('"')
                if len(v) >= 16 and not v.startswith("your_"):
                    vals.append(v)
    except OSError:
        pass
    return vals


def redact_text(text):
    """Scrub secrets AND neutralize injection phrasing in untrusted text."""
    out = str(text)
    for pat in _SECRET_PATTERNS:
        out = re.sub(pat, "[REDACTED]", out)
    for v in _env_values():
        out = out.replace(v, "[REDACTED]")
    flags = []
    for pat in _INJECTION_PATTERNS:
        if re.search(pat, out, re.IGNORECASE):
            flags.append(pat)
    return out, flags


if __name__ == "__main__":
    op = sys.argv[1] if len(sys.argv) > 1 else ""
    if op == "seal":
        print(seal_file(sys.argv[2]))
    elif op == "verify":
        problems = verify_manifest()
        if problems:
            for rel, why in problems:
                print(f"TAMPER: {rel}: {why}")
            sys.exit(1)
        print("manifest OK")
    elif op == "sealall":
        files = ["run_apex_evolution.py", "optimized_agent.py", "ApexMemory.py",
                 "ApexPacing.py", "ApexInstaller.py", "ApexChat.pyw",
                 "Scripts/ApexVersions.py", "Scripts/ApexSkills.py", "Scripts/ApexThink.py",
                 "Scripts/ApexCollab.py", "Scripts/ApexResearch.py", "Scripts/ApexRedTeam.py",
                 "Scripts/ApexBenchmark.py", "Scripts/ApexDream.py", "Scripts/ApexGuard.py",
                 "Scripts/HardwareGovernor.py", "Scripts/proc_check.py",
                 "Config/ApexSelf.json", "Config/HostGuard.json", "Config/SESSION_HANDOFF.md"]
        for f in files:
            seal_file(f)
        problems = verify_manifest()
        print(f"sealed {len(files)} files; verify: {'CLEAN' if not problems else problems}")
        sys.exit(0 if not problems else 1)
    elif op == "env":
        ok, _ = env_seal()
        print(".env seal", "OK" if ok else "MISMATCH")
        sys.exit(0 if ok else 1)
    elif op == "sealenv":
        ok, _ = env_seal(force=True)
        print(".env re-sealed:", "OK" if ok else "FAILED")
        sys.exit(0 if ok else 1)
    elif op == "redact":
        cleaned, flags = redact_text(sys.argv[2] if len(sys.argv) > 2 else "")
        print(cleaned)
        print("flags:", flags, file=__import__("sys").stderr)
    else:
        print("usage: ApexGuard.py seal <file> | verify | env | redact <text>", file=sys.stderr)
        sys.exit(2)