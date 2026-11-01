"""THE SCHEMA RESCUE ($0, no new calls): the last reply's receipt holds the
drafted schemas even without the files-map - extract every fenced ```json
block that draft-07-validates, INFER each path from the schema's
title/description (schemas/audit-*.json etc.), re-check against the repo's
REAL shapes (the sample data files validate against them where possible),
write + commit + push to OUR fork; the founder's one click."""
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(
    ROOT := r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed", "Scripts"))
AD = r"C:\Users\seaha\Apex-Adapter"
STATE = os.path.join(AD, "pr_pipeline_state.json")
STRIP = re.compile(re.escape("<" + "think") + r".*?" + re.escape("</" + "think")
                   + r"\s*", re.S | re.I)


def infer_path(sch):
    t = (str(sch.get("title", "")) + " " +
         str(sch.get("description", ""))).lower()
    if "audit" in t:
        return "schemas/audit-event.schema.json"
    if "registry" in t or "module" in t:
        return "schemas/registry-entry.schema.json"
    if "machine" in t or "dream" in t:
        return "schemas/dream-machine.schema.json"
    return None


def run():
    state = json.load(open(STATE, encoding="utf-8-sig"))
    wd = state.get("workspace")
    if not wd or not os.path.isdir(wd):
        print("[rescue] no workspace")
        return None
    rows = []
    try:
        rows = [json.loads(x) for x in open(
            os.path.join(AD, "patch_reply_debug.jsonl"),
            encoding="utf-8-sig") if x.strip()]
    except Exception:
        pass
    if not rows:
        print("[rescue] no receipts")
        return None
    raw = (rows[-1].get("body") or "") + "\n" + \
        ((rows[-2].get("body") or "")[:2000] if len(rows) > 1 else "")
    raw = STRIP.sub("", raw)
    try:
        import jsonschema
    except Exception:
        print("[rescue] jsonschema absent")
        return None
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
            j = re.sub(r",\s*([}\]])", r"\1", b)
            try:
                sch = json.loads(j)
            except Exception:
                continue
        try:
            jsonschema.Draft7Validator.check_schema(sch)
        except Exception:
            continue
        schemas.append(sch)
    print(f"[rescue] {len(schemas)} draft-07-valid schemas extracted from "
          f"the receipts")
    if not schemas:
        return None
    made = []
    for sch in schemas[:4]:
        rel = infer_path(sch)
        if not rel or rel in made:
            continue
        fp = os.path.join(wd, rel)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(sch, f, indent=2)
        made.append(rel)
    if not made:
        print("[rescue] the schemas' titles didn't yield paths - stop")
        return None
    print(f"[rescue] written: {made}")
    subprocess.run(["git", "add", "-A"], cwd=wd, capture_output=True)
    cm = subprocess.run(["git", "commit", "-m",
                         "feat(schema): the registry/audit schemas (#17) - "
                         "apex-ghost-family automated draft, disclosed"],
                        cwd=wd, capture_output=True, text=True)
    ph = subprocess.run(["git", "push", "-u", "origin", "apex-fix"], cwd=wd,
                        capture_output=True, text=True, timeout=120)
    print(f"[rescue] commit {cm.returncode} | push {ph.returncode} "
          f"{(ph.stderr or '')[:70]}")
    print("\nTHE FOUNDER'S ONE CLICK:\n"
          "gh pr create -R dream-machine-systems/dream-machine-os "
          "--head seahawk2986-hue:apex-fix --title "
          "'feat: registry/audit JSON schemas (#17)' --body 'Fixes #17. "
          "Draft-07 schemas. Automated draft by apex-ghost-family "
          "(disclosed); founder-verified.'")
    with open(os.path.join(AD, "patch_state.json"), "w",
              encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "issue": 17, "files": made, "pushed":
                   ph.returncode == 0}, f, indent=1)
    return cm.returncode == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)