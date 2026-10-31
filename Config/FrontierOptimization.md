# Frontier Optimization Pack — scoped to our hardware
**Hardware:** RTX 3050 8 GB · 16 GB RAM · i5-10400F (6C/12T, AVX2) · LM Studio + llama.cpp stack
**Built:** 2026-10-31 · **Spend: $0** · no model reloads performed (RAM was 3.2 GB free; deferred to quiet window)

## What the frontier actually does (scraped, with sources)

| Technique | Who uses it | Our status |
|---|---|---|
| MoE expert weights on CPU, attention/shared on GPU | KTransformers (kvcache-ai) — added an **AVX2-only CPU backend** Mar 2026, exactly our CPU; llama.cpp ships `--n-cpu-moe N` + `--moe-cache-mib` | **NEW** for us — the key to the 30B-A3B MoE fit-test |
| KV cache quantization (q8_0 ~50% KV memory cut) | vLLM/SGLang serving defaults; llama.cpp `-ctk/-ctv q8_0` | **NEW** — one toggle |
| Flash Attention | frontier serving is always-on; llama.cpp `-fa on` | **NEW** — one toggle |
| Speculative decoding with small draft model | DeepSeek MTP, EAGLE; llama.cpp `--spec-draft-model`; LM Studio `--speculative-draft-*` | **DRAFT MODELS DOWNLOADED:** `qwen3-0.6b` (639 MB) for the 8B chat brain, `qwen2.5-0.5b-instruct` (676 MB) for the 14B coding brain — same vocab, verified |
| mmap loading (no full residency) | llama.cpp default `-lm auto` | already our default |
| TTL auto-unload (idle memory reclaim) | serverless serving practice | already in use (1 h TTL) |
| PagedAttention / continuous batching | vLLM-only | not applicable to llama.cpp; `--parallel` discipline is our equivalent |

Sources: llama.cpp `tools/server/README.md` (master, Oct 2026) · KTransformers README · LM Studio speculative-decoding docs · `lms` CLI help. All fetched live this session.

## The MoE verdict flips
The previous "14.7 GB doesn't fit" conclusion assumed **full-weight residency**.
With `--n-cpu-moe 999` + `-ngl 999` + mmap, only attention/shared weights (~1–2 GB) go to VRAM and experts stream from RAM on demand. This is the exact recipe KTransformers ships for consumer GPUs with 8 GB VRAM. **The Qwen3-30B-A3B fit-test is back on the table** (needs RAM > 11.5 GB free → quiet window).

## Wrong-brain fix (live bug found)
`lms ps` showed **qwen2.5-coder-7b-instruct serving the chat lane** (was LOADED/GENERATING). The V2 engine correctly names `qwen2.5-14b-instruct`, but LM Studio was default-served whatever was resident — that's the source of any "coder-7b" self-description drift. ApexServe.ps1's Chat profile unloads the coder and pins **qwen3-8b** instead.

## LM Studio GUI toggles `lms` can't set (one-time, per model, Power User mode)
1. Flash Attention → ON (per model, load config)
2. KV Cache Quantization (experimental) → q8_0 for K and V
3. Qwen3-30B-A3B: "Force Expert Weights onto CPU" → ON
4. Speculative Decoding → select `qwen3-0.6b` / `qwen2.5-0.5b-instruct` per model
(Or skip the GUI entirely — ApexServe.ps1's Test profile drives raw llama-server with every flag.)

## Benchmark protocol (quiet window, RAM > 11.5 GB free)
Measure before/after on the same prompt, `max_tokens 1200` (Qwen3 think-phase rule):
- time-to-first-token, tokens/s — chat model vs chat model+draft
- MoE fit-test: peak RAM, tokens/s, quality spot-check
Everything measured, nothing claimed — per REPORT-HONESTY.md.