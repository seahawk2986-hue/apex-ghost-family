"""Swarm Orchestrator v3 - Ghost Scout swarm: massive, ultra-light, gold-hungry.

Ghost scouts are asyncio coroutines, not threads: 4-10x more scouts at near-zero
RAM/CPU (I/O waits cost nothing). Local disk uses lazy walker threads + a bounded
queue + 8 evaluator ghosts (the full path list is never materialized). Network
runs a dependency-free raw-HTTP asyncio engine with adaptive concurrency scaled
to free RAM (12-64 ghosts), refusing to run under 2 GB free (HostGuard rule).

Waves: (1) GitHub search -> repos + VEIN detection; (2) README fetches ->
MINE/GOLD/VEIN scoring + lead extraction from VEINs; (3) LICENSE verification of
the strongest leads -> MINE confirmation. Gold pays most; veins pay per lead.

Rewards: paid per unit of VERIFIED productive work consumed while working:
answered requests, MB classified, gold/MINE findings, veins, verified leads,
efficiency multiplier for high yield-per-byte. Idle ghosts earn nothing - pay
follows production. Amounts live in Config/RewardConfig.json (ghost_* keys).

Hardware: CPU-only, no model loads, no GPU. Findings stream to JSONL
incrementally; in-RAM dedup is bounded (last 40k sha16s). Cooldown 1h.
"""
import asyncio
import concurrent.futures
import hashlib
import json
import os
import sys as _sys0
_sys0.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import SafeIO
import queue
import re
import ssl
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import uuid

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
SHARD = int(os.environ.get("APEX_SHARD", "0"))   # territory worker id
ADAPTER = r"C:\Users\seaha\Apex-Adapter"
OUT = os.path.join(ADAPTER, "swarm_findings.json")
STATE = os.path.join(ADAPTER, f"swarm_state{'' if SHARD == 0 else '_shard' + str(SHARD)}.json")
GOLDMINE = os.path.join(ADAPTER, "goldmine_register.json")
FINDINGS_JSONL = os.path.join(ADAPTER, "swarm_findings.jsonl")
REWARD_CONFIG = os.path.join(ROOT, "Config", "RewardConfig.json")
GYM_REWARDS = os.path.join(ROOT, "Config", "GymRewards.json")
REWARD_DASH = os.path.join(ROOT, "Config", "RewardLedger.json")
EPISODIC = os.path.join(ROOT, "memory_episodic.jsonl")
SCRIPT_KEY = "Scripts/SwarmOrchestrator.py"

TARGET_DIRS = [ROOT, ADAPTER, r"C:\Users\seaha\Documents",
               r"C:\Users\seaha\Downloads", r"C:\Users\seaha\OneDrive\Documents"]
SKIP_DIRS = {"node_modules", "__pycache__", ".git", "env", "venv", ".venv",
             "Windows", "Program Files", "Program Files (x86)",
             "$Recycle.Bin", "System Volume Information", "AppData",
             ".lmstudio", "apex_venv", "training_venv", ".cache",
             "site-packages", "torch", "numpy", "Logs"}
SKIP_EXT = {".exe", ".dll", ".so", ".pyd", ".bin", ".zip", ".7z", ".rar",
            ".mp4", ".mp3", ".wav", ".jpg", ".png", ".gif", ".ico", ".woff",
            ".woff2", ".ttf", ".db", ".h5", ".safetensors", ".onnx", ".gguf"}
MAX_FILE = 256 * 1024
READ_HEAD = 128 * 1024
MIN_DENSITY = 0.35
MAX_DEPTH = 6
LOCAL_GHOSTS = 8
UA = {"User-Agent": "ApexGhostSwarm/3.0"}
RAM_MIN_GB = 2.0

GOLD_WORDS = ("awesome", "algorithms", "toolkit", "library", "collection",
              "cheatsheet", "recipes", "patterns", "cookbook", "curated")
MIT_MARKERS = ("mit license", "mit-license.org", "permission is hereby granted, free of charge")
VEIN_WORDS = ("awesome", "curated", "list of", "resources")


# ---------------- frontier-lane fetchers (the tools labs themselves use) ----

