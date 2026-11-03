"""SourcingDesk - THE 100-DOC PROVENANCE ROUND (2026-11-03; the law:
a source is PROVEN only when OUR OWN fetch of the org's own page comes
back with the expected provenance-token on it; a guessed id that fails
prints loudly and stays failed - nothing is laundered into [V]):

  THE OUTSOURCING LAW (per Config/outsourcing_state.json):
  the fetching silicon = GitHub runners + keyless lanes (arXiv-side);
  the founder's box holds the corpus + the receipts, and fetches a tiny
  local proof-of-door sample only. `--max-fetch` caps each run politely.

  corpus = papers+BLOGS from TOP AI COMPANIES (OpenAI, DeepMind/Google,
  Anthropic, Meta, Microsoft, NVIDIA, Mistral, xAI, DeepSeek, Qwen,
  Zhipu/GLM, Moonshot, Cohere, Hugging Face, IBM, Apple, Stability,
  Bloomberg, Amazon, ByteDance). Every receipt row: ts, url, org, the
  token demanded, http, ok, title, note + sha256 (the audit trail).
  verified n / attempted m is the ONLY number that exists afterward.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.environ.get(
    "APEX_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEDGER = os.path.join(ROOT, "Config", "sourcing_ledger.jsonl")
STATE_F = os.path.join(ROOT, "Config", "sourcing_state.json")
UA = "Mozilla/5.0 (ApexSourcingDesk/1.0; honest receipts)"
SLEEP_BETWEEN = 0.4
ARXIV = "https://arxiv.org/abs/"

# corpus: (org, url, token-that-must-appear-on-the-org's-own-page)
# the tokens = an author surname or a title fragment from training
# knowledge [K]; ONLY the fetch converts it to [V].
CORPUS = [
    # ---- OpenAI ----
    ("OpenAI", ARXIV + "2303.08774", "GPT-4 Technical Report"),
    ("OpenAI", ARXIV + "2005.14165", "Few-Shot Learners"),
    ("OpenAI", ARXIV + "2203.02155", "Ouyang"),
    ("OpenAI", ARXIV + "2001.08361", "Kaplan"),
    ("OpenAI", ARXIV + "2103.00020", "Radford"),
    ("OpenAI", ARXIV + "2212.04356", "Radford"),
    ("OpenAI", ARXIV + "2204.06125", "Ramesh"),
    ("OpenAI", ARXIV + "2107.03374", "Chen"),
    ("OpenAI", ARXIV + "2112.09332", "Nakano"),
    ("OpenAI", ARXIV + "2309.17421", "GPT-4V(ision)"),
    ("OpenAI", ARXIV + "2305.20050", "Lightman"),
    ("OpenAI", ARXIV + "2312.09390", "Burns"),
    ("OpenAI", ARXIV + "2210.10760", "Gao"),
    ("OpenAI", ARXIV + "1706.03741", "Christiano"),
    ("OpenAI", ARXIV + "1502.05477", "Schulman"),
    # ---- Google DeepMind / Google Research ----
    ("Google DeepMind", ARXIV + "2203.15556", "Hoffmann"),
    ("Google DeepMind", ARXIV + "2312.11805", "Rohan Anil"),
    ("Google DeepMind", ARXIV + "2403.05530", "Gemini 1.5"),
    ("Google DeepMind", ARXIV + "1712.01815", "Silver"),
    ("Google DeepMind", ARXIV + "1911.08265", "Schrittwieser"),
    ("Google DeepMind", ARXIV + "2112.11446", "Rae"),
    ("Google DeepMind", ARXIV + "2203.07814", "AlphaCode"),
    ("Google DeepMind", ARXIV + "2212.12794", "GraphCast"),
    ("Google DeepMind", ARXIV + "2403.08295", "Gemma"),
    ("Google DeepMind", ARXIV + "2408.00118", "Gemma 2"),
    ("Google DeepMind", ARXIV + "2301.04104", "Hafner"),
    ("Google DeepMind", ARXIV + "2310.08864", "Open X-Embodiment"),
    ("Google Research", ARXIV + "2201.11903", "Jason Wei"),
    ("Google Research", ARXIV + "2210.03629", "Shunyu Yao"),
    ("Google Research", ARXIV + "1910.10683", "Raffel"),
    ("Google Research", ARXIV + "2101.03961", "Fedus"),
    ("Google Research", ARXIV + "2204.02311", "Chowdhery"),
    ("Google Research", ARXIV + "2305.10403", "PaLM 2"),
    ("Google DeepMind", ARXIV + "2302.01318", "Speculative Sampling"),
    ("Google Research", ARXIV + "2211.17192", "Leviathan"),
    ("Google Research", ARXIV + "2404.07143", "Infini-attention"),
    ("Google Research", ARXIV + "2010.11929", "Dosovitskiy"),
    ("Google Research", ARXIV + "2303.03378", "Driess"),
    ("Google Research", ARXIV + "2305.16264", "Muennighoff"),
    # ---- Anthropic ----
    ("Anthropic", ARXIV + "2212.08073", "Bai"),
    ("Anthropic", ARXIV + "2209.11895", "Elhage"),
    ("Anthropic",
     "https://transformer-circuits.pub/2024/scaling-monosemanticity" +
     "/index.html", "Scaling Monosemanticity"),
    ("Anthropic", "https://www.anthropic.com/engineering/building-" +
     "effective-agents", "effective agents"),
    # ---- Meta ----
    ("Meta AI", ARXIV + "2302.13971", "Touvron"),
    ("Meta AI", ARXIV + "2307.09288", "Llama 2"),
    ("Meta AI", ARXIV + "2407.21783", "Llama 3 Herd"),
    ("Meta AI", ARXIV + "2302.04761", "Schick"),
    ("Meta AI", ARXIV + "2304.02643", "Kirillov"),
    ("Meta AI", ARXIV + "2304.07193", "Oquab"),
    ("Meta AI", ARXIV + "2205.01068", "Susan Zhang"),
    ("Meta AI", ARXIV + "2308.12950", "Code Llama"),
    ("Meta AI", ARXIV + "2401.10020", "Yuan"),
    # ---- Microsoft ----
    ("Microsoft", ARXIV + "2106.09685", "LoRA"),
    ("Microsoft", ARXIV + "2306.11644", "phi-1"),
    ("Microsoft", ARXIV + "2303.12712", "Sparks of Artificial"),
    ("Microsoft", ARXIV + "2311.11045", "Orca 2"),
    ("Microsoft", ARXIV + "2309.05463", "phi-1.5"),
    ("Microsoft", ARXIV + "2308.08155", "Wu"),
    ("Microsoft", ARXIV + "2404.16130", "GraphRAG"),
    ("Microsoft", ARXIV + "2304.08485", "Visual Instruction"),
    # ---- NVIDIA ----
    ("NVIDIA", ARXIV + "2406.11704", "Nemotron-4"),
    ("NVIDIA", ARXIV + "2411.13676", "Hymba"),
    ("NVIDIA", "https://developer.nvidia.com/blog", "NVIDIA"),
    # ---- Mistral ----
    ("Mistral AI", ARXIV + "2310.06825", "Jiang"),
    ("Mistral AI", ARXIV + "2401.04088", "Mixtral"),
    ("Mistral AI", "https://mistral.ai/news", "Mistral"),
    # ---- xAI ----
    ("xAI", "https://x.ai/blog/grok-1.5", "Grok"),
    # ---- DeepSeek ----
    ("DeepSeek", ARXIV + "2401.02951" if False else ARXIV + "2405.04434",
     "DeepSeek-V2"),
    ("DeepSeek", ARXIV + "2401.06066", "DeepSeekMoE"),
    ("DeepSeek", ARXIV + "2412.19437", "DeepSeek-V3"),
    ("DeepSeek", ARXIV + "2501.12948", "DeepSeek-R1"),
    # ---- Alibaba Qwen ----
    ("Alibaba Qwen", ARXIV + "2309.16609", "Qwen Technical Report"),
    ("Alibaba Qwen", ARXIV + "2407.10671", "Qwen2"),
    ("Alibaba Qwen", ARXIV + "2412.15115", "Qwen2.5"),
    ("Alibaba Qwen", ARXIV + "2505.09388", "Qwen3"),
    # ---- Moonshot Kimi ----
    ("Moonshot Kimi", ARXIV + "2501.12599", "Kimi k1.5"),
    # ---- Cohere ----
    ("Cohere", ARXIV + "2402.07827", "Aya"),
    ("Cohere", "https://cohere.com/blog", "Cohere"),
    # ---- Hugging Face ----
    ("Hugging Face", ARXIV + "2310.16944", "Zephyr"),
    ("Hugging Face", "https://huggingface.co/blog", "Hugging Face"),
    # ---- IBM ----
    ("IBM", "https://research.ibm.com/blog", "IBM"),
    # ---- Apple ----
    ("Apple", ARXIV + "2410.05229", "GSM-Symbolic"),
    ("Apple", "https://machinelearning.apple.com/research", "Apple"),
    # ---- Stability AI ----
    ("Stability AI", ARXIV + "2307.01952", "SDXL"),
    ("Stability AI", ARXIV + "2403.03206", "Rectified Flow"),
    # ---- Bloomberg ----
    ("Bloomberg", ARXIV + "2303.17564", "BloombergGPT"),
    # ---- Amazon ----
    ("Amazon", ARXIV + "2406.02818", "Chain-of-Agents"),
    ("Amazon", ARXIV + "2305.14314", "Dettmers"),
    # ---- ByteDance ----
    ("ByteDance", ARXIV + "2402.13929", "SDXL-Lightning"),
    # ---- round-2 buffer (the 18-gap closes on real fetches or not at all)
    ("OpenAI", ARXIV + "2102.12092", "Ramesh"),
    ("OpenAI", ARXIV + "2110.14168", "Cobbe"),
    ("OpenAI", ARXIV + "2109.07958", "Lin"),
    ("Google DeepMind", ARXIV + "2206.07682", "Wei"),
    ("Google DeepMind", ARXIV + "2204.14198", "Alayrac"),
    ("Google DeepMind", ARXIV + "2205.06175", "Reed"),
    ("Google Research", ARXIV + "2201.08239", "Thoppilan"),
    ("Google Research", ARXIV + "2302.06675", "Symbolic Discovery"),
    ("Meta AI", ARXIV + "2212.12017", "Iyer"),
    ("Meta AI", ARXIV + "2305.13516", "Pratap"),
    ("Alibaba Qwen", ARXIV + "2308.12966", "Qwen-VL"),
    ("Apple", ARXIV + "2406.11794", "DataComp"),
    # ---- protocol/spec doors (the open-standard layer) ----
    ("Anthropic MCP", "https://modelcontextprotocol.io/introduction",
     "Model Context Protocol"),
    ("ONNX", "https://onnx.ai", "ONNX"),
]


def _already_verified():
    """idempotence: a verified URL never re-fetches (the runner's
    silicon, and the orgs', are treated politely)."""
    done = set()
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                    if r.get("ok"):
                        done.add(r["url"])
                except Exception:
                    continue
    return done


def _fetch(url):
    """the polite fetch: 429s sleep-and-retry once, everything else
    fails fast and honestly."""
    last = ""
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as x:
                final_url = x.geturl()
                body = x.read(250_000).decode("utf-8", "replace")
            return 200, body, final_url, ""
        except Exception as e:
            last = f"{type(e).__name__} {getattr(e, 'code', '')}"
            code = getattr(e, "code", 0)
            if code == 429 and attempt == 1:
                time.sleep(10)
                continue
            break
    return 0, "", "", last


def _title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip()[:120]


def _verify(org, url, token):
    http, html, final_url, err = _fetch(url)
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "org": org,
           "url": url, "token": token, "http": http, "ok": False,
           "title": "", "note": "", "sha256": ""}
    if http != 200:
        row["note"] = f"fetch-failed: {err}" if err else "fetch-failed"
        return row
    row["title"] = _title(html)
    row["sha256"] = hashlib.sha256(
        html.encode("utf-8", "replace")).hexdigest()[:16]
    html_l = html.lower()
    if token.lower() not in html_l:
        row["note"] = ("TOKEN-ABSENT on the org's own page - the id or "
                       "the provenance guess failed (stays failed)")
        return row
    base = url.split("/")[2] if "://" in url else url.split("/")[0]
    if (base or "").split(":")[0] not in final_url:
        row["note"] = f"redirected off-domain -> {final_url[:80]}"
        return row
    row["ok"] = True
    row["note"] = f"PROVEN on {base}"
    return row


