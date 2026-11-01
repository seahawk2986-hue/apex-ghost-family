"""CONVERSION RUN (Part VIII W3 Agentless + W7 Rubrics + human gate):
ONE run = ONE triaged candidate -> localize (tarball, keyless) -> draft
(single-turn brain call, bounded) -> rubric-validate (context-grounded
checklist; no sandbox needed) -> HUMAN-GATED dossier. Nothing is ever filed
automatically; the family's first external artifacts go through Andrew.
Hardware law: stdlib, bounded calls (60s), RAM-gated 2.2GB, fail-closed,
print-first. Digest-evidenced dossier. One artifact per run by design."""
import gzip
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import time
import urllib.request

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
AD = r"C:\Users\seaha\Apex-Adapter"
TRIAGE = os.path.join(ROOT, "Config", "issue_triage.jsonl")
DOSSIER_DIR = os.path.join(ROOT, "family", "draft_artifacts")
REVIEW = os.path.join(AD, "pending_review.jsonl")


def ram_free():
    try:
        import psutil
        return psutil.virtual_memory().available / 2 ** 30
    except Exception:
        return 0.0


def loaded_model():
    """Two-server aware brain probe (LM Studio state + Ollama resident);
    None else - honest skips, never loads (the run scheduler loads delib-
    erately during RAM windows, never the organs)."""
    try:
        for m in json.load(urllib.request.urlopen(
                "http://127.0.0.1:1234/api/v0/models", timeout=4)).get("data", []):
            if m.get("state") == "loaded" and "text-embedding" not in (m.get("id") or ""):
                return m["id"]
    except Exception:
        pass
    try:
        ps = json.load(urllib.request.urlopen(
            "http://127.0.0.1:11434/api/ps", timeout=4)).get("models", [])
        if ps:
            return ps[0].get("name")
    except Exception:
        pass
    return None


