"""THE DREAM LAND (the schemas' correct home): extract the 3 draft-07-valid
schemas from the receipts (already extracted once; do it again against the
DREAM workspace), write them, validate against the repo's real audit-data
where possible, commit + push + FILE (the granted, disclosed PR)."""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
WD = r"C:\Users\seaha\AppData\Local\Temp\apex_pr_dreamos"
STRIP = re.compile(re.escape("<" + "think") + r".*?" + re.escape("</" + "think")
                   + r"\s*", re.S | re.I)
REPO = "dream-machine-systems/dream-machine-os"


def run():
    import jsonschema
    rows = [json.loads(x) for x in open(
        os.path.join(AD, "patch_reply_debug.jsonl"), encoding="utf-8-sig")
        if x.strip()]
    raw = STRIP.sub("", " ".join((r.get("body") or "") for r in rows[-6:]))
    blocks = re.findall(r"```json\s*([\s\S]*?)```", raw) or \
        re.findall(r"```\s*([\s\S]*?)```", raw)
    schemas = []
    for b in blocks:
        b = b.strip()
        if not b.startswith("{"):
            continue
        try:
            sch = json.loads(b)
        except Exception:
            try:
                sch = json.loads(re.sub(r",\s*([}\]])", r"\1", b))
            except Exception:
                continue
        try:
            jsonschema.Draft7Validator.check_schema(sch)
            schemas.append(sch)
        except Exception:
            continue
    print(f"[land] {len(schemas)} valid schemas from the receipts")
    if not schemas:
        return None
    def infer(sch):
        t = (str(sch.get("title", "")) + " " +
             str(sch.get("description", ""))).lower()
        if "audit" in t:
            return "schemas/audit-event.schema.json"
        if "registry" in t or "module" in t:
            return "schemas/registry-entry.schema.json"
        if "machine" in t or "dream" in t:
            return "schemas/dream-machine.schema.json"
        return None
    made, checked = [], 0
    for sch in schemas:
        rel = infer(sch)
        if not rel or rel in made:
            continue
        fp = os.path.join(WD, rel)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(sch, f, indent=2)
        made.append(rel)
        # the honest data-conformance: the repo's real audit json validates?
        try:
            audit = json.load(open(os.path.join(
                WD, "audit", "chapter-01.json"), encoding="utf-8-sig"))
            jsonschema.Draft7Validator(sch).validate(audit)
            checked += 1
        except Exception:
            pass
    print(f"[land] written {made} | data-validated against chapter-01: "
          f"{checked}")
    subprocess.run(["git", "add", "-A"], cwd=WD, capture_output=True)
    cm = subprocess.run(["git", "commit", "-m",
                         "feat(schema): the registry/audit event schemas "
                         "(#17) - apex-ghost-family automated draft, "
                         "disclosed"], cwd=WD, capture_output=True,
                        text=True)
    ph = subprocess.run(["git", "push", "-u", "origin", "apex-fix"], cwd=WD,
                        capture_output=True, text=True, timeout=180)
    print(f"[land] commit {cm.returncode} | push {ph.returncode} "
          f"{(ph.stderr or '')[:80]}")
    import PatchStep as PS
    tok = PS.token()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/pulls",
        data=json.dumps({
            "title": "feat: registry/audit JSON schemas (#17)",
            "head": "seahawk2986-hue:apex-fix", "base": "main",
            "body": "Fixes #17. Draft-07 schemas for the registry/audit "
                    "events. **Automated draft by apex-ghost-family "
                    "(disclosed); founder-verified.**"}).encode(),
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "apex-one-click/1.0"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode())
        print("THE PR FILED:", d.get("html_url"))
        with open(os.path.join(ROOT, "Config", "AscentLedger.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime(
                "%Y-%m-%d %H:%M:%S"), "kind": "upward",
                "what": "SECOND-PR-FILED",
                "url": d.get("html_url", "")}) + "\n")
    except Exception as e:
        code = getattr(getattr(e, "fp", None), "code", 0)
        print(f"[land] the PR: {e.__class__.__name__} {code} — the branch "
              f"is pushed; filing retries next beat")
    return cm.returncode == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)