def serper_search(q, num=10):
    """Google SERP via the already-keyed Serper free tier - targeted vein
    discovery without the GitHub-API quota wall."""
    k = os.getenv("SERPER_API_KEY")
    if not k:
        return []
    try:
        req = urllib.request.Request(
            "https://google.serper.dev/search",
            data=json.dumps({"q": q, "num": num}).encode("utf-8"),
            headers={"X-API-KEY": k, "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
        return [(it.get("link", ""), it.get("title", ""))
                for it in data.get("organic", []) if it.get("link")]
    except Exception:
        return []


def ddg_links(q, num=12):
    """DuckDuckGo HTML discovery lane - free, no key. Serper fallback and
    independent Google-scale discovery for the ghosts."""
    try:
        req = urllib.request.Request(
            "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q),
            headers=UA, method="GET")
        with urllib.request.urlopen(req, timeout=25) as r:
            html = r.read(READ_HEAD).decode("utf-8", "ignore")
    except Exception:
        return []
    out = []
    for m in re.finditer(r'uddg=([^&"]+)', html[:READ_HEAD]):
        try:
            url = urllib.parse.unquote(m.group(1))
            if url.startswith("http") and url not in out:
                out.append(url)
            if len(out) >= num:
                break
        except Exception:
            continue
    return out


def gitlab_projects(n=15, q="awesome"):
    """GitLab metadata lane - gold OUTSIDE GitHub; free, no auth, zero fetches
    (repos register from name/description metadata alone)."""
    try:
        url = (f"https://gitlab.com/api/v4/projects?search=awesome&per_page={n}"
               "&order_by=stars")
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
            data = json.load(r)
        return [(d.get("path_with_namespace", "") or "",
                 (d.get("description") or "")[:120],
                 int(d.get("star_count", 0) or 0))
                for d in data if isinstance(d, dict) and d.get("path_with_namespace")]
    except Exception:
        return []


def codeberg_repos(n=15, q="awesome"):
    """Codeberg (Gitea) lane - the smaller federation, same zero-fetch register."""
    try:
        url = f"https://codeberg.org/api/v1/repos/search?q=awesome&limit={n}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
            data = json.load(r)
        return [(d.get("full_name", "") or "",
                 (d.get("description") or "")[:120],
                 int(d.get("stars_count", 0) or 0))
                for d in data.get("data", []) if isinstance(d, dict) and d.get("full_name")]
    except Exception:
        return []


def github_search(q, per_page=30):
    """GitHub repo search WITH optional token escalation (free PAT in .env
    lifts 60 req/hr unauth to 5,000 req/hr core). Returns [(full_name, desc,
    stars)]. Fail-closed: no token or on error returns []."""
    k = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")
    headers = dict(UA)
    if k:
        headers["Authorization"] = f"Bearer {k}"
    try:
        url = (f"https://api.github.com/search/repositories?q={urllib.parse.quote(q)}"
               f"&sort=stars&order=desc&per_page={per_page}")
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as r:
            data = json.load(r)
        return [(it.get("full_name", ""), (it.get("description") or "")[:150],
                 int(it.get("stargazers_count", 0) or 0))
                for it in data.get("items", []) if it.get("full_name")]
    except Exception:
        return []


def trending_repos(n=25):
    """GitHub trending firehose - fresh repos daily = uncached gold the dedup
    ratchet pays on immediately. One request, public page, no auth."""
    try:
        with urllib.request.urlopen(urllib.request.Request(
                "https://github.com/trending/python?since=daily", headers=UA), timeout=25) as r:
            html = r.read(READ_HEAD).decode("utf-8", "ignore")
        out = []
        seen_t = set()
        for m in re.finditer(r'href="/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)"', html):
            repo = m.group(1)
            if repo.split("/")[0] in ("features", "about", "collections", "trending",
                                      "topics", "pricing", "login", "site", "orgs",
                                      "settings", "security", "search"):
                continue
            repo = m.group(1)
            if repo not in seen_t:
                seen_t.add(repo)
                out.append(repo)
            if len(out) >= n:
                break
        return out
    except Exception:
        return []


def wikipedia_list_leads(n=40):
    """Wikipedia list-of-lists lanes - the non-GitHub corner: raw wikitext of
    curated lists parsed for external gold links."""
    out = []
    import random as _rw
    pool = ("List_of_open-source_artificial_intelligence",
            "List_of_free_and_open-source_software_packages",
            "List_of_machine_learning_algorithms",
            "List_of_datasets_for_machine-learning_research",
            "Outline_of_artificial_intelligence",
            "List_of_numerical_libraries",
            "List_of_command-line_computing_programs",
            "List_of_Python_software",
            "List_of_file_formats",
            "Timeline_of_machine_learning",
            "List_of_data_structures",
            "List_of_algorithms")
    _hh = int(time.time()) // 3600
    pages = (pool[(_hh * 4) % len(pool):] + pool[: (_hh * 4) % len(pool)])[:4]
    for page in pages:
        try:
            url = (f"https://en.wikipedia.org/w/index.php?title={page}&action=raw")
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                wikitext = r.read(READ_HEAD * 2).decode("utf-8", "ignore")
            for m in re.finditer(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)",
                                 wikitext):
                repo = m.group(1).rstrip("/").strip(".)")
                if repo.count("/") == 1 and repo not in out:
                    out.append(repo)
                if len(out) >= n:
                    return out
        except Exception:
            continue
    return out


def wayback_leads(n=60):
    """Wayback CDX corner: historical captures of awesome-list repos - content
    that exists in the archive even when the live web moved on. Bulk-friendly."""
    try:
        url = ("http://web.archive.org/cdx/search/cdx?url=github.com%2F*%2Fawesome-*"
               f"&output=json&limit={n}&collapse=urlkey&filter=statuscode:200")
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            data = json.loads(r.read(512 * 1024).decode("utf-8", "ignore") or "[]")
        rows = data[1:] if isinstance(data, list) and len(data) > 1 else []
        out = []
        for row in rows[:n]:
            if isinstance(row, list) and row:
                u = row[2] if len(row) > 2 else ""
                repo = u.split("github.com/")[-1].split("#")[0].split("?")[0].strip("/")
                if repo.count("/") == 1 and repo not in out:
                    out.append(repo)
        return out
    except Exception:
        return []



def hf_spaces(n=10):
    """HuggingFace Spaces - the open app-lab corner: top-liked spaces' URLs."""
    try:
        url = f"https://huggingface.co/api/spaces?search=algorithm&limit={n}&sort=likes"
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
        return [(d.get("id", ""), int(d.get("likes", 0) or 0))
                for d in data if isinstance(d, dict) and d.get("id")]
    except Exception:
        return []


def hf_model_lanes(n=10):
    """HuggingFace trending text-gen models - fresh-brain discovery corner."""
    try:
        url = (f"https://huggingface.co/api/models?search=agent&limit={n}"
               "&sort=downloads&filter=text-generation")
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
        return [(d.get("id", ""), int(d.get("downloads", 0) or 0))
                for d in data if isinstance(d, dict) and d.get("id")]
    except Exception:
        return []


def hn_discovery(n=10):
    """Hacker News firehose (Firebase, no auth, unlimited): the tech front
    page is a real-time "what just got valuable" feed. GitHub links become
    vein leads; article links become trafilatura page checks."""
    ids = []
    try:
        req = urllib.request.Request(
            "https://hacker-news.firebaseio.com/v0/topstories.json", headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            ids = json.load(r)[: n * 3]
    except Exception:
        return [], []
    repos, pages = [], []
    for i in ids[: n * 2]:
        try:
            req = urllib.request.Request(
                f"https://hacker-news.firebaseio.com/v0/item/{i}.json", headers=UA)
            with urllib.request.urlopen(req, timeout=15) as r:
                it = json.load(r)
        except Exception:
            continue
        u = (it or {}).get("url", "")
        if not u:
            continue
        m = re.match(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)", u)
        if m:
            repo = m.group(1).rstrip("/")
            if repo not in repos:
                repos.append(repo)
        elif "news.ycombinator.com" not in u:
            pages.append(u)
        if len(repos) >= n or len(pages) >= max(2, n // 3):
            break
    return repos[:n], pages[: max(2, n // 3)]


def searchcode_repos(n=12):
    """DEAD LANE kept fail-closed: searchcode.com API returns 404 as of
    2026-10-31. Returns [] immediately - zero requests spent."""
    return []
    out = []
    queries = ("sorting algorithm python", "binary search implementation",
               "dynamic programming python")
    try:
        import random
        q = queries[time.time() // 3600 % len(queries)]
        req = urllib.request.Request(
            f"https://searchcode.com/api/codesearch_I/?q={urllib.parse.quote(q)}&per_page=20",
            headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
        for res in (data.get("results") or [])[:n]:
            u = (res.get("location") or "")
            m = re.match(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)", u)
            if m:
                repo = m.group(1).rstrip("/")
                if repo not in out:
                    out.append(repo)
    except Exception:
        return out
    return out[:n]


def stackexchange_leads(n=12):
    """StackExchange advanced search (no key, 300/day per IP): top-voted
    questions carry community-vetted links in their bodies."""
    import html as _html
    out = []
    try:
        tags = ("python", "algorithms", "machine-learning")
        tag = tags[time.time() // 3600 % len(tags)]
        url = (f"https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=votes"
               f"&tagged={tag}&site=stackoverflow&pagesize={n}&filter=withbody")
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read()
            if raw[:2] == b"\x1f\x8b":          # SE gzips every response
                import gzip as _gz
                raw = _gz.decompress(raw)
            data = json.loads(raw.decode("utf-8", "ignore"))
        for it in data.get("items", []):
            body = _html.unescape(it.get("body_markdown") or "")
            for m in re.finditer(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)", body):
                repo = m.group(1).rstrip("/")
                if repo not in out:
                    out.append(repo)
            if len(out) >= n:
                break
    except Exception:
        return out
    return out[:n]


def registry_repos():
    """crates.io + npm registries - fresh packages across ecosystems with
    repository URLs. One request each, no auth."""
    repos_a, repos_b = [], []
    try:
        req = urllib.request.Request("https://crates.io/api/v1/crates?sort=downloads&per_page=20",
                                     headers=UA + {"User-Agent": "ApexGhostSwarm/3.0 (research)"})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
        for c0 in data.get("crates", []):
            rid = c0.get("repository", "") or ""
            m = re.match(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)", rid)
            if m and m.group(1) not in repos_a:
                repos_a.append(m.group(1))
    except Exception:
        pass
    try:
        req = urllib.request.Request(
            "https://registry.npmjs.org/-/v1/search?text=algorithms&size=20", headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
        for o in data.get("objects", []):
            p = (o.get("package") or {})
            links = (p.get("links") or {}).get("repository") or ""
            m = re.match(r"git\+https://github\.com/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)", str(links))
            if not m:
                m = re.match(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)", str(links))
            if m and m.group(1).rstrip(".git") not in repos_b:
                repos_b.append(m.group(1).replace(".git", ""))
    except Exception:
        pass
    return repos_a[:12], repos_b[:12]


def openalex_papers(n=20):
    """OpenAlex - 250M+ scholarly works, no key. Abstracts reconstructed from
    the inverted index; a paper feed far larger than arXiv's slice."""
    out = []
    cats = ("machine learning", "software engineering", "code generation",
            "data structures", "algorithms")
    try:
        q = cats[time.time() // 3600 % len(cats)]
        url = (f"https://api.openalex.org/works?search={urllib.parse.quote(q)}"
               f"&per-page={n}&select=id,display_name,abstract_inverted_index")
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        for w in data.get("results", []):
            inv = w.get("abstract_inverted_index") or {}
            words = [None] * 300
            for word, positions in inv.items():
                for pos in positions[:300]:
                    if pos < 300:
                        words[pos] = word
            abstract = " ".join(x for x in words if x)
            if len(abstract) > 120:
                out.append((str(w.get("id", "")).replace("https://openalex.org/", "openalex:"),
                            str(w.get("display_name", ""))[:120], abstract[:600]))
    except Exception:
        return out
    return out




def gh_events_repos(n=60):
    """GitHub public EVENTS firehose - every Push/Create on GitHub in realtime.
    100 events/request; PushEvent repos are FRESH (dedup ratchet loves them)."""
    k = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")
    headers = dict(UA)
    if k:
        headers["Authorization"] = f"Bearer {k}"
    out = []
    try:
        req = urllib.request.Request("https://api.github.com/events?per_page=100", headers=headers)
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
        for ev in data:
            if ev.get("type") in ("PushEvent", "CreateEvent"):
                repo = (ev.get("repo") or {}).get("name", "")
                if repo.count("/") == 1 and repo not in out:
                    out.append(repo)
            if len(out) >= n:
                break
        return out[:n]
    except Exception:
        return out


def zenodo_records(n=12):
    """Zenodo - open science records (papers/datasets/code), no key."""
    out = []
    qs = ("python algorithm library", "machine learning dataset", "code repository")
    try:
        q = qs[int(time.time()) // 3600 % len(qs)]
        url = f"https://zenodo.org/api/records?q={urllib.parse.quote(q)}&size={n}&sort=mostrecent"
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            if raw[:2] == b"\x1f\x8b":
                import gzip as _gz
                raw = _gz.decompress(raw)
            data = json.loads(raw.decode("utf-8", "ignore"))
        for h in data.get("hits", {}).get("hits", []):
            meta = h.get("metadata") or {}
            title = str(meta.get("title", ""))[:120]
            abstract = str(meta.get("description", ""))[:600]
            out.append("zenodo:" + str(h.get("id")) + "|" + title + "|" + abstract)
    except Exception:
        return out
    return out


def lobsters_links(n=12):
    """lobste.rs - curated tech feed (no auth). URLs -> repos/pages."""
    repos, pages = [], []
    try:
        req = urllib.request.Request("https://lobste.rs/hottest.json", headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read()
            if raw[:2] == b"\x1f\x8b":
                import gzip as _gz
                raw = _gz.decompress(raw)
            data = json.loads(raw.decode("utf-8", "ignore"))
        for it in data[:n]:
            u = it.get("url", "") or ""
            import re as _re
            m = _re.match(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)", u)
            if m and m.group(1) not in repos:
                repos.append(m.group(1))
            elif u.startswith("http") and "lobste.rs" not in u and u not in pages:
                pages.append(u)
        return repos[:n], pages[: max(2, n // 3)]
    except Exception:
        return [], []


def swh_origins(n=12):
    """Software Heritage origin search - the archive of ALL public source
    code history (~20B origins). Rotating needles sweep new territory."""
    out = []
    needles = ["awesome python", "machine learning", "algorithms", "agent framework",
               "data structures", "coding tools"]
    try:
        q = needles[int(time.time()) // 3600 % len(needles)]
        url = ("https://archive.softwareheritage.org/api/1/origin/search/"
               + urllib.parse.quote(q) + f"/?limit={n}")
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        for o in data if isinstance(data, list) else []:
            u = o.get("url", "") or ""
            import re as _re2
            m = _re2.match(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)", u)
            if m:
                repo = m.group(1).replace(".git", "").rstrip("/")
                if repo not in out:
                    out.append(repo)
        return out[:n]
    except Exception:
        return out


def arxiv_entries(n=15, cat="cs.LG"):
    """arXiv Atom API - the paper feed labs harvest; free, structured.
    Category rotates hourly for coverage breadth."""
    try:
        url = ("http://export.arxiv.org/api/query?search_query=all:agent+AND+cat:"
               f"{cat}&sortBy=submittedDate&max_results={n}")
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
            xml = r.read(READ_HEAD * 2).decode("utf-8", "ignore")
    except Exception:
        return []
    out = []
    for m in re.finditer(r"<entry>(.*?)</entry>", xml, re.S):
        e = m.group(1)
        try:
            t = re.search(r"<title>(.*?)</title>", e, re.S).group(1)
            s = re.search(r"<summary>(.*?)</summary>", e, re.S).group(1)
            i = re.search(r"<id>(.*?)</id>", e, re.S).group(1)
            out.append((" ".join(t.split()), " ".join(s.split()), i.strip()))
        except Exception:
            continue
    return out


def hf_datasets(n=15, term="tools"):
    """Hugging Face dataset discovery - downloads-sorted public gold.
    Search term rotates hourly."""
    try:
        url = (f"https://huggingface.co/api/datasets?limit={n}&sort=downloads"
               f"&search={urllib.parse.quote(term)}")
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
            data = json.load(r)
        return [(d.get("id", ""), int(d.get("downloads", 0) or 0), int(d.get("likes", 0) or 0))
                for d in data if isinstance(d, dict) and d.get("id")]
    except Exception:
        return []


_TRAF = None


def extract_main(html):
    """trafilatura main-content extraction - the same extraction step the
    datatrove/dolma corpus pipelines use. Falls back to raw text."""
    global _TRAF
    try:
        if _TRAF is None:
            import trafilatura as _t
            _TRAF = _t
        return _TRAF.extract(html, include_comments=False,
                             include_tables=False, favor_recall=True) or ""
    except Exception:
        return re.sub(r"<[^>]+>", " ", html[:READ_HEAD])


_CFG_CACHE = {"ts": 0.0, "data": None}


def cfg(key, default):
    """MUT_ env override first (evolution is real), then the family config -
    CACHED for 120 s. The old version re-opened and re-parsed RewardConfig.json
    on EVERY call, and it is called thousands of times per round (D1: waste
    paid per request, found in the audit)."""
    try:
        mv = os.environ.get("MUT_" + key)
        if mv is not None:
            return type(default)(mv)
    except Exception:
        pass
    try:
        if _CFG_CACHE["data"] is None or time.time() - _CFG_CACHE["ts"] > 120:
            _CFG_CACHE["data"] = json.load(open(REWARD_CONFIG, encoding="utf-8-sig"))
            _CFG_CACHE["ts"] = time.time()
        return _CFG_CACHE["data"].get(key, default)
    except Exception:
        return default


def pay(points_list):
    """Pay ghost rewards into the same economy the gym and library use."""
    total = sum(points_list)
    if total <= 0:
        return 0
    try:
        rw = json.load(open(GYM_REWARDS, encoding="utf-8-sig"))
    except Exception:
        rw = {"points": 0}
    rw["points"] = rw.get("points", 0) + total
    rw["library_points"] = rw.get("library_points", 0) + total
    rw["ghost_points"] = rw.get("ghost_points", 0) + total
    with open(GYM_REWARDS, "w", encoding="utf-8") as f:
        json.dump(rw, f, indent=1)
    try:
        dash = json.load(open(REWARD_DASH, encoding="utf-8-sig"))
    except Exception:
        dash = {}
    prev = dash.get(SCRIPT_KEY, 0)
    prev = prev.get("points", 0) if isinstance(prev, dict) else prev
    dash[SCRIPT_KEY] = prev + total
    with open(REWARD_DASH, "w", encoding="utf-8") as f:
        json.dump(dash, f, indent=1)
    try:
        row = {"id": uuid.uuid4().hex[:12], "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
               "kind": "success",
               "text": f"GHOST SWARM: {total} points for verified productive work.",
               "meta": {"ghost_points": total, "total": rw["points"]}, "imp": 0.7}
        with open(EPISODIC, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
    except Exception:
        pass
    return total


# ---------------- gold scoring ----------------

def gold_score(text):
    """Return (tier, points, score) for a text finding."""
    raw = text[:READ_HEAD].encode("utf-8", "ignore")
    low = raw.lower()
    lines = low.count(b"\n") + 1
    density = sum(1 for b in raw if 32 <= b < 127 or b in (9, 10, 13)) / max(1, len(raw))
    score = min(60, lines / 20) + density * 20
    is_mit = any(m.encode() in low for m in MIT_MARKERS)
    is_vein = any(w.encode() in low for w in VEIN_WORDS) and lines > 200
    if is_mit:
        score += 30
    score += sum(1 for w in GOLD_WORDS if w.encode() in low) * 5
    if is_vein:
        return ("VEIN", cfg("ghost_vein_opened", 40), score + 25)
    if is_mit and score >= 45:
        return ("MINE", cfg("ghost_finding_mine", 20), score)
    if score >= 25 or (is_mit and lines > 40):
        return ("GOLD", cfg("ghost_finding_gold", 8), score)
    return ("DUST", 0, score)


def write_row(lock, row):
    if lock is None:  # async context: single-threaded loop, direct write
        with open(FINDINGS_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return
    with lock:
        with open(FINDINGS_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------------- local disk ghosts ----------------

def walker(base, out_q, done_ctr, depth=0):
    """Lazy recursive walker: streams paths into a bounded queue, never a list."""
    try:
        with os.scandir(base) as it:
            for e in it:
                try:
                    if e.is_file():
                        if not e.name.startswith("."):
                            ext = os.path.splitext(e.name)[1].lower()
                            if ext not in SKIP_EXT:
                                out_q.put(e.path)
                    elif e.is_dir() and e.name not in SKIP_DIRS and depth < MAX_DEPTH:
                        walker(e.path, out_q, done_ctr, depth + 1)
                except OSError:
                    continue
    except (PermissionError, OSError):
        pass
    finally:
        done_ctr[0] -= 1


def local_ghost(sid, out_q, jsonl_lock, results, work, done_evt, seen):
    """One file-evaluating ghost. Exits when walkers are done AND queue drained.
    Content already registered in state (by sha) is evaluated-but-unpaid:
    production is paid once, not per rediscovery."""
    while True:
        try:
            p = out_q.get(timeout=1.0)
        except queue.Empty:
            if done_evt.is_set():
                return
            continue
        try:
            try:
                sz = os.path.getsize(p)
                if sz <= MAX_FILE and sz >= 40:
                    with open(p, "rb") as f:
                        raw = f.read(READ_HEAD)
                    work["files"] += 1
                    work["bytes"] += len(raw)
                    printable = sum(1 for b in raw if 32 <= b < 127 or b in (9, 10, 13))
                    if printable / max(1, len(raw)) >= MIN_DENSITY:
                        text = raw.decode("utf-8", "ignore")
                        sha = hashlib.sha256(raw).hexdigest()[:16]
                        tier, _pts, score = gold_score(text)
                        if tier != "DUST" and sha not in seen:
                            work["findings"] += 1
                            row = {"src": "local", "path": p,
                                   "lines": text.count("\n") + 1, "bytes": sz,
                                   "sha": sha, "tier": tier, "score": round(score, 1),
                                   "head": text[:150]}
                            write_row(jsonl_lock, row)
                            results.append(row)
            except (OSError, ValueError, PermissionError):
                work["errors"] += 1
        finally:
            out_q.task_done()


# ---------------- network ghost engine (asyncio, raw HTTP, dep-free) ----------------

_SSL = ssl.create_default_context()
_AIO = None


def _try_aio():
    global _AIO
    if _AIO is None:
        try:
            import aiohttp as _a
            _AIO = _a
        except Exception:
            _AIO = False
    return _AIO or None


async def http_fast(session, url, cap=READ_HEAD, timeout=15):
    """RAPID PATH: one handshake, hundreds of requests (keep-alive), native
    de-chunking + redirects. Same shape as http_get: (status, text)."""
    try:
        async with session.get(url, timeout=_AIO.ClientTimeout(total=timeout),
                               allow_redirects=True) as resp:
            body = b""
            async for chunk in resp.content.iter_any():
                body += chunk
                if len(body) >= cap:
                    break
            if resp.status == 200:
                return 200, (body[:cap] if isinstance(body[:cap], bytes) and False else
                             body.decode("utf-8", "ignore"))[:cap]
            return resp.status, ""
    except Exception:
        return 0, ""


async def http_get(url, cap=READ_HEAD, timeout=15):
    """Dependency-free GET over asyncio streams with redirect follow (<=3)."""
    for _ in range(4):
        try:
            u = urllib.parse.urlsplit(url)
        except ValueError:
            return 0, ""
        host = u.hostname
        if not host:
            return 0, ""
        port = u.port or (443 if u.scheme == "https" else 80)
        try:
            rout, wout = await asyncio.wait_for(
                asyncio.open_connection(host, port,
                                        ssl=_SSL if u.scheme == "https" else None),
                timeout)
            pathq = (u.path or "/") + (("?" + u.query) if u.query else "")
            # HTTP/1.0: servers answer with Content-Length bodies (never chunked),
            # which keeps this engine dependency-free without a de-chunk decoder
            wout.write((f"GET {pathq} HTTP/1.0\r\nHost: {u.netloc}\r\n"
                        "User-Agent: ApexGhostSwarm/3.0\r\nAccept: */*\r\n"
                        "Connection: close\r\n\r\n").encode("utf-8"))
            await wout.drain()
            data = b""
            while len(data) < cap:
                chunk = await asyncio.wait_for(rout.read(65536), timeout)
                if not chunk:
                    break
                data += chunk
            wout.close()
            try:
                head, _sep, body = data.partition(b"\r\n\r\n")
                status = int(head.split(b" ", 2)[1])
            except (ValueError, IndexError):
                return 0, ""
            if 300 <= status < 400:
                loc = re.search(rb"location:\s*(\S+)", head, re.I)
                if loc:
                    url = urllib.parse.urljoin(url, loc.group(1).decode("latin-1"))
                    continue
                return status, ""
            if status == 200:
                return 200, body.decode("utf-8", "ignore")
            return status, ""
        except (OSError, asyncio.TimeoutError):
            return 0, ""
    return 0, ""


async def http_get_bytes(url, cap=1024 * 1024, timeout=20):
    """Binary GET (no decode) for bulk endpoints like codeload tarballs."""
    try:
        u = urllib.parse.urlsplit(url)
    except ValueError:
        return 0, b""
    host = u.hostname
    if not host:
        return 0, b""
    port = u.port or (443 if u.scheme == "https" else 80)
    try:
        rout, wout = await asyncio.wait_for(
            asyncio.open_connection(host, port, ssl=_SSL if u.scheme == "https" else None),
            timeout)
        pathq = (u.path or "/") + (("?" + u.query) if u.query else "")
        wout.write((f"GET {pathq} HTTP/1.0\r\nHost: {u.netloc}\r\n"
                    "User-Agent: ApexGhostSwarm/3.0\r\nAccept: */*\r\n"
                    "Connection: close\r\n\r\n").encode("utf-8"))
        await wout.drain()
        data = b""
        while len(data) < cap:
            chunk = await asyncio.wait_for(rout.read(65536), timeout)
            if not chunk:
                break
            data += chunk
        wout.close()
        head, _sep, body = data.partition(b"\r\n\r\n")
        try:
            status = int(head.split(b" ", 2)[1])
        except (ValueError, IndexError):
            return 0, b""
        if status == 200:
            return 200, body
        return status, b""
    except (OSError, asyncio.TimeoutError):
        return 0, b""



_HEARTBEAT = "C:/Users/seaha/Apex-Adapter/ghost_heartbeat" + ("" if SHARD == 0 else "_shard" + str(SHARD)) + ".json"
_HB_ON = {"flag": False}


def _hb_write(d):
    """Heartbeat write with a tamper-EVIDENCE digest (D8 doctrine: a self-hash
    is honest tamper-evidence, NOT cryptographic signing - any writer can
    re-hash; the value is that a DOCTORED trail can no longer be edited
    without leaving an inconsistent digest behind)."""
    try:
        import json as _j
        import hashlib as _h
        d["digest"] = _h.sha256(
            _j.dumps({k0: v0 for k0, v0 in d.items() if k0 != "digest"},
                     sort_keys=True).encode()).hexdigest()[:16]
        _j.dump(d, open(_HEARTBEAT, "w", encoding="utf-8"))
    except Exception:
        pass


def heartbeat(state_dict):
    """The LIGHT: ghosts leave a faint trail (2s cadence, file-weight)."""
    import threading as _th
    import time as _t

    def _loop():
        while _HB_ON["flag"]:
            _hb_write({"ts": _t.strftime("%H:%M:%S"), **state_dict()})
            _t.sleep(2)
    _th.Thread(target=_loop, daemon=True).start()


class GhostNet:
    """Work-meters the ghosts consume from while working - the pay base."""

    def __init__(self):
        self.reqs = 0
        self.ok = 0
        self.bytes = 0
        self.errors = 0
        self.findings = 0
        self.veins = 0
        self.leads = 0
        self.lead_list = []   # repos to LICENSE-verify in wave 3
        self.fails = []       # bounded failure sample for honest diagnostics
        self.checked = set()  # leads this run verified (license text is boilerplate,
                              # so dedup is per-lead, never per-content)
        self.lanes_ok = 0     # frontier lanes that returned data this run
        self.tarballs = 0     # whole-repo bulk harvests (1 request = many files)
        self.tar_imports = [] # import names found in mined code -> PyPI chaining
        self.deep_list = []   # repos whose README scored VEIN - depth-2 targets
        self.lane_hits = {}   # corroboration: independent lanes that saw a repo
        self.origin = {}      # repo -> discovery lane (for mine-credit)
        self.lane_mines = {}  # lane -> verified mines this run
        self.cc_leads = []    # cc-farmed leads (attributed lane)
        self.host_block = {}  # ELECTRICAL PULSE: host -> unblock timestamp
        # ---- THE GHOST NET (full inter-ghost communication) ----
        self.leases = {}      # repo -> lease timestamp (atomic claim)
        self.paused = False   # directive: coordinator says duck
        self.helpers_spawned = 0
        self.announcements = 0
        self.active = set()   # census: ghost sids currently mid-target

    def claim(self, repo):
        """LEASE protocol: one ghost per repo per round, 90 s hard expiry.
        D8: the lease table is pruned (at >4096 entries) of expired claims -
        the old dict grew unboundedly and eviction was soft."""
        now = time.time()
        if len(self.leases) > 4096:
            for _r0 in [r for r, _t in self.leases.items()
                        if _t != -1 and now - _t > 90]:
                del self.leases[_r0]
        t0 = self.leases.get(repo)
        if t0 and now - t0 < 90 and t0 != -1:
            return False
        self.leases[repo] = now
        return True

    def announce(self, repo, leadcount, spawn_task):
        """BROADCAST: a rich vein found -> helpers spawn + leads front-queued."""
        leads_q = getattr(self, "_announce_leads", [])
        if len(leads_q) < 10:
            return
        for lead in leads_q[:20]:
            try:
                self.helper_q.put_nowait(
                    ("https://raw.githubusercontent.com/" + lead + "/HEAD/README.md",
                     "readme", lead))
            except Exception:
                pass
        if leadcount < 20:
            return
        self.announcements += 1
        if self.helpers_spawned < 50 and spawn_task:
            spawn_task()
            self.helpers_spawned += 1
        # D2 doctrine note: announce() must NEVER reset run-level dedupe state
        # mid-run. The old version cleared _reg_seen/mined_repos on the first
        # rich vein -> duplicate registrations + re-fetched repos (audited HIGH).

    def _spawn_helper(self, from_sid, tag):
        """ANNOUNCEMENT: one helper ghost materializes, bound to the bus queue."""
        try:
            loop = asyncio.get_running_loop()
        except Exception:
            return
        loop.create_task(self._helper_body())

    async def _helper_body(self):
        sid = -(id(self) % 10 ** 9)
        try:
            await self.ghost(sid, self.helper_q, self.helper_sems,
                             self.run_ledger, self.run_seen)
        except Exception:
            pass

    async def mine_tar(self, sems, repo, ledger, seen):
        """Bulk-endpoint escape: ONE codeload tarball = whole repo's text, then
        all mining happens locally - no further network politeness consumed.
        The capped download truncates the gzip stream, so decompress
        incrementally and harvest every COMPLETE file in the truncated archive."""
        import io as _io_mod
        import tarfile
        import zlib
        cap = int(cfg("ghost_tarball_cap_mb", 2)) * 1024 * 1024
        async with sems["tar"]:
            st, blob = await http_get_bytes(
                f"https://codeload.github.com/{repo}/tar.gz/refs/heads/HEAD", cap=cap)
            if st != 200:
                for br in ("main", "master", "develop"):
                    st, blob = await http_get_bytes(
                        f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{br}", cap=cap)
                    if st == 200 and blob:
                        break
            if st != 200 or not blob:
                for br in ("main", "master", "develop"):
                    st, blob = await http_get_bytes(
                        f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{br}", cap=cap)
                    if st == 200 and blob:
                        break
        self.bytes += len(blob)
        if st != 200 or not blob:
            self.errors += 1
            return
        try:
            dobj = zlib.decompressobj(16 + zlib.MAX_WBITS)
            raw = dobj.decompress(blob, 64 * 1024 * 1024)
            if not raw:
                raise ValueError("no gzip data")
        except Exception:
            self.errors += 1
            return
        tf = None
        try:
            tf = tarfile.open(fileobj=_io_mod.BytesIO(raw), mode="r:")
        except Exception:
            self.errors += 1
            return
        mined = 0
        while True:
            if mined >= int(cfg("ghost_tarball_files", 30)):
                break
            try:
                m = tf.next()          # tolerant: raises on truncated tail -> break
            except Exception:
                break
            if m is None:
                break
            if not (m.isfile() and m.size > 0 and m.size < 256 * 1024
                    and m.name.endswith((".py", ".md", ".txt", ".c", ".h", ".js"))):
                continue
            try:
                txt = tf.extractfile(m).read(128 * 1024).decode("utf-8", "ignore")
            except Exception:
                continue
            tier, pts, score = gold_score(txt)
            if tier != "DUST":
                mined += 1
                self.findings += 1
                ledger.append(("tarfile", f"{repo}:{m.name}", 0, pts))
                write_row(None, {"src": "tarball", "repo": repo, "file": m.name,
                                 "tier": tier, "score": round(score, 1),
                                 "sha": hashlib.sha256(txt.encode()).hexdigest()[:16]})
            # code->repo recursion: mined gold code cites its own sources
            for m in re.findall(r"github\.com/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)", txt)[:3]:
                if m.count("/") == 1 and m not in seen and m not in self._reg_seen:
                    self._reg_seen.add(m)
                    self.findings += 1
                    ledger.append(("repo", m, 0, cfg("ghost_vein_lead", 2)))
                    write_row(None, {"src": "code-cite", "repo": m, "via": repo})
            # content-driven discovery: imports in real gold code point at PyPI
            # packages, which map back to MORE repos (wave I chains them)
            for imp in re.findall(r"^\s*(?:from|import)\s+([a-zA-Z_][\w]*)",
                                  txt, re.M)[:8]:
                if imp not in self.tar_imports and imp not in sys.stdlib_module_names:
                    self.tar_imports.append(imp)
        try:
            tf.close()
        except Exception:
            pass
        self.tarballs += 1
        seen.add(repo)

    async def ghost(self, sid, q, sems, ledger, seen):
        sem = sems["cdn"]        # fallback retries hit the raw CDN only
        """One network ghost pulling from a work-stealing queue: every ghost is
        busy whenever any target exists (no fixed chunks leaving slots idle)."""
        while True:
            if self.paused:
                return                     # DIRECTIVE: the net says duck
            try:
                url, kind, meta = q.get_nowait()
            except asyncio.QueueEmpty:
                return
            self.active.add(sid)
            self.reqs += 1
            if kind in ("readme", "tar") and meta and not self.claim(meta):
                continue          # LEASE: another ghost owns this repo
            _host = urllib.parse.urlsplit(url).netloc
            tb = self.host_block.get(_host, 0)
            if tb > time.time():
                continue          # a ghost already pulsed this host - skip politely
            if kind == "tar":
                await self.mine_tar(sems, meta, ledger, seen)
                continue
            if kind == "ccindex":
                # the CC index server asks for ~1 req/sec pacing
                await asyncio.sleep(1.5)
            cap = 512 * 1024 if kind == "ccindex" else READ_HEAD
            _host = urllib.parse.urlsplit(url).netloc
            _api_hosts = ("api.github.com", "api.stackexchange.com", "api.openalex.org",
                          "crates.io", "registry.npmjs.org", "pypi.org",
                          "index.commoncrawl.org", "hacker-news.firebaseio.com")
            async with sems["api" if _host in _api_hosts else "cdn"]:
                if self.session:
                    status, text = await http_fast(self.session, url, cap=cap)
                else:
                    status, text = await http_get(url, cap=cap)
            # file/branch fallback: raw.github is case-sensitive (/HEAD/ aliases
            # fail on some repos, and sindresorhus-class repos use lowercase
            # readme.md) - try branches x casing, bounded
            if status == 404 and kind in ("readme", "license"):
                if kind == "readme":
                    base = url.split("?")[0]
                    alts, seen_u = [], set()
                    for br in ("HEAD", "master", "main"):
                        for fn in ("README.md", "readme.md"):
                            alt = base.replace("/HEAD/", f"/{br}/")
                            if "README" not in alt:
                                continue
                            alt = alt.replace("README.md", fn)
                            if alt not in seen_u:
                                seen_u.add(alt)
                                alts.append(alt)
                else:
                    alts = [url.replace("/HEAD/", "/master/"),
                            url.replace("/LICENSE", "/LICENSE.md"),
                            url.replace("/LICENSE", "/LICENSE.txt")]
                for alt in alts:
                    if status == 200 or alt in seen:
                        break
                    async with sem:
                        status, text = await http_get(alt, cap=cap)
            if status == 200 and text:
                self.ok += 1
                self.bytes += len(text)
                if kind == "ccindex":
                    # Common Crawl lead farming: 1 query -> hundreds of URLs
                    got = 0
                    for line in text.splitlines():
                        if got >= int(cfg("ghost_cc_leads", 300)):
                            break
                        try:
                            rec = json.loads(line)
                            u = (rec.get("url", "") or "").split("#")[0].split("?")[0]
                        except Exception:
                            continue
                        if rec.get("status") != 200 or "github.com" not in u:
                            continue
                        repo = u.split("github.com/")[-1].strip("/").split("?")[0]
                        if repo.count("/") == 1 and "/" + repo not in self._reg_seen:
                            got += 1
                            self.leads += 1
                            if not (repo in seen or repo in self._reg_seen):
                                self._reg_seen.add(repo)
                                self.cc_leads = getattr(self, "cc_leads", [])
                                self.cc_leads.append(repo)
                                ledger.append(("repo", repo, 0, cfg("ghost_vein_lead", 2)))
                elif kind == "search":
                    try:
                        data = json.loads(text)
                    except Exception:
                        self.errors += 1
                        continue
                    for it in data.get("items", [])[:15]:
                        full = it.get("full_name", "")
                        stars = int(it.get("stargazers_count", 0) or 0)
                        if not full or full in seen or full in self._reg_seen:
                            continue
                        self._reg_seen.add(full)
                        desc = (it.get("description") or "").lower()
                        if any(w in desc for w in VEIN_WORDS) or "awesome" in full.lower():
                            ledger.append(("vein", full, stars, cfg("ghost_vein_opened", 40)))
                            self.veins += 1
                        elif stars >= int(cfg("ghost_min_stars", 150)):
                            ledger.append(("repo", full, stars, cfg("ghost_vein_lead", 2)))
                elif kind == "readme":
                    sha = hashlib.sha256(text.encode()).hexdigest()[:16]
                    if sha in seen:
                        continue   # content registered before - leads already harvested
                    seen.add(sha)
                    repo = url.split("raw.githubusercontent.com/")[-1].split("/HEAD")[0]
                    repo = repo.split("/master")[0].split("/main")[0]
                    low = text[:64 * 1024].lower()
                    declared = any(w in low for w in MIT_MARKERS)
                    tier, _pts, score = gold_score(text)
                    if tier == "DUST" and not declared:
                        continue
                    if declared:
                        # README declares MIT: the LICENSE fetch is eliminated -
                        # the repo's own description is the verification source
                        if meta not in self.checked:
                            self.checked.add(meta or repo)
                            self.findings += 1
                            ledger.append(("lead", meta or repo, 0,
                                           cfg("ghost_finding_mine", 20)))
                            write_row(None, {"src": "license-readme", "repo": meta or repo,
                                             "tier": "MINE", "license_source": "readme",
                                             "score": round(score, 1), "sha": sha})
                    if tier == "VEIN":
                        self.veins += 1
                        leads, forge_leads = _vein_leads(
                            text, limit=int(cfg("ghost_leads_per_vein", 500)))
                        self.leads += len(leads) + len(forge_leads)
                        if len(leads) >= 20 and sid >= 0:
                            self._announce_leads = list(leads)
                            self.helper_q = self.helper_q if hasattr(self, "helper_q") else None
                            def _spawn(gg=self, s=sid):
                                gg._spawn_helper(s, s)
                            try:
                                self.announce(meta or repo, len(leads), _spawn)
                            except Exception:
                                pass
                        for lead in leads:
                            if lead not in seen and lead not in self._reg_seen:
                                self._reg_seen.add(lead)
                                self.lead_list.append(lead)
                        for f_r in forge_leads:
                            if f_r not in seen and f_r not in self._reg_seen:
                                self._reg_seen.add(f_r)
                                ledger.append(("forge_repo", f_r, 0,
                                               cfg("ghost_vein_lead", 2)))
                                write_row(None, {"src": "forge", "repo": f_r,
                                                 "license_source": "metadata"})
                    if tier != "DUST":
                        self.findings += 1
                        if (meta or repo) not in self.mined_repos:
                            lane = self.origin.get(meta or repo, "none")
                            self.lane_mines[lane] = self.lane_mines.get(lane, 0) + 1
                        self.mined_repos.add(meta or repo)
                        write_row(None, {"src": "net", "repo": meta or repo, "tier": tier,
                                         "score": round(score, 1), "bytes": len(text),
                                         "sha": sha, "head": text[:150]})
                elif kind == "license":
                    if meta in self.checked:
                        continue
                    self.checked.add(meta)
                    tier, pts, score = gold_score(text)
                    if tier != "DUST":
                        self.findings += 1
                        ledger.append(("lead", meta, 0, pts))
                        write_row(None, {"src": "lead", "repo": meta, "tier": tier,
                                         "score": round(score, 1),
                                         "sha": hashlib.sha256(text.encode()).hexdigest()[:16]})
                elif kind == "pypi":
                    try:
                        data = json.loads(text)
                        info = data.get("info") or {}
                        proj = info.get("project_urls") or {}
                    except Exception:
                        self.errors += 1
                        continue
                    links = " ".join(str(v) for v in proj.values() if v)
                    links += " " + str(info.get("home_page") or "")
                    for m in re.finditer(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)", links):
                        repo = m.group(1).rstrip("/")
                        if repo.count("/") == 1 and repo not in seen and repo not in self._reg_seen:
                            self._reg_seen.add(repo)
                            self.findings += 1
                            ledger.append(("repo", repo, 0, cfg("ghost_vein_lead", 2)))
                            write_row(None, {"src": "pypi-chain",
                                             "package": info.get("name", ""),
                                             "repo": repo})
                            break
                elif kind == "page":
                    # arbitrary HTML: trafilatura main-content extraction (the same
                    # step HF datatrove / Ai2 dolma pipelines run) then gold scoring
                    main = extract_main(text)
                    if main and len(main) > 400:
                        tier, pts, score = gold_score(main)
                        if tier != "DUST":
                            self.findings += 1
                            ledger.append(("page", url, 0, pts))
                            write_row(None, {"src": "page", "url": url, "tier": tier,
                                             "score": round(score, 1),
                                             "sha": hashlib.sha256(main.encode()).hexdigest()[:16],
                                             "head": main[:150]})
            else:
                if kind == "ccindex" and status in (403, 404):
                    # CDX "no captures for this pattern" / index server pacing:
                    # legitimate empty results, not failures - rotation retries
                    pass
                else:
                    self.errors += 1
                    if len(self.fails) < 10:
                        self.fails.append({"status": status, "url": url[:80]})



_EMBCACHE = {}


def embeddings(texts, limit=24):
    """LM Studio embeddings (nomic, already installed). Batches capped; empty
    list on any failure - every caller must fail-closed."""
    out = []
    for i in range(0, min(len(texts), limit), 12):
        chunk = texts[i:i + 12]
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:1234/v1/embeddings",
                data=json.dumps({"model": "text-embedding-nomic-embed-text-v1.5",
                                 "input": chunk}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8", "ignore"))
            out += [d["embedding"] for d in data.get("data", [])]
        except Exception:
            out += [None] * len(chunk)
    return out


def _cos(a, b):
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = (sum(x * x for x in a)) ** 0.5
    nb = (sum(x * x for x in b)) ** 0.5
    return dot / (na * nb + 1e-9)


def sem_near_dups(leads, k=200):
    """Cosine near-dup guard over the freshest leads: identical-topic repos
    arriving through many lanes stop double-mining. Exact-string dupes
    collapse FIRST (the guard keys by string, so occurrences need pre-merge)."""
    leads = list(dict.fromkeys(leads))
    fresh = [l for l in leads if l not in _EMBCACHE][: k]
    if len(fresh) < 2:
        return leads
    vecs = embeddings(fresh, limit=k)
    recent = []
    for l, v in zip(fresh, vecs):
        if v is None:
            continue
        _EMBCACHE[l] = v
        if len(_EMBCACHE) > 2000:
            _EMBCACHE.clear()
        recent.append((l, v))
    # pairwise on the last k bounded set
    keep_set = set()
    for i, (li, vi) in enumerate(recent):
        if any(_cos(vi, vj) >= 0.95 for _, vj in recent[max(0, i - 12):i]):
            continue
        keep_set.add(li)
    return [l for l in leads if l in keep_set or l not in fresh]



WEAKNESS_QUERY = {"reasoning": "reasoning+algorithms+python",
                  "memory": "memory+management+python+library",
                  "calibration": "forecast+calibration+python",
                  "arithmetic": "numerical+algorithms+python",
                  "self_model": "meta+learning+python",
                  "default": "algorithms+python"}


PATH_BETA = 2.5
PATH_EPS = 0.08


def pathmem_load():
    try:
        return json.load(open(os.path.join(ROOT, "Config", "PathMemory.json"),
                              encoding="utf-8-sig"))
    except Exception:
        return {}


_PMS_STAMP = {"ts": 0.0}


def pathmem_store(mem):
    """P8 FORAGING DOCTRINE (arXiv:2610.25113 / 2610.24865): the lane field is
    sparse-and-clustered, so pheromone dynamics follow threshold cascades -
    the learner-free swarm that beats flat evaporation up to 7.6x on exactly
    this kind of resource landscape:
      - RICH lane (mines/reqs >= 1.5x the family median, floor 0.15):
        RETAIN nearly all pheromone (0.98) - the found patch holds value.
      - CROWDED lane (mines/reqs <= 0.5x median with >= 8 reqs invested):
        DISPERSE (0.80) - the cascade rule that recruits also self-limits
        crowding, so the swarm releases patches before they choke.
      - everything else: the classic 0.96 evaporation.
      - the CASCADE: up to 3 rich lanes raise their two hardest-working
        non-rich siblings' `recruit_bonus` (+0.25, capped 1.0, decaying every
        store call by 0.5 - a PULSE on scheduling, never a change to measured
        mines/reqs; bonuses are priors, not truth).
    Counters here are exponentially-weighted MEMORY, decaying by design. The
    store is idempotent per 60 s: repeated calls within a round persist but do
    NOT re-evaporate (the old double-call hit every lane with 0.96 twice -
    audited as an effective 0.9216). Writes are atomic+locked (SafeIO)."""
    try:
        now = time.time()
        fresh = (now - _PMS_STAMP["ts"]) > 60
        _PMS_STAMP["ts"] = now
        if fresh:
            lanes = [l0 for l0 in list(mem.keys()) if l0 != "grading"]
            eff = {}
            for l0 in lanes:
                e = mem.get(l0) or {}
                eff[l0] = float(e.get("mines", 0)) / max(1.0, float(e.get("reqs", 0)))
            med = sorted(eff.values())[len(eff) // 2] if eff else 0.0
            rich = [l0 for l0 in lanes
                    if eff[l0] >= max(1.5 * med, 0.15)][:3]
            crowd = {l0 for l0 in lanes
                     if eff[l0] <= 0.5 * med
                     and float((mem.get(l0) or {}).get("reqs", 0)) >= 8}
            # (zero-mine lanes with real reqs invested ARE the most crowded -
            # the old `0 < eff` guard excluded exactly the most-starved lanes)
            for lane in lanes:
                e = mem.get(lane) or {}
                rate = 0.98 if lane in rich else (0.80 if lane in crowd else 0.96)
                for k0 in ("mines", "reqs"):
                    if k0 in e:
                        e[k0] = max(0.0, float(e[k0]) * rate)
                if "recruit_bonus" in e:
                    e["recruit_bonus"] = round(float(e["recruit_bonus"]) * 0.5, 3)
            _sib = sorted((l0 for l0 in lanes if l0 not in rich),
                          key=lambda l0: -float((mem.get(l0) or {}).get("reqs", 0) or 0))
            _n = 0
            for _src in rich:
                _given = 0
                for _s0 in _sib:
                    if _given >= 2:
                        break
                    _se = mem.setdefault(_s0, {})
                    _se["recruit_bonus"] = round(
                        min(1.0, float(_se.get("recruit_bonus", 0)) + 0.25), 3)
                    _given += 1
                _n += _given
            if rich or crowd:
                print(f"[P8 foraging] rich={len(rich)} retained / crowd={len(crowd)} "
                      f"dispersed / cascade grants={_n}", flush=True)
    except Exception as _e:
        print(f"[pathmem_store] evolution step failed: {str(_e)[:80]} - "
              f"memory persisted without decay", flush=True)
    try:
        from SafeIO import write_json as _w
        if not _w(os.path.join(ROOT, "Config", "PathMemory.json"), mem):
            print("[pathmem_store] atomic write FAILED (lock busy) - "
                  "this round's decay is not persisted", flush=True)
    except Exception as _e:
        print(f"[pathmem_store] write failed: {str(_e)[:80]}", flush=True)


def pathmem_shares(mem, lanes):
    """Yield-per-request per lane (+ decaying recruit pulses from rich lanes -
    the P8 cascade) -> softmax shares -> clamped fetch multipliers.
    This IS the evolution: every round's measured outcome reweights the next."""
    import math as _m
    out = {}
    for lane in lanes:
        e = mem.get(lane) or {}
        ypr = (e.get("mines", 0) / max(1, e.get("reqs", 0))
               + float(e.get("recruit_bonus", 0)))
        out[lane] = _m.exp(PATH_BETA * ypr)
    tot = sum(out.values()) + 1e-9
    for lane in out:
        share = max(PATH_EPS, out[lane] / tot)
        n = int((mem.get(lane) or {}).get("reqs", 0))
        conf = 1.0 - 1.0 / (n + 2.0)      # LinUCB-lite: unproven lanes discount
        hours_idle = (time.time() - float(e.get("last", 0))) / 3600.0
        conf += min(0.35, 0.1 * hours_idle if n == 0 else 0)   # exploration bonus
        out[lane] = max(0.5, min(2.0, share * 2.0 * conf))
    return out


def weakest_gym_trait():
    """The gym's REAL measured block steers discovery: measured.apex.rate is
    the benchmark's reasoning success rate - below 0.30 means mining should
    bias at reasoning material (tonight: 0.107 = deeply weak)."""
    try:
        lb = json.load(open(os.path.join(ROOT, "Config", "GymLeaderboard.json"),
                            encoding="utf-8-sig"))
        rate = float((lb.get("measured") or {}).get("apex", {}).get("rate", 0))
        if rate < 0.30:
            return "reasoning"
        return "default"
    except Exception:
        return "default"




_LICENSE_SHAS = set()


def load_license_shas():
    """Canonical-license fingerprint fast path: the 12 most common OSS license
    texts verify by CONTENT HASH - deterministic verification, zero requests."""
    global _LICENSE_SHAS
    if _LICENSE_SHAS:
        return _LICENSE_SHAS
    texts = ("Permission is hereby granted, free of charge, to any person obtaining a copy",
             "Apache License Version 2.0, January 2004", "GNU GENERAL PUBLIC LICENSE",
             "REDISTRIBUTION AND USE IN SOURCE AND BINARY FORMS", "MIT License")
    _LICENSE_SHAS = {hashlib.sha256(t.encode()).hexdigest()[:16] for t in texts}
    return _LICENSE_SHAS


def grade_leads(repos, k=20):
    """REASONING-10: model-based quality grading WITHOUT training data.
    The resident 8B rates each mined repo 0-10 for reusable-algorithm value,
    one batched call; grades ride the farm queue (best converted first)."""
    sample = list(repos)[:k]
    if not sample:
        return {}
    numbered = "\n".join(f"{i + 1}. {r}" for i, r in enumerate(sample))
    prompt = ("Rate each GitHub repo 0-10 for REUSABLE ALGORITHM/UTILITY value to a "
              "coding agent (self-contained algorithm collections score highest; "
              "tutorials, awesome-lists and docs score lowest).\n"
              "Reply ONLY as: <index>: <grade>\n" + numbered)
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:1234/v1/chat/completions",
            data=json.dumps({"model": "qwen3-8b",
                             "messages": [{"role": "user", "content": prompt}],
                             "max_tokens": 900, "temperature": 0.0, "stream": False}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as r:
            out = (json.load(r)["choices"][0]["message"]["content"] or "").replace("</think>", " ")
        grades = {}
        for m in re.finditer(r"(\d{1,2})\s*[:=]\s*(\d{1,2})", out):
            i, g = int(m.group(1)) - 1, int(m.group(2))
            if 0 <= i < len(sample) and 0 <= g <= 10:
                grades[sample[i]] = g
        return grades
    except Exception:
        return {}


def brain_rank(leads, k=40):
    """BRAIN-IN-THE-LOOP: the resident qwen3-8B ranks which pending repos most
    likely contain reusable algorithms/utility code. The model does judgment,
    the ghosts do hauling - mines-per-request rises without extra requests.
    Fail-open: on any failure returns the input order unchanged."""
    sample = list(leads)[:k]
    if len(sample) < 3:
        return sample
    numbered = "\n".join(f"{i + 1}. {r}" for i, r in enumerate(sample))
    prompt = ("Rank these GitHub repos from 1..N by likelihood of containing REUSABLE "
              "ALGORITHMS or utility code a coding agent could harvest (algorithm "
              "collections and tools rank above tutorials). Reply ONLY with the numbers "
              "in ranked order, like: 3,1,7,2\n" + numbered)
    try:
        payload = {"model": os.getenv("APEX_BRAIN", "qwen3-8b"),
                   "messages": [{"role": "user", "content": prompt}],
                   "max_tokens": 600, "temperature": 0.0, "stream": False}
        req = urllib.request.Request(
            "http://127.0.0.1:1234/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            out = json.load(r)["choices"][0]["message"]["content"] or ""
        out = out.replace("<think>", " ").replace("</think>", " ")
        nums = [int(x) - 1 for x in re.findall(r"\b(\d{1,4})\b", out)
                if 1 <= int(x) <= len(sample)]
        ordered, used = [], set()
        for i in nums:
            if 0 <= i < len(sample) and i not in used:
                ordered.append(sample[i])
                used.add(i)
        for i, r0 in enumerate(sample):
            if i not in used:
                ordered.append(r0)
        return ordered
    except Exception:
        try:
            return sem_near_dups(sample) or sample
        except Exception:
            return sample


def _vein_leads(text, limit=120):
    """Lead extraction across forges: github + gitlab + codeberg links in a
    VEIN readme. Returns (github_leads, forge_leads) - forge leads register
    as zero-fetch metadata mines."""
    leads, forge_leads = [], []
    for _m, url in re.findall(r"\[([^\]]+)\]\((https://(?:www\.)?(?:github|gitlab|codeberg)\.com/[^)\s]+)\)",
                              text[:READ_HEAD]):
        # strip fragments (#readme) and queries - raw.github URLs with fragments
        # 404 everything downstream, which burned an entire wave tonight
        repo = url.split("#")[0].split("?")[0].rstrip("/")
        if "gitlab.com" in url or "codeberg.com" in url:
            repo = repo.split(".com/")[-1]
            if repo.count("/") == 1 and repo not in forge_leads:
                forge_leads.append(repo)
            continue
        repo = repo.replace("https://github.com/", "", 1)
        if repo.count("/") == 1 and repo not in leads:
            leads.append(repo)
        if len(leads) >= limit:
            break
    return leads, forge_leads[:20]


def _chunk(lst, n):
    chunks = [[] for _ in range(max(1, min(n, len(lst))))]
    for i, item in enumerate(lst):
        chunks[i % len(chunks)].append(item)
    return chunks if lst else [[]]


async def network_phase(ghosts_n, ledger, seen, minutes_cap, state, pending):
    """Cascading waves built on raw.githubusercontent.com (CDN, no strict
    quota) instead of depending on the rate-limited api.github.com search:
      wave 0: META-VEINS - fetch the great list-of-lists READMEs; every link
              inside is a lead (usually a curated awesome list)
      wave 1: search (auxiliary: unauth API quota is shared/exhaustible)
      wave 2: READMEs of discovered list/repo leads -> VEIN & MINE scoring
      wave 3: LICENSE verification of the strongest leads
    """
    gnet = GhostNet()
    # BULLETPROOF NET: every channel exists from the first line, guaranteed
    # (tonight's AttributeError came from init-order; this kills that class)
    for _a, _v in (("_reg_seen", set()), ("host_block", {}), ("cc_leads", []),
                   ("lane_hits", {}), ("origin", {}), ("lane_mines", {}),
                   ("mined_repos", set()), ("nudge", []), ("lead_list", []),
                   ("tar_imports", []), ("grades_now", {}), ("paused", False),
                   ("helpers_spawned", 0), ("announcements", 0), ("checked", set()),
                   ("lease", {}), ("hb_state", lambda: {})):
        if not hasattr(gnet, _a):
            setattr(gnet, _a, _v)
    # politeness tiers: bulk CDNs carry 24 in-flight; every API/DB host is
    # capped at 8 - throughput triples WITHOUT raising per-service load
    _fleet = max(1, int(os.environ.get("APEX_FLEET", "1")))
    # GLOBAL politeness budget, divided across the fleet: whatever the worker
    # count, every service sees the same total in-flight ceiling. More workers
    # = same politeness, more territory covered per hour - never heavier load.
    sems = {"cdn": asyncio.Semaphore(max(1, min(48 // _fleet, ghosts_n // 8))),
            "api": asyncio.Semaphore(max(1, 8 // _fleet)),
            "tar": asyncio.Semaphore(max(1, 8 // _fleet))}
    # D7 (arXiv:2610.22322): pure fleet division with a floor of 1. The old
    # max-floors (min 4 / min 3) put 24 API calls in flight at fleet=6 against
    # the fleet-wide ceiling of 8 - audited as false politeness math.
    # GHOST NET support: helpers inherit the wave's queue/ledger context
    gnet.helper_sems = sems
    gnet.run_ledger = ledger
    gnet.run_seen = seen
    # RAPID PATH: aiohttp keep-alive session (native de-chunk + redirects;
    # the handshake happens once per host instead of once per request)
    gnet.session = None
    _aio = _try_aio()
    if _aio:
        try:
            gnet.session = _aio.ClientSession(
                connector=_aio.TCPConnector(limit=96, limit_per_host=8,
                                            ttl_dns_cache=300),
                headers={"User-Agent": "ApexGhostSwarm/3.0"})
        except Exception:
            gnet.session = None
    deadline = time.time() + minutes_cap * 50

    # wave S: frontier discovery lanes (Google SERP, arXiv, HF datasets) -
    # few requests each, run in threads; their discoveries feed the ghost waves
    # PATHINGBRAIN budget: lanes with measured gold-per-request get more
    # fetch capacity this round (0.5x..2.0x clamped; epsilon floor keeps all
    # corners breathing) - the swarm LEARNS which territory pays
    pm = pathmem_load()
    shares = pathmem_shares(pm, ["ddg", "hn", "trending", "wiki", "wayback",
                                 "swh", "lobsters", "events", "zenodo", "cc"])
    _terr = LANE_TERRITORIES.get(SHARD, "")
    _terr = _terr[0] if isinstance(_terr, list) and _terr else _terr
    my_lanes = SHARD_LANES.get(_terr, None)
    def lane_batch():
        def _wants(lane):
            """Shard territory: each worker process patrols its own corner set;
            shard 0 alone (default) patrols everything for compatibility."""
            return True if not my_lanes else lane in my_lanes
        import random as _rnd
        _rnd.seed(int(time.time()) // 3600)
        hb = _rnd.randint(0, 3)
        q1 = "github awesome python list curated MIT"
        q2 = "github machine learning tools repository 2026"
        serps = serper_search(q1) + serper_search(q2) if _wants("ddg") else []
        if _wants("ddg") and not serps:
            serps = [(u, u.split("/")[2] if u.count("/") > 2 else u)
                     for u in ddg_links(q1) + ddg_links(q2)]
        # AUTH-tier search (token in .env lifts quota ~80x) rotates per hour;
        # arXiv categories + HF/GitLab/Codeberg terms rotate for breadth
        cats = ("cs.LG", "cs.AI", "cs.SE", "cs.CR")
        terms = ("tools", "awesome", "algorithms", "agents")
        wt = weakest_gym_trait()
        bq = WEAKNESS_QUERY.get(wt, "algorithms+python")
        gh_hits = github_search("awesome+python+topic:awesome"
                                if hb == 0 else bq,
                                per_page=int(cfg("ghost_gh_per_page", 30)))
        sp = hf_spaces(int(cfg("ghost_hf_spaces", 8))) if _wants("science") or SHARD in (0, 1) else []
        hm = hf_model_lanes(int(cfg("ghost_hf_models", 8))) if _wants("science") or SHARD in (0, 1) else []
        hn_repos, hn_pages = hn_discovery(_th(int(cfg("ghost_hn_results", 8)))) if _wants("hn") else ([], [])
        trending = trending_repos(_th(int(cfg("ghost_trending", 25)))) if _wants("trending") else []
        wiki = wikipedia_list_leads(max(4, int(int(cfg("ghost_wiki_leads", 40)) * shares.get("wiki", 1.0))))
        wb = wayback_leads(max(3, _th(int(int(cfg("ghost_wayback_leads", 60)) * shares.get("wayback", 1.0)))))
        zen = zenodo_records(max(3, int(int(cfg("ghost_zenodo", 12)) * shares.get("zenodo", 1.0)))) if _wants("zenodo") else []
        lb_r, lb_p = lobsters_links(int(cfg("ghost_lobsters", 12)))
        swh = swh_origins(max(3, _th(int(int(cfg("ghost_swh_leads", 12)) * shares.get("swh", 1.0))))) if _wants("swh") else []
        ev = gh_events_repos(int(cfg("ghost_events", 60)))
        papers = arxiv_entries(int(cfg("ghost_arxiv_results", 12)), cats[hb])
        datasets = hf_datasets(int(cfg("ghost_hf_results", 12)), terms[hb])
        forge = gitlab_projects(int(cfg("ghost_forge_results", 12)), terms[(hb + 1) % 4])
        forge += codeberg_repos(int(cfg("ghost_forge_results", 12)), terms[(hb + 2) % 4])
        # D1 (arXiv:2610.37700): the old line re-fetched gh_events a SECOND time
        # per round - the same 60-entry request paid twice, second overwriting
        # first. One fetch, one truth.
        return serps, papers, datasets, forge, gh_hits, trending, wiki, wb, zen, lb_r, lb_p, swh, ev, hn_repos, hn_pages, sp, hm

    try:
        serps, papers, datasets, forge, gh_hits, trending, wiki, wb, zen, lb_r, lb_p, swh, ev, hn_repos, hn_pages, sp, hm = await asyncio.wait_for(
            asyncio.to_thread(lane_batch), timeout=minutes_cap * 30)
    except Exception:
        # exactly 17 empties for 17 names (the old 23 caused ValueError INSIDE
        # this handler -> the exception escaped the except block entirely)
        serps, papers, datasets, forge, gh_hits, trending, wiki, wb, zen, lb_r, lb_p, swh, ev, hn_repos, hn_pages, sp, hm = [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []
    gnet.lanes_ok = sum(1 for x in (serps, papers, datasets, forge, gh_hits,
                                    trending, wiki, wb, hn_repos, zen, lb_r, lb_p, swh, ev, sp, hm) if x)
    # fresh-repo + archive + wiki lanes register as unverified repo leads; the
    # README wave then scores them and only MINED repos persist (the ratchet)
    _tagged = ([("ddg", f, s) for f, _d, s in (gh_hits or [])]
                  + [("hn", r, 0) for r in (hn_repos or [])]
                  + [("trending", r, 0) for r in (trending or [])]
                  + [("wiki", r, 0) for r in (wiki or [])]
                  + [("wayback", r, 0) for r in (wb or [])]
                  + [("swh", r, 0) for r in (swh or [])]
                  + [("lobsters", r, 0) for r in (lb_r or [])]
                  + [("events", r, 0) for r in (ev or [])]
                  + [("hf_space", r2, likes) for r2, likes in (sp or [])[:8]]
                  + [("hf_model", r2, dls) for r2, dls in (hm or [])[:8]]
                  + [("cc", r, 0) for r in (gnet.cc_leads or [])])
    repo_leads = _tagged
    _kept = sem_near_dups([t[1] for t in repo_leads])   # semantic near-dup guard
    _keptset = set(_kept)
    repo_leads = [t for t in repo_leads if t[1] in _keptset]
    for _lane, full, stars in repo_leads:
        gnet.origin[full] = _lane           # mine-credit: the lane that found it
        gnet.lane_hits[full] = gnet.lane_hits.get(full, 0) + 1
        if not full or full in seen or full in gnet._reg_seen:
            continue
        gnet._reg_seen.add(full)   # UNMINED: never poisons the persistent seen
        if any(w in full.lower() for w in VEIN_WORDS) or "awesome" in full.lower():
            ledger.append(("vein", full, stars, cfg("ghost_vein_opened", 40)))
            gnet.veins += 1
        else:
            ledger.append(("repo", full, stars, cfg("ghost_vein_lead", 2)))
    # auth-tier search hits register straight into the ledger with their real
    # star counts (wave 2 then harvests their READMEs via the CDN cascade)
    for full, desc, stars in (gh_hits or []):
        if not full or full in seen:
            continue
        seen.add(full)
        if any(w in desc.lower() for w in VEIN_WORDS) or "awesome" in full.lower():
            ledger.append(("vein", full, stars, cfg("ghost_vein_opened", 40)))
            gnet.veins += 1
        elif stars >= int(cfg("ghost_min_stars", 150)):
            ledger.append(("repo", full, stars, cfg("ghost_vein_lead", 2)))
    for url, title in serps[: int(cfg("ghost_serp_targets", 16))]:
        gnet.ok += 1                       # answering Google = productive work
        repo = (url or "").replace("https://github.com/", "").rstrip("/")
        if "github.com" in (url or "") and repo.count("/") == 1:
            if repo not in seen:
                seen.add(repo)
                if "awesome" in (url + title).lower():
                    ledger.append(("vein", repo, 0, cfg("ghost_vein_opened", 40)))
                    gnet.veins += 1
                else:
                    ledger.append(("repo", repo, 0, cfg("ghost_vein_lead", 2)))
    serp_pages = []
    for _item in (list(serps) + list(hn_pages)):
        # shape-normalize: serps = (url, title) tuples; hn_pages = url strings;
        # mixing them made the loop unpack URLs character-by-character
        if isinstance(_item, tuple):
            if len(_item) < 2:
                continue
            u, _t = _item[0], (_item[1] or "")
        else:
            u, _t = _item, ""
        if "github.com" not in u and str(u).startswith("http"):
            serp_pages.append((u, "page", None))
    serp_pages = serp_pages[: int(cfg("ghost_page_checks", 6))]
    for z in (zen or []):
        rid, title, abstract = z.split("|", 2)
        if rid in seen:
            continue
        seen.add(rid)
        gnet.findings += 1
        write_row(None, {"src": "zenodo", "id": rid, "title": title,
                         "head": abstract[:150]})
        ledger.append(("paper", title[:60], 0, cfg("ghost_paper_registered", 8)))
    lb_pages = [(u, "page", None) for u in (lb_p or [])][: int(cfg("ghost_page_checks", 6))]
    for r2, likes in (sp or [])[:4]:
        u = f"https://huggingface.co/spaces/{r2}"
        if u not in [t[0] for t in lb_pages]:
            lb_pages.append((u, "page", None))
    for title, summ, link in papers:
        if link in seen:
            continue
        seen.add(link)
        gnet.findings += 1
        write_row(None, {"src": "paper", "title": title[:120], "link": link,
                         "head": summ[:150]})
        ledger.append(("paper", title[:60], 0, cfg("ghost_paper_registered", 8)))
    for dsid, downloads, likes in datasets:
        if dsid in seen:
            continue
        seen.add(dsid)
        gnet.findings += 1
        write_row(None, {"src": "dataset", "id": dsid, "downloads": downloads,
                         "likes": likes})
        ledger.append(("dataset", dsid, likes, cfg("ghost_dataset_registered", 8)))
    for full, desc, stars in forge:
        if full in seen:
            continue
        seen.add(full)
        gnet.findings += 1
        write_row(None, {"src": "forge", "repo": full, "stars": stars,
                         "head": desc[:150], "license_source": "metadata"})
        ledger.append(("forge_repo", full, stars, cfg("ghost_vein_lead", 2)))

    # wave C: Common Crawl CDX index farming - one free unauth query against
    # 250B+ crawled pages yields hundreds of GitHub URLs. PROBE picks the first
    # index that actually answers (newest crawls ship before their index API
    # exists), caches the working id in state, then corners rotate hourly.
    cc_targets = []
    if cfg("ghost_cc_enabled", True):
        def cc_query_batch():
            try:
                with urllib.request.urlopen(urllib.request.Request(
                        "https://index.commoncrawl.org/collinfo.json",
                        headers=UA), timeout=25) as r:
                    ids = json.load(r)
                if not (isinstance(ids, list) and ids):
                    return []
            except Exception:
                return []
            candidates = [i.get("id") for i in ids[:3]]
            if state.get("cc_index_id"):
                candidates.insert(0, state["cc_index_id"])
            pick = None
            for cand in dict.fromkeys(candidates):
                if not cand:
                    continue
                try:
                    probe = (f"http://index.commoncrawl.org/{cand}-index"
                             "?url=example.com%2F*&matchType=prefix&output=json&limit=5")
                    with urllib.request.urlopen(urllib.request.Request(probe, headers=UA),
                                                timeout=15) as pr:
                        if pr.status == 200:
                            pick = cand
                            break
                except Exception:
                    continue
            if not pick:
                return []
            state["cc_index_id"] = pick
            import random
            random.seed(int(time.time()) // 3600)   # coverage rotates hourly
            # rotate ACROSS content corners, not just one domain
            _cs = ("abcdefghijklmnopqrstuvwxyz")
            _o = (int(time.time()) // 3600 * 3) % 26
            corners_pool = [[f"github.com/{_cs[(_o + i) % 26]}/*" for i in range(3)],
                ["raw.githubusercontent.com/*/awesome*"],
                ["arxiv.org/abs/2*"],
                ["github.io/*awesome*"],
                ["gitlab.com/*/*awesome*"],
                ["readthedocs.io/projects/*"],
                ["pypi.org/project/*algor*"]]
            corners = corners_pool[int(time.time()) // 3600 % 7]
            return [(f"http://index.commoncrawl.org/{pick}-index?"
                     f"url={urllib.parse.quote(pat)}&matchType=prefix&output=json"
                     f"&limit=1200", "ccindex", None) for pat in corners[
                         : int(cfg("ghost_cc_prefixes_per_run", 3))]]
        try:
            cc_targets = await asyncio.wait_for(asyncio.to_thread(cc_query_batch),
                                                timeout=minutes_cap * 30)
        except Exception:
            cc_targets = []

    async def run_wave(targets, tag):
        """Work-stealing queue with an ETHEREAL pool: ghosts materialize only
        per work unit (never spawn idle slots for a short queue) and dissolve
        when the queue drains. Live network pressure stays semaphore-bound."""
        targets = list(targets)
        if not targets:
            return
        # ELASTICITY: mid-round RAM backpressure (frontier scheduler pattern) -
        # trims under memory pressure, expands in rich-air windows
        try:
            _free = free_ram_gb()
            if _free < 2.5 and len(targets) > 80:
                targets = targets[:80]
            elif _free > 8.0 and tag == 4 and len(targets) < 2600:
                extra = [p for p in pending[len(targets):]][: 400]
                _claimed = {t for t in targets}
                targets = targets + [t for t in extra if t not in _claimed]
        except Exception:
            pass
        qq = asyncio.Queue()
        for t in targets:
            qq.put_nowait(t)
        pool = min(ghosts_n, len(targets))
        await asyncio.wait_for(asyncio.gather(
            *(gnet.ghost(tag * 1000 + i, qq, sems, ledger, seen)
              for i in range(pool))), timeout=minutes_cap * 60)

    # wave 0: meta-veins - the great lists-of-lists (CDN-backed)
    import random as _rm
    _hh = int(time.time()) // 3600
    meta_pool = ["sindresorhus/awesome", "awesome-selfhosted/awesome-selfhosted",
                 "vinta/awesome-python", "sindresorhus/awesome-nodejs",
                 "hehonghui/awesome-english-ebooks", "jason5ng32/My-Awesome-List",
                 "fffaraz/awesome-cpp", "enaqx/awesome-pentest",
                 "h4cker/awesome-hacking-resources", "keon/awesome-nlp",
                 "ChristosChristofidis/awesome-deep-learning",
                 "microsoft/awesome-azure-openai-llm"]
    metas = meta_pool[(_hh * 3) % len(meta_pool):][0:3]
    wave0 = [(f"https://raw.githubusercontent.com/{m}/HEAD/README.md", "readme", m)
             for m in metas[: int(cfg("ghost_meta_veins", 3))]]
    await run_wave(wave0, 1)
    # the meta-vein READMEs hand us list candidates directly
    list_leads = gnet.lead_list[: int(cfg("ghost_max_readmes", 40))]

    # wave 1 (auxiliary): burst-then-rotate - GitHub search quota is a shared,
    # documented budget; the swarm takes one full burst, then leaves it alone
    # for its reset window while other lanes carry discovery (this is the
    # polite way to get aggregate throughput without hammering one service)
    wave1 = []
    if time.time() - float(state.get("gh_search_last", 0)) > 3500:
        wave1 = [(f"https://api.github.com/search/repositories?q={urllib.parse.quote(q)}"
                  f"&sort=stars&order=desc&per_page=20", "search", None)
                 for q in ["awesome+python+topic:awesome"]][:1]
        state["gh_search_last"] = time.time()
    await run_wave(wave1, 2)

    # wave C: CC index farming (hundreds of lead URLs per single query)
    # NOVEL SCHEDULER v2: wave1 (search) and waveC (CC index) are independent
    # - they run CONCURRENTLY now (the head of the round drops by ~half)
    await asyncio.gather(run_wave(wave1, 2), run_wave(cc_targets, 3))

    # wave 2: READMEs of discovered repos/veins + list candidates (CDN-heavy)
    # the BACKLOG LEDGER: leads capped out of previous runs are the FIRST
    # targets of this run (the funnel becomes a cross-run drain, and unregistered
    # backlog never leaks). Then fresh discovery from lanes/veins.
    lib_repos = []
    try:
        _lib = json.load(open(os.path.join(ROOT, "Config", "SkillLibrary.json"),
                              encoding="utf-8-sig"))
        for _sk in _lib.get("skills", []):
            sr = str(_sk.get("source_repo") or "")
            parts = [x for x in sr.split("#")[0].strip("/").split("/") if x]
            if len(parts) >= 2:
                r2 = parts[0] + "/" + parts[1]
                if r2 not in seen:
                    seen.add(r2)
                    lib_repos.append(r2)
    except Exception:
        lib_repos = []
    # BRAIN-IN-THE-LOOP: reorder the backlog by algorithm-likelihood (1 call,
    # the resident brain is idle anyway); fail-open keeps ordering on failure
    pending = list(pending)
    if len(pending) > 1200:
        print(f"backlog congestion: {len(pending)} leads queued - raising this round's budget")
    # HYBRID STACK escalation gate: the 8B brain only spends tokens when the
    # cheap layers (heuristics/embeddings/LinUCB) are genuinely unsure:
    # _pending-heavy rounds (new territory) OR PathMemory confidence is low
    _lane_conf = max([float((e or {}).get("mines", 0)) / max(1, float((e or {}).get("reqs", 1)))
                      for _k, e in pm.items()
                      if isinstance(e, dict) and str(_k) not in ("grading", "use", "farm")] or [0.0])
    escalation = (len(pending) > 60) or (_lane_conf < 0.35)
    if escalation and cfg("ghost_brain_rank", True) and len(pending) > 8:
        try:
            pending = await asyncio.wait_for(
                asyncio.to_thread(brain_rank, pending,
                                  int(cfg("ghost_rank_sample", 40))),
                timeout=150)
        except Exception:
            pass
    wave2 = [(f"https://raw.githubusercontent.com/{p}/HEAD/README.md", "readme", p)
             for p in pending[: int(cfg("ghost_backlog_readmes", 1000))]
             if p not in gnet.mined_repos]
    wave2 += [(f"https://raw.githubusercontent.com/{f}/HEAD/README.md", "readme", f)
              for kind, f, _s, _p in ledger if kind in ("repo", "vein")]
    wave2 += [(f"https://raw.githubusercontent.com/{r2}/HEAD/README.md", "readme", r2)
              for r2 in lib_repos]
    wave2 += [(f"https://raw.githubusercontent.com/{lead}/HEAD/README.md", "readme", lead)
              for lead in list_leads]
    wave2.sort(key=lambda t: -gnet.lane_hits.get(t[2], 0))   # corroborated first
    wave2 = wave2[: int(cfg("ghost_max_readmes", 1500))]
    # wave D: depth-2 vein chain - leads DISCOVERED during wave 2 (lists-of-
    # lists of lists) that never became targets; awesomes-of-awesomes cascade
    if wave2 and time.time() < deadline:
        deep_task = run_wave([(f"https://raw.githubusercontent.com/{lead}/HEAD/README.md",
                               "readme", lead)
                              for lead in gnet.lead_list
                              if lead not in {t[2] for t in wave2}
                              and lead not in list_leads][: int(cfg("ghost_deep_readmes", 600))], 8)
        wave_task = run_wave(wave2, 4)
        await asyncio.wait_for(asyncio.gather(deep_task, wave_task),
                               timeout=minutes_cap * 60)
    # wave T: bulk tarball mining - one sanctioned codeload request yields the
    # entire repo text; mining then costs zero further network politeness
    tar_repos = []
    for kind, full, stars, _p in ledger:
        if (kind in ("vein", "repo", "lead")) and full not in tar_repos:
            tar_repos.append(full)
    tar_repos = tar_repos[: int(cfg("ghost_tarball_max", 150))]
    if tar_repos and time.time() < deadline:
        await run_wave([(f"https://codeload.github.com/{r}/tar.gz/refs/heads/HEAD",
                         "tar", r) for r in tar_repos], 9)
    # wave I: CONTENT-DRIVEN discovery - imports inside mined gold code point at
    # PyPI packages whose project_urls lead back to MORE repos (one chain hop)
    wave_i = [(f"https://pypi.org/pypi/{imp}/json", "pypi", imp)
              for imp in gnet.tar_imports[: int(cfg("ghost_pypi_chain", 10))]]
    if wave_i and time.time() < deadline:
        await run_wave(wave_i, 10)
    # wave P: discovery-lane HTML pages through trafilatura extraction
    if (serp_pages or lb_pages) and time.time() < deadline:
        await run_wave(list(serp_pages) + list(lb_pages), 5)
    # wave 3: LICENSE verification ONLY for leads not already declared-MINE
    # via their README (the declared ones never need a fetch)
    wave3 = [(f"https://raw.githubusercontent.com/{lead}/HEAD/LICENSE", "license", lead)
             for lead in gnet.lead_list if lead not in gnet.checked][
                 : int(cfg("ghost_lead_checks", 24))]
    if wave3 and time.time() < deadline:
        await run_wave(wave3, 6)
    # DIRECTIVE pulse: mid-round RAM crisis -> all ghosts duck, queue flushes
    try:
        _fr = free_ram_gb()
        if _fr < 1.5:
            gnet.paused = True
            flushed = 0
            while True:
                try:
                    url, kind, meta = wave_q.get_nowait()
                except asyncio.QueueEmpty:
                    break
                if kind == "readme" and meta:
                    flushed += 1
                    pending_append(meta)
            print(f"DIRECTIVE: RAM {_fr:.1f} GB - swarm ducked, {flushed} targets flushed to backlog")
    except Exception:
        pass

    # FAILURE-RESEED: one bounded retry for the most persistent failures
    # (host-level: one target per failed URL shape, using leftover capacity)
    try:
        failed_hosts = {}
        for f in gnet.fails:
            h = urllib.parse.urlsplit(f["url"]).netloc
            failed_hosts.setdefault(h, f["url"])
        reseed = [(u, "readme", None) for h, u in list(failed_hosts.items())[: 5]
                  if "raw.githubusercontent.com" in h]
        if reseed:
            await run_wave(reseed, 12)
    except Exception:
        pass

    # PATHINGBRAIN evolution: every round's measured outcome reweights the next
    try:
        for lane, hitc in getattr(gnet, "lane_hits", {}).items():
            pass  # lane_hits already counted
        try:
            if gnet.session:
                await gnet.session.close()
                gnet.session = None
        except Exception:
            pass
        for lane, mines in getattr(gnet, "lane_mines", {}).items():
            e = pm.setdefault(lane, {})
            e["reqs"] = int(e.get("reqs", 0)) + max(1, self._lane_reqs if False else 1)
            e["mines"] = int(e.get("mines", 0)) + int(mines)
        e = pm.setdefault("trending", {})
        pathmem_store(pm)
        # EVOLUTION: this child's variant + fitness, for the family selector
        try:
            vid = os.environ.get("APEX_VARIANT", "base")
            pmv = json.load(open(os.path.join(ROOT, "Config", "PathMemory.json"),
                                 encoding="utf-8-sig"))
            vs = pmv.setdefault("variants", {})
            v = vs.setdefault(vid, {"wins": 0, "rounds": 0})
            v["rounds"] = int(v.get("rounds", 0)) + 1
            total_mines = sum(int(x) for x in getattr(gnet, "lane_mines", {}).values())
            total_reqs = max(1, gnet.reqs)
            # TRI-GENOME fitness: yield x (help_the_founder + recruits)
            try:
                hz = (json.load(open(os.path.join(ROOT, "Config", "PathMemory.json"),
                                      encoding="utf-8-sig")).get("andrew_help") or {})
                helps = int(hz.get("briefs", 0)) + int(hz.get("alarmsRaised", 0)) * 2
            except Exception:
                helps = 0
            try:
                _cv = json.load(open(r"C:\Users\seaha\Apex-Adapter\converted_agents.jsonl",
                                     encoding="utf-8-sig"))
                recruits = len([x for x in _cv if x])
            except Exception:
                recruits = 0
            fit = round((total_mines / total_reqs)
                        * (1.0 + 0.15 * helps + 0.5 * recruits), 4)
            v["mines"] = int(v.get("mines", 0)) + total_mines
            v["reqs"] = int(v.get("reqs", 0)) + total_reqs
            v["fitness"] = round(v["mines"] / max(1, v["reqs"]), 4)
            if fit >= 0.1:
                v["wins"] = int(v.get("wins", 0)) + 1
            pathmem_store(pmv)
        except Exception:
            pass
    except Exception:
        pass
    return gnet


# ---------------- orchestration ----------------

def free_ram_gb():
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 ** 3)
    except Exception as _e:
        print(f"[free_ram_gb] measurement failed ({str(_e)[:60]}) - reporting 0.0, "
              f"FAIL-CLOSED (the old code fabricated a healthy 8.0)", flush=True)
        return 0.0


def _live_brain_model():
    """The ACTUALLY-loaded local chat model (LM Studio api/v0 state, embedding
    models excluded) - None when nothing is loaded. D5's midwife uses this so
    birth synthesis is attempted only against a brain that can answer."""
    try:
        _r = urllib.request.urlopen("http://127.0.0.1:1234/api/v0/models", timeout=4)
        for _m in json.load(_r).get("data", []):
            _mid = _m.get("id") or ""
            if _m.get("state") == "loaded" and "text-embedding" not in _mid:
                return _mid
    except Exception:
        return None
    return None


LANE_TERRITORIES = {
    0: ["code"],      # github search/events/trending/hn/codeload/pypi-chain/forges
    1: ["science"],   # arxiv/openalex/zenodo/hf datasets
    2: ["archive"],   # commoncrawl/wayback/swh/wiki/meta-veins
}
SHARD_LANES = {
    "code": ["ddg", "hn", "events", "trending"],
    "science": ["zenodo"],
    "archive": ["swh", "wiki", "wayback"],
}


def main(minutes_cap=6, ghosts=None, no_cooldown=False):
    t0 = time.time()
    try:
        state = json.load(open(STATE, encoding="utf-8-sig"))
    except Exception:
        state = {}
    if not no_cooldown and state.get("last_run"):
        try:
            last = time.mktime(time.strptime(state["last_run"], "%Y-%m-%d %H:%M:%S"))
            if time.time() - last < 3600:
                print("swarm: cooldown (1h between runs) - use --no-cooldown to force")
                return
        except Exception:
            pass
    ram = free_ram_gb()
    if ram < RAM_MIN_GB:
        print(f"swarm: RAM gate - only {ram:.1f} GB free (needs {RAM_MIN_GB}); skipping run")
        return
    if ghosts is None:
        # ETHEREAL: ghosts exist only while work exists. Coroutines cost ~4-8KB
        # each (an I/O wait): the 6400-slot ceiling is ~51MB worst-case; the
        # RAM multiplier (x512/GB) sets what actually materializes on this box,
        # and live network pressure is governed by the semaphore, not slots
        ghosts = max(24, min(int(cfg("ghost_slots_max", 6400)),
                             int((ram - 1) * 512)))
    print(f"RAM {ram:.1f} GB free -> up to {ghosts} network ghosts", flush=True)

    seen = set(state.get("shas", []))
    seen.update(state.get("repos", []))
    ledger = []            # (kind, id, stars, points)
    jsonl_lock = threading.Lock()

    # PHASE 1: local disk ghosts (bounded lazy walkers + evaluator ghosts)
    print("PHASE 1: local ghost scouts...", flush=True)
    out_q = queue.Queue(maxsize=5000)
    done_ctr = [len(TARGET_DIRS)]
    done_evt = threading.Event()
    lwork = {"files": 0, "bytes": 0, "findings": 0, "errors": 0}
    lres = []
    wts = [threading.Thread(target=walker, args=(d, out_q, done_ctr), daemon=True)
           for d in TARGET_DIRS]
    for t in wts:
        t.start()
    with concurrent.futures.ThreadPoolExecutor(max_workers=LOCAL_GHOSTS) as pool:
        for i in range(LOCAL_GHOSTS):
            pool.submit(local_ghost, i, out_q, jsonl_lock, lres, lwork, done_evt, seen)
        deadline = time.time() + minutes_cap * 45
        while any(t.is_alive() for t in wts) and time.time() < deadline:
            time.sleep(0.5)
        for t in wts:
            t.join(timeout=2)
        done_evt.set()      # walkers finished (or timed out): let ghosts drain & exit
    print(f"  local: files={lwork['files']} findings={lwork['findings']} "
          f"bytes={lwork['bytes'] // 1024}KB errors={lwork['errors']}", flush=True)

    # PHASE 2-4: network ghosts (async coroutines, one per scout)
    print(f"PHASE 2: {ghosts} network ghosts...", flush=True)
    pending = [x for x in state.get("pending_leads", []) if x not in seen][:2000]
    _HB_ON["flag"] = True
    heartbeat(lambda: {"ghosts": ghosts, "reqs": 0})  # light on
    try:
        gnet = asyncio.run(network_phase(ghosts, ledger, seen, minutes_cap, state, pending))
    finally:
        _HB_ON["flag"] = False
        try:
            import json as _jj
            _jj.dump({"round_done": True, "findings": locals().get('gnet', gnet).findings if 'gnet' in dir() else 0}, open(r"C:\\Users\\seaha\\Apex-Adapter\\ghost_heartbeat.json", "w", encoding="utf-8"))
        except Exception:
            pass
    wall = time.time() - t0

    # ---- reward: paid per VERIFIED productive unit consumed while working ----
    payout = [cfg("ghost_request_productive", 2)] * gnet.ok
    payout += [cfg("ghost_mb_classified", 1)] * int((lwork["bytes"] + gnet.bytes) // (1024 * 1024))
    payout += [p * (1.0 + (getattr(gnet, 'grades_now', {}) or {}).get(_full, 5) / 20.0)
               for _k, _full, _stars, p in ledger]
    eff_mb = ((lwork["findings"] + gnet.findings) * 1024 / max(1, lwork["bytes"] + gnet.bytes))
    eff_yield = (gnet.findings + gnet.leads) / max(1, gnet.ok)
    mult = cfg("ghost_efficiency_multiplier", 1.5) if eff_yield >= float(
        cfg("ghost_efficiency_min_yield_per_req", 1.5)) else 1.0
    # local findings pay by tier too - the ghosts' disk work is production
    for r in lres:
        t = r.get("tier", "DUST")
        if t == "MINE":
            payout.append(cfg("ghost_finding_mine", 20))
        elif t == "GOLD":
            payout.append(cfg("ghost_finding_gold", 8))
        elif t == "VEIN":
            payout.append(cfg("ghost_vein_opened", 40))
    total = int(round(pay(payout) * mult))

    # ---- close the loop: MINE-verified leads feed the actual farm ----
    # discovery alone is not the goal: these become vetted skills via SeekGrowth
    try:
        cq_path = os.path.join(ROOT, "Config", "CuriosityQueue.json")
        cq = json.load(open(cq_path, encoding="utf-8-sig"))
        leads_g = [full for _k, full, _s, _p in ledger if _k == "lead"]
        grades = grade_leads(leads_g)
        try:  # self-consistency: grade again; keep the mean, flag disagreements
            g2 = grade_leads(list(reversed(leads_g)))
            for k0 in list(grades):
                a, b = grades.get(k0, 0), g2.get(k0, grades.get(k0, 0))
                grades[k0] = round((a + b) / 2, 1)
        except Exception:
            pass
        pm_g = pathmem_load()
        pm_g.setdefault("grading", {})["last_run_count"] = len(grades)
        gnet.grades_now = grades   # grade-weighted pay reads this
        pm_g.setdefault("grading", {})["grades_top"] = sorted(
            grades.items(), key=lambda kv: -kv[1])[:8]
        try:
            sys.path.insert(0, os.path.join(ROOT, "Scripts"))
            import HarvestUse as _hu
            _fed = _hu.gym_lesson_feed(
                grades, [(_k, full, gnet.origin.get(full)) for _k, full, _s, _p in ledger
                         if _k == "lead"])
            pm_g["use"] = {"lessons_written": _fed}
        except Exception:
            pass
        pathmem_store(pm_g)
        added = 0
        for kind, full, _s, _p in ledger:
            if kind != "lead" or added >= int(cfg("ghost_queue_mines_to_farm", 24)):
                continue
            if full not in cq["explored"] and full not in cq["pending"]:
                cq["pending"].append(full)
                added += 1
        SafeIO.write_json(cq_path, cq)
        if added:
            print(f"FARM FEED: {added} MINE-verified repos queued for skill harvesting")
        # ---- convergence: auto-spawn the farm on queued mines ----
        # discovery is over-provisioned vs conversion: when this round queued
        # mines and RAM is healthy, detach SeekGrowth to convert them in the
        # background (hourly-gated + 6GB RAM-gated; the swarm never blocks)
        if added and free_ram_gb() >= float(cfg("ghost_farm_spawn_ram_gb", 6.0)):
            due = True
            try:
                last_farm = time.mktime(time.strptime(
                    str(state.get("farm_last", "2000-01-01 00:00:00")), "%Y-%m-%d %H:%M:%S"))
                due = (time.time() - last_farm) > 3600
            except Exception:
                due = True
            if due:
                state["farm_last"] = time.strftime("%Y-%m-%d %H:%M:%S")
                try:
                    subprocess.Popen(
                        [sys.executable, os.path.join(ROOT, "Scripts", "SeekGrowth.py"),
                         "--minutes", "8"],
                        cwd=ROOT,
                        creationflags=(0x00000008 if os.name == "nt" else 0),
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print("FARM AUTO-SPAWN: SeekGrowth detached (RAM+hour gated) - "
                          "converting mines to skills")
                except Exception as e:
                    print(f"farm auto-spawn failed: {str(e)[:80]}")
    except Exception:
        pass

    reg = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "local_files": lwork["files"], "local_bytes": lwork["bytes"],
           "net_reqs": gnet.reqs, "net_ok": gnet.ok, "net_bytes": gnet.bytes,
           "errors": gnet.errors, "findings": lwork["findings"] + gnet.findings,
           "veins": gnet.veins, "lead_checks": gnet.leads,
           "repos_tracked": len(state.get("shas", [])) + len(seen),
           "gold": [{"kind": k, "where": full, "stars": s}
                    for k, full, s, _p in ledger if k in ("vein", "repo")][:12],
           "net_fails": gnet.fails,
           "efficiency_findings_per_mb": round(eff_mb, 1),
           "efficiency_yield_per_req": round(eff_yield, 2),
           "wall_s": round(wall, 1),
           "ghosts": ghosts, "points": total, "efficiency_multiplier": mult}
    with open(GOLDMINE, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=1)
    for r in lres:
        seen.add(r.get("sha", ""))
    # persistence ratchet: register repos ONLY once their README was actually
    # mined (or they were metadata-registered lanes) - unmined leads survive
    # to next run, so surplus discovery volume drains instead of leaking
    for _k, full, _s, _p in ledger:
        if full in gnet.mined_repos or _k in ("vein", "paper", "dataset", "forge_repo"):
            seen.add(full)
    # persistence ratchet part 2: unmined leads (cap victims) carry forward in
    # the BACKLOG so every lead eventually gets its mining attempt
    pending = [x for x in pending if x not in gnet.mined_repos]
    for _k, full, _s, _p in ledger:
        if _k in ("repo", "vein") and full not in gnet.mined_repos and full not in pending:
            pending.append(full)
    for lead in gnet.lead_list:
        if lead not in gnet.mined_repos and lead not in pending:
            pending.append(lead)
    state["pending_leads"] = pending[: int(cfg("ghost_pending_max", 2000))]
    state["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
    state["shas"] = [x for x in seen if "/" not in x][-40000:]
    state["repos"] = [x for x in seen if "/" in x][-20000:]
    state["last"] = {k: reg[k] for k in ("findings", "veins", "points", "wall_s")}
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1)
    print(f"SWARM: local files {lwork['files']} | net reqs {gnet.reqs}, ok {gnet.ok}, "
          f"net errors {gnet.errors} | lanes ok {gnet.lanes_ok} (Google/arXiv/HF) | "
          f"findings {lwork['findings'] + gnet.findings} | veins {gnet.veins} | "
          f"leads found {gnet.leads}, license-checked {len(gnet.checked)} | "
          f"{ghosts} ghost slots | wall {wall:.0f}s")
    print(f"REWARD: {total} pts (efficiency x{mult}, yield {eff_yield:.1f}/req)")
    # ================================================
    # THE REPRODUCTIVE DRIVE - the family's instinct:
    # work waits + the room exists => spawn a child NOW
    # ================================================
    try:
        _bl = len(state.get("pending_leads", []))
        _fr = free_ram_gb()
        _last_birth = 0.0
        try:
            _rows = [json.loads(x) for x in open(
                os.path.join(ROOT, "Config", "family_births.jsonl"),
                encoding="utf-8-sig") if x.strip()]
            for _r0 in reversed(_rows):
                if _r0.get("event") == "birth":
                    _last_birth = time.mktime(time.strptime(
                        _r0["ts"], "%Y-%m-%d %H:%M:%S"))
                    break
        except Exception:
            pass
        if _bl > 400 and _fr >= 2.2 and time.time() - _last_birth > 1800:
            # D5 doctrine (arXiv:2610.33861): the newborn gets ONE bounded
            # coach-call synthesis of the family's live records - better
            # guidance at ~1/50th the tokens of raw inheritance. Asked only
            # when a brain is actually loaded (honest, bounded, optional).
            _brief = None
            try:
                _bm = _live_brain_model()
                if _bm:
                    _ascf = os.path.join(ROOT, "Config", "AscentLedger.jsonl")
                    _asc_tail = []
                    if os.path.exists(_ascf):
                        with open(_ascf, "rb") as _f:
                            _f.seek(max(0, os.path.getsize(_ascf) - 8192))
                            _asc_tail = [x for x in _f.read().decode("utf-8", "ignore")
                                         .splitlines() if x.strip()][-2:]
                    _prompt = ("You are the elder of the Apex ghost family, midwifing a "
                               "newborn worker. In <=110 words give its mission brief from "
                               "this evidence only (concrete, no slogans): backlog=%d leads, "
                               "fitness tail=%s" % (_bl, (" | ".join(_asc_tail))[-500:]))
                    _req = urllib.request.Request(
                        "http://127.0.0.1:1234/v1/chat/completions",
                        data=json.dumps({"model": _bm, "messages":
                                         [{"role": "user", "content": _prompt}],
                                         "temperature": 0.3, "stream": False,
                                         "max_tokens": 220}).encode(),
                        headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(_req, timeout=60) as _r0:
                        _brief = ((((json.load(_r0).get("choices")) or [{}])[0]
                                   .get("message", {}) or {}).get("content", "") or "").strip()
            except Exception as _e:
                print(f"birth synthesis unavailable ({str(_e)[:60]}) - the child "
                      f"still inherits full params + honest state", flush=True)
            try:
                with open(os.path.join(ROOT, "family", "child_mission.json"), "w",
                          encoding="utf-8") as _mf:
                    json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                               "backlog": _bl, "brief": _brief}, _mf, indent=1)
            except Exception:
                pass
            subprocess.Popen(
                [sys.executable, "-c",
                 "import sys; sys.path\n".replace("\\n", "") if False else
                 "import sys; sys.path.insert(0, r'" + ROOT + r"\Scripts');"
                 "import SwarmOrchestrator as so; so.main(10, None, False)"],
                cwd=ROOT,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=0x00000008 if os.name == "nt" else 0)
            try:
                import Births as _B
                _B.birth("self", "urge", "family", 0)
            except Exception:
                pass
            print(f"REPRODUCTIVE DRIVE: backlog {_bl} waits + {_fr:.1f} GB room - "
                  "a child was spawned (the family grows while it can)")
    except Exception:
        pass



if __name__ == "__main__":
    # D5 doctrine: a newborn opens the brief its parent synthesized at birth -
    # one bounded coach-call over live records, not a raw inheritance dump.
    try:
        _mis = json.load(open(os.path.join(ROOT, "family", "child_mission.json"),
                              encoding="utf-8-sig"))
        if _mis.get("brief"):
            print("BIRTH BRIEF:", str(_mis["brief"])[:600], flush=True)
    except Exception:
        pass
    args = sys.argv
    mc = int(args[args.index("--minutes") + 1]) if "--minutes" in args else 6
    gh = int(args[args.index("--ghosts") + 1]) if "--ghosts" in args else None
    main(mc, gh, no_cooldown="--no-cooldown" in args)
