"""THE 50-PAPER VOICE HARVEST: arXiv's free API (no keys, $0), 10 targeted
queries x 8 results, deduped by arxiv-id, top-50 kept. Every paper gets a
one-line takeaway + the feature it supports. Output:
Config/VoicePapers50.jsonl + a digest print. Bounded: ~10 tiny requests."""
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "VoicePapers50.jsonl")

QUERIES = [
    ("ack-backchannel", 'all:"backchannel" AND all:"dialogue"'),
    ("turn-taking", 'all:"turn-taking" AND all:"conversational"'),
    ("barge-in", 'all:"interruption" AND all:"spoken dialogue"'),
    ("wake-word", 'all:"wake word" OR all:"keyword spotting"'),
    ("tts-naturalness", 'all:"text-to-speech" AND all:"naturalness"'),
    ("vui", 'all:"voice user interface"'),
    ("latency", 'all:"latency" AND all:"spoken dialogue system"'),
    ("emotion", 'all:"speech emotion recognition" AND all:"assistant"'),
    ("multiturn", 'all:"multi-turn" AND all:"dialogue system"'),
    ("clarity-confirm", 'all:"confirmation" AND all:"speech" AND all:"interface"'),
]

NS = "{http://www.w3.org/2005/Atom}"
papers = {}
for tag, q in QUERIES:
    url = ("https://export.arxiv.org/api/query?search_query="
           + urllib.parse.quote(q) + "&max_results=8&sortBy=relevance")
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            xml = r.read().decode("utf-8", "replace")
        root = ET.fromstring(xml)
        for e in root.iter(NS + "entry"):
            aid = (e.findtext(NS + "id") or "").split("/abs/")[-1]
            title = " ".join((e.findtext(NS + "title") or "").split())
            year = (e.findtext(NS + "published") or "")[:4]
            authors = [(a.findtext(NS + "name") or "")
                       for a in e.iter(NS + "author")]
            abstract = " ".join((e.findtext(NS + "summary") or "").split())[:200]
            if aid and title and aid not in papers:
                papers[aid] = {"id": aid, "title": title[:140],
                               "authors": ", ".join(authors[:3])
                                          + (" et al." if len(authors) > 3 else ""),
                               "year": year, "tag": tag, "abstract": abstract}
    except Exception as ex:
        print(f"[query {tag}] error: {str(ex)[:70]}")
    time.sleep(3)  # arXiv's politeness rate

rows = list(papers.values())[:50]
with open(OUT, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"[harvest]: {len(rows)} papers -> {OUT}")
by_tag = {}
for r in rows:
    by_tag.setdefault(r["tag"], []).append(r)
for t, rs in sorted(by_tag.items()):
    print(f"  {t:<18} {len(rs)}  e.g. {rs[0]['title'][:70]} ({rs[0]['year']})")