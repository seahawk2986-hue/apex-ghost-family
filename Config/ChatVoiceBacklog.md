# THE CHAT/VOICE CANON → APEX: THE VERDICT-MAP (44 sources, 2026-11-01)
*The comparison: what the successful corpus does → what Apex had → what I implemented today (tested 25/25) → what stays queued and why. Full canon: `Config/ChatVoiceCanon.jsonl` + `.md`. All $0.00.*

## ✅ IMPLEMENTED TODAY (tested, live)

| The canon-practice (sources) | The Apex-state before | The implementation | The proof |
|---|---|---|---|
| **Streaming responses** (OpenAI, Anthropic, Gemini, Ollama, Open WebUI, LibreChat — ranked #1 by 6+ sources) | Chat = blocking: the full reply arrived in one blob | `CloudBrain.chat_stream` (groq-SSE + ollama-NDJSON generator; route-order = truth-priority; credits-tier structurally out) + `POST /talk/api/stream` (SSE) + the streamed render in the page | Live wire: `meta → tok → done`, first-token ~1–3s; groq-first verified; ChatVoiceTests 25/25 |
| **Cancellable / barge-in** (LiveKit interruptions, Deepgram full-duplex, Vapi, Retell) | No cancel existed mid-reply | STOP button (AbortController = text-barge-in; the partial = recorded honestly) + **ApexSpeak.ps1**: chunked interruptible TTS with the "stop"-keyword recognizer (SAPI = $0) | Page-tests + organ-parse + chunker-bounded all green |
| **Latency metrics** (ElevenLabs p50/p95 latency budgets, Vapi observability) | No first-token metric existed | `Config/ChatMetrics.json`: lane + ttft_s per ask (rolling 50); the meta-event carries ttft to the console | Tests + live rows |
| **Context-carry** (NN/g "save info task-to-task"; the Eno anti-pattern) | Recall = semantic-only | The prior-2 conversation-injected into the stream-prompt ("context continues; do not repeat it") | Route-test green |
| **Honest-UX** (NN/g #1/#9/#10: bot-disclosure, honest not-understanding, escape-hatch; MS handoff pattern) | Hiccup text already honest | The escape-hatch line ("say 'stop' to my voice, or page a human — I never fake answers") + aria-live a11y + automatic fallback to the blocking lane | Page-tests green |
| **The $0-law vs the canon** | — | Every stream-lane = the free set only; the credits-tier = out at source; the paid platforms in the canon = pattern-sources (patterns copied free) | Credits-exclusion tests + gate discipline |

## ⏳ QUEUED (honest rationales — not rejected)

| The practice (sources) | Why queued |
|---|---|
| **Local STT: faster-whisper / whisper.cpp** (SYSTRAN, ggerganov, HF) | RAM-law: SAPI recognition today ≈ 0-RAM; faster-whisper small-int8 ≈ 1–2GB. Queued for a nightly idle-window (same gate as the QLoRA pass). Planned organ: `ApexHear.py` (streaming partial-segments → chat) |
| **Vosk tiny-STT** (50MB model) | Same RAM-slot decision; the fallback-fallback if faster-whisper strains |
| **Web-Speech API in the page** (MDN×2) | Zero-install voice in the browser (SpeechRecognition + SpeechSynthesis, free). Queued for the next chat-page sweep; today = Blink-browsers only (honest limit) |
| **Turn-detection models** (LiveKit VAD/turn) | A continuous-listen feature; our voice = wake+dictation+speak (turns are natural). Revisit if a continuous-listening lane opens |
| **Structured tool-calls in streams** (OpenAI cookbook partial-args, Anthropic partial-json) | The personal chat has no tools; the room's V2 already has tool-loops (Micah's engine). Queued |
| **Multi-agent handoffs / Squads** (LiveKit recipes, Deepgram multi-agent, Vapi Squads) | The family already = multi-organ. Queued as a design-doc, not a build |
| **Config-as-code / simulations** (Vapi gitops, Dialogflow CI-test) | The family's cadence already does code+receipts via git; a nice formalization, low urgency |
| **SSML prosody** | SAPI supports SSML; queued for the Speak-organ's polish |
| **Post-call analysis loops** (Bland, Vapi monitor) | The nightly ChatEval already re-races lanes blind; extend it to score transcript-quality next |

## 🖥️ OUTSOURCING (their machines, per the order)

- **WebHarvest organ** (`Scripts/WebHarvest.py`, runner=actions): the 44 canon-URLs get fetched + title/description extracted **on GitHub's machines** (the same runner-side pattern as PaperHarvest10/11/12); the distilled rows commit as receipts — not our box, $0.
- The nightly ChatEval (03:30 schtask) keeps verifying the chat-voice ranking off our daytime hours; the 10-loop = hourly.

## THE HONEST BOTTOM-LINE

The corpus's top chat-UX practices = **streaming, cancel/barge-in, latency-metrics, context-carry, honest-escape** — all five are now IN and tested (25/25) on the live system at $0.00. The voice-side got the first real organ (interruptible Speak + the ears' wake/dictation). The heaviest wins left (faster-whisper STT, browser-voice) are RAM/window-gated on purpose — our hardware laws hold: nothing runs that strains the box, and everything that can run elsewhere, runs elsewhere.