def sweep(target=100, max_fetch=None, show_failed=False):
    done = _already_verified()
    verified = len(done)
    attempted = 0
    failed_rows = []
    orgs = {}
    print(f"[sourcing]: start | ledger-verified {verified}/{len(CORPUS)} "
          f"candidates | target {target}")
    for org, url, token in CORPUS:
        if verified >= target:
            break
        if max_fetch and attempted >= max_fetch:
            break
        if url in done:
            continue
        row = _verify(org, url, token)
        attempted += 1
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        if row["ok"]:
            verified += 1
            orgs[org] = orgs.get(org, 0) + 1
        else:
            failed_rows.append(row)
        if attempted % 15 == 0:
            print(f"[sourcing]: ... {verified} verified / {attempted} "
                  f"attempted this run")
        time.sleep(SLEEP_BETWEEN)
    state = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "target": target,
        "verified_total_ledger": verified, "attempted_this_run": attempted,
        "orgs_this_run": orgs,
        "law": "ok only when the org's own page carries the provenance "
               "token under OUR fetch; failures stay on file visibly"}
    try:
        json.dump(state, open(STATE_F, "w", encoding="utf-8"), indent=1)
    except Exception:
        pass
    print(f"[sourcing]: RUN-RESULT verified-now "
          f"{verified}/{len(CORPUS)} candidates "
          f"| fetched {attempted} this run "
          f"| orgs: {json.dumps(orgs)}")
    if verified < target:
        need = target - verified
        print(f"[sourcing]: HONEST SHORTFALL {need} below target "
              f"- fix the failed ids (they print below) and re-run; "
              f"no receipt is invented to close the gap")
    for row in failed_rows:
        print(f"  FAIL {row['url']} -> {row['note']}")
    return verified


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=100)
    ap.add_argument("--max-fetch", type=int, default=None)
    ap.add_argument("--show-failed", action="store_true")
    args = ap.parse_args()
    sweep(args.target, args.max_fetch, args.show_failed)
