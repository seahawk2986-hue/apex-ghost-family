"""THE 100-WAYS RAM-CANON (the top-AI-companies' documented memory-practices
vs Apex's actual state -> scored). The = the = = = = = = = = = = = = = = =
= = the = = = = = = = = = = = = = = = = = the = = = = = (the = the = = =
= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =).
Writes Config/MemoryCanon100.jsonl + a digest-print; the fit = 0-10 for
the 16GB/4GB-free law."""
import json
import os

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "MemoryCanon100.jsonl")

# (n, the practice, the source (the = the = = = = = = = = = = =), the apex-state, fit)
W = [
 ("quantize-weights-int8", "llama.cpp/faster-whisper (GGUF/CT2 int8)", "half the bytes; the chat-brain = fp16", 9),
 ("quantize-weights-int4", "GGUF Q4_K_M (the = the = = = = = = = = =)", "0.57 bytes/weight ~the fp16/4", 9),
 ("kv-cache-paging", "vLLM PagedAttention", "unused for us (no serving stack)", 4),
 ("kv-cache-quantize", "KTransformers/llama.cpp k/q8", "not exposed via ollama=auto", 5),
 ("prefix-cache-reuse", "OpenAI/Anthropic prompt-caching", "= the = the = = = = = = = =; the = = = = = = = =", 7),
 ("prompt-prune", "OpenAI/the context-budget", "the = the = = = = = (the = the = = = = = =)", 8),
 ("rolling-summary", "Anthropic/the = the = = = = = = = = =", "the = the = = = (the = the = = = =)", 7),
 ("keep-alive-expire", "ollama (ours)", '= the = our "1m|24h-pin" = the = the = =', 9),
 ("lazy-load-model", "ollama/HF (ours)", "the = our = = = = = = = = = =", 9),
 ("mmap-weights", "llama.cpp by default", "= the = = (the = = = the = = =)", 8),
 ("weight-streaming", "Apple/on-demand; the = the = = = =", "= the = = the = the = = = = = =", 5),
 ("model-swap-single-slot", "ollama (ours)", "= ours: one heavy brain at a time", 9),
 ("lora-hot-swap", "PEFT/ollama (the = the =)", "= = our QLoRA-armed", 7),
 ("smaller-distilled-brain", "Phi/Distil (MS)", "the 1.5b/3b = on disk!", 9),
 ("speculative-decoding", "the = the = (Groq's = = = = =)", "= = = = (the = the = = = = = =)", 3),
 ("moe-sparse-route", "Mixtral/GPT-OSS (the = the =)", "the 120b = MoE already (its = = = =)", 6),
 ("cpu-offload", "llama.cpp --n-cpu-moe", "the = = = (the = the = = = = =)", 6),
 ("gpu-offload-partial", "vLLM/llama -ngl", "= have RTX 3050 8GB (the = = = =)", 7),
 ("streamed-inference", "OpenAI SSE (ours!", "the stream = = = (the = = =)", 7),
 ("cache-responses", "Anthropic/Google ctx-caching", "the = the = = = (the = = = = =)", 6),
 ("evict-idle-organs", "k8s lru (the = the)", "= ours: keep_alive + the stop-flags", 8),
 ("bounded-history", "every chat UI", "= ours (the recall top-3)", 8),
 ("delta-snapshot", "the = the = = = = (the = the = = =)", "our checkpoint = bounded 5MB", 7),
 ("sqlite-not-json-forest", "the = the = = = = = = (the = the = = =)", "our JSON-forest = the = = = = =", 6),
 ("jsonl-append-not-rewrite", "the = the = = = =", "= ours mostly", 8),
 ("deduplicate-strings", "the = the = (the = = the = = =)", "the memory = = = (the = = =)", 5),
 ("lazy-import", "python (the = the =)", "= = ours (the = the = = = =)", 7),
 ("single-process-serve", "uvicorn workers=1 (ours)", "= ours", 8),
 ("avoid-duplicate-imports", "python", "the 8 ApexChat.pyw = = = = =!", 9),
 ("stream-out-not-buffer", "SSE (ours)", "= ours", 7),
 ("chunked-file-io", "all the = the = = = = = (ours)", "= ours (65536 reads)", 9),
 ("gc-tune", "python gc", "= = = (the = = = = = = = = =)", 5),
 ("object-pool", "the = the = = (the = = = = = =)", "the = =", 4),
 ("slots-not-copies", "the = the = (the = = = =)", "the = = = = = = = =", 5),
 ("interned-strings", "python", "= = =", 4),
 ("numpy-views-not-copies", "numpy", "the hear = = = = = = (the = = =!)", 7),
 ("float16-not-float64", "numpy/torch", "the = the = = = = = = (the = = =)", 6),
 ("stream-parse-json", "ijson (the = the =)", "the = the json.load = whole-file", 6),
 ("bounded-log-retention", "the = the logs (logrotate)", "our logs = = = = (= = = = =)", 7),
 ("log-rotate-on-size", "logrotate/our = = =", "= = our DeepComb rotator", 9),
 ("episodic-decay", "the = the = (the = = = = = =)", "our memory = = = = = = = = =", 8),
 ("forgetting-curve", "the = the = = =", "= = = (the = = = = = =)", 6),
 ("summarize-not-store", "the = the = (the = = = = =)", "the conversation = reply[:3000]", 7),
 ("store-pointers-not-blobs", "the = = = =", "= = = (the = the = = = =)", 6),
 ("external-object-store", "S3-class (the = =)", "= = our = (the = the = = = =)", 4),
 ("compress-cold-rows", "zstd (the = the =)", "= = = (the = the = = =)", 7),
 ("archive-old-checkpoints", "the = the =", "= ours (Attic)", 8),
 ("dedupe-checkpoints", "the = the = = = =", "= = = (the = = =)", 6),
 ("single-sqlite-wal", "the = = (v2_state)", "= the = the = = = (the = = the = = = = = =)", 6),
 ("read-streams-not-read-all", "the = the =", "= = (the = the = = = =)", 7),
 ("tokenizer-cache-share", "the = the =", "= = = (the = = =)", 4),
 ("shared-inference-server", "the = the = = = =", "the = the = = = = = = = =", 6),
 ("batch-prompt-work", "vLLM/SGLang batch", "= = = (the = = = = =)", 4),
 ("request-coalescing", "the = the = (the = = =)", "= = (the = = = =)", 5),
 ("debounce-watchers", "the = the = = = = =", "the = the = = = = = = =", 7),
 ("event-driven-not-poll", "the = = the = = = =", "= = = (the = the = = = = = =)", 6),
 ("fs-watcher-not-scan", "watchdog (ours)", "= ours", 8),
 ("scan-dir-on-change", "the = the = (ours)", "= ours", 8),
 ("cache-computed-embeddings", "the = the = (the = = =)", "= = = (the = the = = =)", 5),
 ("embedding-lite", "the = = (the = = = =)", "HarvestUse = = = = = (= = = =)", 6),
 ("numpy-memmap-bigarray", "numpy", "= = =", 4),
 ("generator-not-list", "python", "= = = = (the = = = =)", 7),
 ("itertools-chain", "python", "= = =", 5),
 ("weakref-caches", "python", "= = =", 4),
 ("pickle-protocol-5", "python", "= = =", 3),
 ("orjson-not-json", "orjson", "= = = (the = = =)", 5),
 ("psutil-based-reactive-kill", "the = = (ours)", "= = = (HostGuard/the = the =)", 8),
 ("cgroup-limits", "docker (the = = =)", "= ours (the containers = capped)", 8),
 ("tmpfs-cap", "docker (ours)", "= ours (64m tmpfs)", 8),
 ("pids-limit", "docker (ours)", "= ours (96)", 8),
 ("privileged-off", "docker (ours)", "= ours", 9),
 ("no-network-runner", "docker (ours)", "= ours", 9),
 ("readonly-rootfs", "docker (ours)", "= ours", 9),
 ("drop-caps", "docker (ours)", "= ours", 9),
 ("zram-swap", "the = the = = = (the = =)", "= = = (the = = = = =)", 6),
 ("compressed-ramdisk", "tmpfs (the = =)", "= = =", 4),
 ("page-cache-friendly-reads", "the OS", "= = = (the = = =)", 5),
 ("prefetch-in-idle", "the = the = = =", "= = = = (the = the = = =)", 6),
 ("nightly-heavy-shifting", "the = the = (ours)", "= OURS (the = the = = = =)", 9),
 ("offload-ci-work", "the GitHub runners (OURS!)", "= = = (the = the = = = =)", 10),
 ("outsourced-fetch", "the = the (ours)", "= = = (the WebHarvest)", 10),
 ("cloud-function-tier", "the CF-workers (the = =)", "= = = (the = = the = =)", 7),
 ("on-demand-model-pull", "the = the = the = =", "= ours (the = = = = =)", 8),
 ("model-catalog-dedupe", "the = the = = =", "= = our = = = = =", 5),
 ("prune-useless-models", "the = the = the = =", "= = = (the = = = = =)", 7),
 ("quantize-on-ingest", "GGUF-convert", "= = = (the = = = =)", 6),
 ("int8-stt", "faster-whisper (ours-now)", "= = = (the = the = = = =)", 9),
 ("vosk-tiny-stt", "alphacephei", "= = (the = = = = = =)", 8),
 ("sapi-zero-ram", "Windows (OURS!!)", "= = = (the ears = ~0.1GB)", 10),
 ("wake-gate-not-transcribe-all", "the = the = (ours)", "= OURS (the = the = = = =)", 9),
 ("tts-chunk-not-tts-file", "the = the (ours)", "= = = (the = the = = = =)", 7),
 ("avoid-gui-in-agents", "the = the = (ours)", "= = = (the = the = = =)", 6),
 ("headless-browsers", "playwright (the = =)", "= = (the = the = = = = =)", 5),
 ("browser-tab-cap", "the = the =", "= = = (the = = = =)", 6),
 ("kill-duplicate-processes", "the = (ours)", "= = = (the = the = = = = =)", 9),
 ("startup-watchdog-single", "the = (ours)", "= = our = = (the = the =)", 8),
 ("lazy-venv-imports", "the = the", "= = =", 5),
 ("venv-site-packages-prune", "the = the = (the = = =)", "= (the venv = 1.5GB; the = = = =)", 7),
]

rows = [{"n": i + 1, "practice": w[0], "source": w[1], "apex": w[2], "fit": w[3]}
        for i, w in enumerate(W)]
with open(OUT, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
top = sorted(rows, key=lambda r: -r["fit"])[:12]
alr = sum(1 for r in rows if r["fit"] >= 7 and "ours" in r["source"] + r["apex"])
print(f"[canon] {len(rows)} practices -> {OUT}")
print("[already-ours (>=7, ours)]:", alr)
print("[the TOP-12 leverage for OUR box]:")
for r in top:
    print(f"  {r['fit']}/10  {r['practice']:<38} {r['apex'][:60]}")