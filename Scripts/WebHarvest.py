"""WEBHARVEST: the canon-canary fetcher (runner=actions: it runs ON THE
GITHUB RUNNER when the lanes fire; also runnable locally). Fetches the
ChatVoiceCanon's URLs, extracts the page's TITLE + the meta-description
+ the first text-snippet -> the rows -> Config/web_harvest/canon_pages.jsonl.
The = the honest: a 15s per-URL bound, no retries, the failures = the
honest rows (the = the never-zero-claims). The $0: the urllib only."""
import concurrent.futures as cf
import json
import os
import re
import urllib.request

ROOT = os.environ.get("APEX_ROOT",
                      r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed")
CANON = os.path.join(ROOT, "Config", "ChatVoiceCanon.jsonl")
OUTDIR = os.path.join(ROOT, "Config", "web_harvest")

HTML = re.compile(r"<[^>]+>")
TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
DESC = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
                  re.I | re.S)


def fetch(row):
    url = row["url"]
    rec = {"n": row["n"], "url": url, "title_in_canon": row["title"]}
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "apex-webharvest/1.0 (research)"})
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read(300_000).decode("utf-8", "replace")
        t = TITLE.search(body)
        d = DESC.search(body)
        text = HTML.sub(" ", body)
        text = re.sub(r"\s+", " ", text).strip()
        rec.update(status="ok", http=r.status,
                   page_title=(t.group(1).strip()[:160] if t else ""),
                   meta_desc=(d.group(1).strip()[:200] if d else ""),
                   snippet=text[:400], bytes_read=len(body))
    except Exception as e:
        rec.update(status="fail", error=str(e)[:120])
    return rec


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    rows = [json.loads(l) for l in open(CANON, encoding="utf-8") if l.strip()]
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        recs = list(ex.map(fetch, rows))
    out = os.path.join(OUTDIR, "canon_pages.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    ok = sum(1 for r in recs if r.get("status") == "ok")
    print(f"[web-harvest] {ok}/{len(recs)} fetched -> {out}")
    return ok, len(recs)


if __name__ == "__main__":
    main()