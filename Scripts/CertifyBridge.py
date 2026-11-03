"""CertifyBridge - THE EXECUTION CERTIFIER (2026-11-04, swarm organ).

THE MEASURED CHOKE (the vetting-funnel audit): the family mines 3,196
repos, statically vets 569 skills... and certifies exactly 10. The drop
was STRUCTURAL, never effortful:
  - SkillLibrary/SkillRegistry connect via NOTHING: ApexSkills.distill
    certifies only files with RewardLedger best>=100 (self-evolution);
  - library rows point at GITHUB paths (prml/kernel/...), and recertify
    resolves them against the LOCAL disk -> instant honest demotion.
    The two halves of the funnel never touched.

THE BRIDGE (novel: seats are EARNED BY RUNNING, not by existing):
  1. pick <= 6 un-certified library skills (bounded beat);
  2. fetch the REAL source from raw.githubusercontent (their own vetted
     path), sha256-MUST-MATCH the vetted row (evidence-first: what was
     vetted is what runs);
  3. behavioral proof: host bandit (the real scanner) + a SEALED container
     run --network none --read-only: ast-compile + import-execution under
     a 20s cap (a top-level crash/loop = not certified, honestly);
  4. nomic embedding (the same vector model the whole family uses) -> a
     registry row in the EXACT distill schema -> find_relevant can
     actually retrieve executed skills now.
  5. episodic receipt + prints. $0. Fail-closed at every step.

Sources: the family's own laws (verify-or-unclaimed; the sandbox-race
TDD contract in run_apex_evolution; the 5-stage gate = the README claim
this organ finally makes TRUE for library skills).
"""
import hashlib
import io
import json
import os
import sqlite3  # noqa: F401 (kept for the reader utilities)
import subprocess
import sys
import time

if getattr(sys.stdout, "apex_wrapped", False) is False:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.stdout.apex_wrapped = True

REPO = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
REGISTRY = os.path.join(REPO, "Config", "SkillRegistry.json")
EPISODIC = os.path.join(REPO, "memory_episodic.jsonl")
MAX_PER_BEAT = 6
IMPORT_CAP_S = 20


def _docker_ok():
    """Docker-true gate (fail-closed: no container = no certification)."""
    try:
        return subprocess.run(["docker", "info"], capture_output=True,
                              timeout=20).returncode == 0
    except Exception:
        return False


_GENERIC = {"__init__", "__main__", "__manifest__", "__version__", "__setup__",
            "config", "logger", "logging", "backend", "utils", "util",
            "helpers", "setup", "constants", "types", "main", "run", "wsgi",
            "settings", "urls", "forms", "serializers", "middleware"}


def _candidates(st, want=MAX_PER_BEAT):
    reg_names = set()
    try:
        reg = json.load(open(REGISTRY, encoding="utf-8-sig"))
        reg_names = {k.split("@")[0].lower() for k in reg.keys()}
    except Exception:
        pass
    out = []
    try:
        lib = json.load(open(os.path.join(REPO, "Config", "SkillLibrary.json"),
                             encoding="utf-8-sig"))
        for s0 in lib.get("skills", []):
            name = str(s0.get("skill") or "").strip()
            repo = str(s0.get("source_repo") or "").strip()
            path = str(s0.get("source_file") or "").strip()
            sha = str(s0.get("sha256") or "").strip()
            if not name or "/" not in repo or not path or len(sha) != 64:
                continue
            if name.lower() in reg_names:
                continue
            # THE NAME LAW (2026-11-04, learned on the first beat): a file
            # basename like "__init__" is not a SKILL NAME - the first beat
            # minted meaningless seats ('__init__', '__manifest__') that
            # find_relevant can never honestly rank. Generic basenames stay
            # UN-certified until their library row carries a real name.
            if name.lower() in _GENERIC:
                continue
            if int(s0.get("lines", 0) or 0) < 6:      # a toothless snippet
                continue
            if any(k in name.lower() for k in ("guard", "safety", "embed")):
                continue                               # the classifier law
            out.append({"skill": name, "repo": repo, "path": path,
                        "sha": sha, "license": s0.get("license") or "",
                        "stars": int(s0.get("stars") or 0),
                        "vetby": s0.get("vetby") or ""})
        out.sort(key=lambda c: (-c["stars"], c["vetby"] != "hub-runner-v1"))
    except FileNotFoundError:
        pass
    return out[:want * 3]


def _fetch(c, token=None):
    import requests
    for branch in ("HEAD", "main", "master"):
        url = f"https://raw.githubusercontent.com/{c['repo']}/{branch}/{c['path']}"
        try:
            r = requests.get(
                url, timeout=25,
                headers={"User-Agent": "apex-ghost-family/2.0",
                         "Authorization": f"Bearer {token}"} if token else
                {"User-Agent": "apex-ghost-family/2.0"})
            if r.status_code == 200 and r.text:
                return r.text
        except Exception:
            continue
    return None