def brain(prompt, model, max_tokens=400, timeout=60):
    req = urllib.request.Request(
        "http://127.0.0.1:1234/v1/chat/completions",
        data=json.dumps({"model": model, "messages":
                         [{"role": "user", "content": prompt}],
                         "temperature": 0.3, "stream": False,
                         "max_tokens": max_tokens}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        txt = (((json.load(r).get("choices")) or [{}])[0].get("message", {})
               or {}).get("content", "") or ""
    # W2-adjacent hygiene: strip think chains if the loaded model reasons
    if "</think>" in txt and "</think>" in txt:
        return txt.split("</think>")[-1].strip()
    return txt.strip()


def pick_candidate():
    best = None
    if os.path.exists(TRIAGE):
        for line in open(TRIAGE, encoding="utf-8-sig"):
            try:
                r0 = json.loads(line)
            except Exception:
                continue
            if float(r0.get("clarity", 0)) >= 45:
                if best is None or float(r0.get("clarity", 0)) > float(best.get("clarity", 0)):
                    best = r0
    return best


def localize(repo, keywords):
    """W3 phase 1: shallow tarball (keyless, branch-fallback), stream files,
    keep excerpts whose path or content matches issue keywords. Bounded."""
    ev, scanned = [], 0
    raw = None
    for suffix in ("refs/heads/HEAD", "", "refs/heads/master", "refs/heads/main"):
        try:
            url = f"https://codeload.github.com/{repo}/tar.gz"
            if suffix:
                url += "/" + suffix
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
            break
        except Exception as e:
            print(f"[convert] fetch {repo} ({suffix or 'default'}) -> {str(e)[:50]}")
            raw = None
    if not raw:
        print("[convert] localize failed honestly: all branches exhausted")
        return ev, scanned
    try:
        tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
        kws = [k for k in re.split(r"\W+", (keywords or "").lower()) if len(k) > 3][:8]
        for m0 in tf.getmembers():
            if not m0.isfile() or not m0.name.endswith(".py") or scanned > 400:
                continue
            scanned += 1
            try:
                src = tf.extractfile(m0).read().decode("utf-8", "ignore")[:20000]
            except Exception:
                continue
            low = src.lower()
            hits = [k for k in kws if k in low or k in m0.name.lower()]
            if hits:
                ev.append({"file": m0.name, "matches": hits,
                           "excerpt": src[:4000]})
                if len(ev) >= 6:
                    break
    except Exception as e:
        print(f"[convert] localize parse failed honestly: {str(e)[:70]}")
    return ev, scanned


def rubric_check(draft, evidence, issue):
    """W7 phase 3: deterministic rubric (no sandbox): patch-shaped? touches a
    localized file's language? addresses issue keywords? Each leg honest.
    A brain-optional opinion could refine this later; deterministic first."""
    kws = [w for w in re.split(r"\W+", issue.lower()) if len(w) > 4][:6]
    legs = {
        "addresses_issue": bool(issue) and any(k in (draft or "").lower() for k in kws),
        "localized_grounding": bool(evidence) and any(
            (e0["file"].split("/")[-1]).rsplit(".", 1)[0].lower()
            in (draft or "").lower() for e0 in evidence),
        "patch_shaped": bool(re.search(r"def \w+|@@|[-+]{1,2}\s", draft or "")) or
                        ("replace" in (draft or "").lower() and len(draft) > 120),
        "not_hallucinated_url": "http://" not in (draft or "")[:200],
    }
    passed = sum(1 for v in legs.values() if v)
    total = len(legs)
    return legs, passed, total


def run():
    if ram_free() < 2.2:
        print("[convert] RAM below 2.2GB gate - skipped honestly this run")
        return None
    cand = pick_candidate()
    if not cand:
        print("[convert] no triaged candidate at clarity>=45 - run IssueTriage first "
              "or lower the bar (honest zero)")
        return None
    repo, issue = cand.get("repo"), (cand.get("issue") or "")
    print(f"[convert] CANDIDATE: {repo} | {issue[:70]} | clarity {cand.get('clarity')}")
    model = loaded_model()
    if not model:
        print("[convert] no loaded brain - honest skip (never loads models on its own)")
        return None
    print(f"[convert] brain: {model}")
    t0 = time.time()
    evidence, scanned = localize(repo, issue)
    print(f"[convert] LOCALIZE: {len(evidence)} relevant files from {scanned} scanned "
          f"(.py stream) in {time.time()-t0:.0f}s")
    if not evidence:
        print("[convert] no localized evidence - one honest zero; the candidate "
              "may be misaligned (Q5 gate caught it early) - logged, nothing filed")
        ev_json = []
    else:
        ev_json = [{k: e0[k] for k in ("file", "matches")} for e0 in evidence]
    ctx = "\n\n".join(f"--- {e0['file']} ---\n{e0['excerpt'][:2500]}" for e0 in evidence) or "(no matching file found)"
    prompt = (f"You are drafting a FIX SUGGESTION (never applied automatically) for "
              f"repo {repo}, issue: {issue!r}\nRelevant code:\n{ctx[:6000]}\n\n"
              f"Produce: (1) a one-paragraph diagnosis, (2) a minimal patch suggestion "
              f"as unified-diff-style pseudocode or concrete edit, (3) one test to "
              f"verify it. Be concrete and minimal.")
    draft = brain(prompt, model) if evidence else ""
    print(f"[convert] DRAFT: {len(draft)} chars from {model} (single-turn, W3)")
    legs, passed, total = rubric_check(draft, evidence, issue)
    print(f"[convert] RUBRIC (W7): {passed}/{total} legs pass -> {legs}")
    ok = bool(evidence) and passed >= (total - 1) and len(draft) > 120
    oid = hashlib.sha256((repo + issue + str(time.time())).encode()).hexdigest()[:12]
    os.makedirs(DOSSIER_DIR, exist_ok=True)
    path = os.path.join(DOSSIER_DIR, oid + ".md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# DRAFT ARTIFACT {oid} - FOR ANDREW'S REVIEW (nothing filed)\n\n"
                f"- repo: {repo}\n- issue: {issue}\n- triaged clarity: {cand.get('clarity')}\n"
                f"- localized evidence: {json.dumps(ev_json, ensure_ascii=False)}\n\n"
                f"## Rubric ({passed}/{total})\n" +
                "".join(f"- {k}: {'PASS' if v else 'FAIL'}\n" for k, v in legs.items()) +
                f"\n## Draft suggestion ({len(draft)} chars, model {model})\n\n{draft}\n\n"
                f"## Alignment caveat (Q5)\nVerify the issue<->fix pairing BEFORE any "
                f"filing; 13.6% of such pairs are misaligned in the wild.\n")
    dig = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    row = {"id": oid, "repo": repo, "issue": issue[:100], "path": path,
           "digest": dig, "rubric": f"{passed}/{total}", "status": "PENDING_HUMAN_REVIEW",
           "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(REVIEW, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    print(f"[convert] HUMAN GATE: dossier {oid} written ({len(draft)}-char draft, "
          f"digest {dig}) -> pending_review.jsonl - NOTHING was filed automatically")
    print(f"[convert] SUMMARY: candidate={repo[:40]} evidence={len(evidence)} "
          f"rubric={passed}/{total} artifact={'READY-FOR-REVIEW' if ok else 'WEAK-SKIP-REVIEW'}")
    return row


if __name__ == "__main__":
    run()