def _bandit_clean(text):
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(text)
        p = f.name
    try:
        r = subprocess.run([sys.executable, "-m", "bandit", "-q", "-f", "json",
                            p], capture_output=True, text=True, timeout=60)
        if r.returncode in (0, 1):
            res = json.loads(r.stdout or "{}").get("results", [])
            return not any(x.get("issue_severity") == "HIGH" for x in res)
        return False
    except Exception:
        return False
    finally:
        try:
            os.remove(p)
        except OSError:
            pass


def _container_behavior(text, fname):
    """compile + import in the sealed container (the family's sandbox law)."""
    import tempfile
    d = tempfile.mkdtemp(prefix="apexcert_")
    fp = os.path.join(d, fname)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(text)
    mod = fname[:-3].replace("-", "_").replace(".", "_")
    try:
        r = subprocess.run(
            ["docker", "run", "--rm", "--network", "none", "--read-only",
             "--tmpfs", "/tmp", "-v", f"{d}:/sandbox", "-w", "/sandbox",
             "python:3.12-slim", "python", "-c",
             f"import ast,sys;ast.parse(open('/sandbox/{fname}',encoding='utf-8').read());"
             f"import importlib.util;spec=importlib.util.spec_from_file_location("
             f"'{mod}','/sandbox/{fname}');m=importlib.util.module_from_spec(spec);"
             f"spec.loader.exec_module(m);print('BEHAVIOR-OK')"],
            capture_output=True, text=True, timeout=IMPORT_CAP_S)
        return r.returncode == 0 and "BEHAVIOR-OK" in (r.stdout or "")
    except Exception:
        return False
    finally:
        try:
            subprocess.run(["docker", "kill", "none"], capture_output=True,
                           timeout=5)
        except Exception:
            pass
        try:
            subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", d],
                           capture_output=True, timeout=15)
        except Exception:
            pass


def _embed(text):
    import requests
    try:
        r = requests.post("http://127.0.0.1:1234/v1/embeddings",
                          json={"model": "text-embedding-nomic-embed-text-v1.5",
                                "input": [text[:4000]]}, timeout=120)
        return [d["embedding"] for d in r.json()["data"]][0]
    except Exception:
        return None


def certify(beat_note=False):
    if not _docker_ok():
        print("[bridge]: Docker down - fail-closed, NO certification this beat")
        return []
    try:
        import ApexIO
        token = ApexIO.env(REPO).get("GITHUB_TOKEN")
    except Exception:
        token = None
    certified = []
    reg = json.load(open(REGISTRY, encoding="utf-8-sig")) if os.path.isfile(REGISTRY) else {}
    for c in _candidates(reg):
        if len(certified) >= MAX_PER_BEAT:
            break
        text = _fetch(c, token)
        if not text:
            print(f"[bridge] {c['skill']}: source fetch refused/walled - honest skip")
            continue
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != c["sha"]:
            print(f"[bridge] {c['skill']}: sha MISMATCH vs the vetted row - skip (evidence-first)")
            continue
        try:
            ast_mod = compile(text, c["skill"], "exec")
        except SyntaxError:
            print(f"[bridge] {c['skill']}: syntax fails at HEAD-state source - honest skip")
            continue
        bc = _bandit_clean(text)
        beh = _container_behavior(text, os.path.basename(c["path"]))
        score = 60.0 + (15.0 if bc else 0.0) + (15.0 if beh else 0.0) + 10.0
        if not bc or not beh:
            print(f"[bridge] {c['skill']}: bandit={bc} behavior={beh} -> score {score:.0f} (the seat is NOT earned)")
            continue
        vec = _embed(text)
        if vec is None:
            print(f"[bridge] {c['skill']}: the embedder refused - skip this beat (honest)")
            continue
        key = f"{c['skill']}@{time.strftime('%Y%m%d_%H%M%S')}"
        reg[key] = {"source": c["path"],
                    "intent": (f"library skill certified by EXECUTION "
                               f"(CertifyBridge): compile+bandit+container-run; "
                               f"repo {c['repo']}"),
                    "reward": score, "best": round(score, 1),
                    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "vec": vec}
        certified.append(key)
        print(f"[bridge] CERTIFIED {key}: execution-proof score {score:.0f}")
    if certified:
        import ApexIO
        with ApexIO.lock(REGISTRY, "certify-bridge"):
            tmp = REGISTRY + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(reg, f, ensure_ascii=False, indent=1)
            os.replace(tmp, REGISTRY)
        try:
            with open(EPISODIC, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": os.urandom(6).hex(),
                    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "kind": "certification",
                    "text": f"CERTIFY-BRIDGE: {len(certified)} skill(s) earned "
                            f"registry seats by RUNNING (compile+bandit+container)",
                    "meta": {"keys": certified}, "imp": 0.9},
                    ensure_ascii=False) + "\n")
        except Exception:
            pass
    else:
        print("[bridge]: no seat earned this beat (the honest no-op)")
    if beat_note:
        pass
    return certified


if __name__ == "__main__":
    certify(beat_note=True)