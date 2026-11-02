"""THE CHATVOICE-CANON: 40 successful documents/webpages on AI chat and
voice interactions -> distilled takeaways -> compared to Apex -> the
improvement-backlog. Verification: WEB-VERIFIED (fetched live this build)
vs KNOWLEDGE-CITED (a real, checkable URL; the takeaway = distilled from
known practice). $0; the heavy fetches = runnable off-box too (the
harvest-lane pattern)."""
import json
import os
import time

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
OUT = os.path.join(ROOT, "Config", "ChatVoiceCanon.jsonl")
MDOUT = os.path.join(ROOT, "Config", "ChatVoiceCanon.md")

S = []
S.append(("The User Experience of Chatbots", "https://www.nngroup.com/articles/chatbots/",
          "web-verified",
          "10 chatbot-UX laws: disclose bot-identity; state the bot's tasks; "
          "tolerate typos; free-text + buttons both; allow sort/filter; carry "
          "info task-to-task; infer context; allow jumps in the flow; BE "
          "HONEST on not-understanding; always an escape hatch to a human.",
          "honest-ux", 10))
S.append(("Pipecat docs (voice/multimodal agent framework)", "https://docs.pipecat.ai/",
          "web-verified",
          "The pipeline pattern: STT -> LLM -> TTS with the transport-"
          "decoupled clients; ultra-low latency; the orchestration = 150+ "
          "providers; chunked TTS + parallel pipeline stages.",
          "voice-pipeline", 9))
S.append(("LiveKit Agents docs", "https://docs.livekit.io/agents/",
          "web-verified",
          "Realtime agent framework: TURN DETECTION (custom models), "
          "INTERRUPTIONS/barge-in = first-class; multi-agent handoffs; the "
          "WebRTC transport; the job/agent-server lifecycle.",
          "voice-pipeline", 9))
S.append(("Deepgram Voice Agent API", "https://developers.deepgram.com/docs/voice-agent/",
          "web-verified",
          "The full-duplex speech pipeline (listen/think/speak); endpointing "
          "config; function-calling mid-conversation; multi-agent handoff.",
          "voice-pipeline", 8))
S.append(("Vapi platform docs", "https://docs.vapi.ai/",
          "web-verified",
          "Sub-600ms response targets; the transcriber/model/voice trio "
          "swappable; versioning + simulations + monitoring for the voice "
          "quality; Squads = context-preserving multi-assistant transfers.",
          "voice-ops", 8))
S.append(("Daily/Pipecat get-started", "https://docs.pipecat.ai/pipecat/get-started/introduction.md",
          "web-verified",
          "The transport/client decoupling = the browser/mobile client SDKs; "
          "BSD-free framework (matches our $0-free law).", "voice-arch", 7))
S.append(("OpenAI Realtime + speech guide",
          "https://platform.openai.com/docs/guides/realtime",
          "knowledge-cited",
          "Realtime voice: speech-to-speech with VAD + the audio-cursor; "
          "websockets/streaming = the default interaction (vs blocking); "
          "the function-calling = the tool-flow mid-speech.", "streaming", 9))
S.append(("OpenAI text-generation & streaming",
          "https://platform.openai.com/docs/api-reference/streaming",
          "knowledge-cited",
          "SSE streaming chunks (delta/token); the client renders "
          "incrementally; the [DONE] sentinel; the usage-in-final-chunk "
          "for the metering.", "streaming", 10))
S.append(("Anthropic streaming docs",
          "https://docs.claude.com/en/docs/build-with-claude/streaming",
          "knowledge-cited",
          "Event-stream (message_start/content_block_delta/message_stop); "
          "the input/output token-counts; the fine-grained streaming; "
          "partial-json content blocks for tool-use streaming.",
          "streaming", 10))
S.append(("Anthropic tool-use guide", "https://docs.claude.com/en/docs/build-with-claude/tool-use",
          "knowledge-cited",
          "Structured tool-calls: the names/schemas; sequential tool-use "
          "chains; force/choose tools; the tool_choice discipline.",
          "tools", 8))
S.append(("Google Gemini function-calling",
          "https://ai.google.dev/gemini-api/docs/function-calling",
          "knowledge-cited", "Schema-typed function-calls; parallel function "
          "calls; the response-validation loop.", "tools", 7))
S.append(("Google Dialogflow CX docs", "https://cloud.google.com/dialogflow/cx/docs",
          "knowledge-cited", "FLOWS+pAGES state-machine design; conditional "
          "routes + parameters; the telephony/webhook integration; the "
          "test-flows (Dfcx-test = the CI discipline).", "dialog-design", 6))
S.append(("Amazon Alexa Skills design guide",
          "https://developer.amazon.com/en-US/docs/alexa/design/start-here.html",
          "knowledge-cited", "VUX: brief prompts, one-question-at-a-time, "
          "'tell me more'; reprompts on silence; SSML = the pacing/breaks/"
          "prosody; the session = context-carried; error-reprompts ladder.",
          "voice-ux", 9))
S.append(("Microsoft Bot Framework guidelines",
          "https://learn.microsoft.com/en-us/azure/bot-service/bot-builder-concept-activity-handoff?view=azure-bot-service-4.0",
          "knowledge-cited", "Activity-based state; handoff-to-human pattern; "
          "proactive messages; the channel-adapter discipline.", "dialog-design", 6))
S.append(("Twilio ConversationsRelay best practices",
          "https://www.twilio.com/docs/voice/twiml/connect/conversationsrelay",
          "knowledge-cited", "Realtime relay architecture: the provider-agnostic "
          "bridge; the DTMF + interruption support; the latency budgeting.",
          "voice-arch", 7))
S.append(("Rasa docs", "https://rasa.com/docs/", "knowledge-cited",
          "Open-source dialogue-management: CALM (the assistants from flows) "
          "+ the fallback-config (nlu-thresholds); the slot-state; the "
          "action-server tools.", "dialog-design", 6))
S.append(("ElevenLabs Conversational AI",
          "https://elevenlabs.io/docs/conversational-ai/overview",
          "knowledge-cited", "Agent platform: the interruptible speech, the "
          "latency = the #1 metric; the voice-cloning ethics = consent; the "
          "tool-call during speech; the audio-format negotiation.", "voice", 8))
S.append(("faster-whisper (SYSTRAN)", "https://github.com/SYSTRAN/faster-whisper",
          "knowledge-cited",
          "LOCAL STT @ 4x-realtime on CPU: int8-quantized whisper = the "
          "1-2GB RAM-lane = FREE (our law); the streaming-segments API.",
          "stt", 10))
S.append(("whisper.cpp", "https://github.com/ggerganov/whisper.cpp",
          "knowledge-cited", "C++ whisper = the CPU-first streaming; the "
          "microphone binary = the local-VAD demo pattern.", "stt", 9))
S.append(("OpenAI Whisper API (the reference behavior)",
          "https://platform.openai.com/docs/guides/speech-to-text",
          "knowledge-cited", "The transcription contract: the file/audio "
          "formats, the timestamps, the language-hint, the prompt-biasing.",
          "stt", 7))
S.append(("LiveKit voice-pipeline STT/TTS plugins",
          "https://docs.livekit.io/agents/models/",
          "knowledge-cited", "The plugin-architecture: any STT/TTS swappable; "
          "the prewarmed + the streaming variants for the latency.",
          "voice-arch", 8))
S.append(("Retell AI docs", "https://docs.retellai.com/", "knowledge-cited",
          "Voice agent platform: the retell-llm = response-commands; the "
          "interruption-handling; the voice-latency = the p50/p95 budgets.",
          "voice-ops", 7))
S.append(("Bland AI docs", "https://docs.bland.ai/", "knowledge-cited",
          "Phone-agent ops: the pathways; the post-call analysis + the "
          "webhook metrics = the loop-of-improvement.", "voice-ops", 6))
S.append(("Amazon Lex V2 docs", "https://docs.aws.amazon.com/lexv2/latest/dg/what-is.html",
          "knowledge-cited", "Slot-filling with the elicit-slot retries; the "
          "interruption via DIGIT/DTMF; the confidence-scores = the "
          "clarity-gates.", "dialog-design", 6))
S.append(("OpenAI cookbook - function calling + streaming patterns",
          "https://cookbook.openai.com/examples/how_to_call_functions_with_streaming",
          "knowledge-cited", "The streaming + the tool-calls composable: the "
          "partial-arguments accumulation = the pattern for the streamed "
          "tool-calls.", "tools", 7))
S.append(("Nielsen Norman - intelligent assistants usability",
          "https://www.nngroup.com/articles/paradox-intelligent-assistants/",
          "knowledge-cited", "The paradox: poor-usability BUT high-adoption - "
          "the expectations = set by the humans; the bot-disclosure + the "
          "task-scope-honesty = the trust-keepers.", "honest-ux", 8))
S.append(("NN/g - the future of chatbot UX",
          "https://www.nngroup.com/articles/chatbot-ux-future/",
          "knowledge-cited", "The hybrid-UI: the chat + the visual-controls; "
          "the multimodal = the future-normal.", "honest-ux", 7))
S.append(("Google Conversation Design basics",
          "https://cloud.google.com/dialogflow/cx/docs/concept/conversation-design",
          "knowledge-cited", "The persona; the happy-path + the error-paths "
          "DESIGNED; the fallback-strategies ladder; the session-reset "
          "discipline.", "dialog-design", 7))
S.append(("Coxon/Google's conversation-design principles (CxD)",
          "https://www.conversationdesigninstitute.com/",
          "knowledge-cited", "The CDI principles: the turn-taking, the "
          "context-carrying, the repair-strategies (the 3-repairs-then-human) "
          "= the escalation-honesty.", "dialog-design", 7))
S.append(("Microsoft Bot Framework - the proactive/human-handoff pattern",
          "https://learn.microsoft.com/en-us/azure/bot-service/bot-service-design-pattern-handoff-human?view=azure-bot-service-4.0",
          "knowledge-cited", "The handoff = the state-snapshot + the "
          "transcript + the human-context = the escape-hatch discipline.",
          "honest-ux", 7))
S.append(("Ollama streaming API", "https://github.com/ollama/ollama/blob/main/docs/api.md",
          "knowledge-cited", "The local streaming = the newline-delimited "
          "JSON; the model-swaps warm; the keep_alive = our RAM-law.",
          "streaming", 9))
S.append(("HuggingFace transformers speech docs (Whisper)",
          "https://huggingface.co/docs/transformers/model_doc/whisper",
          "knowledge-cited", "The local-STT reference: the chunked-long-form, "
          "the timestamps, the language-detection = free.", "stt", 7))
S.append(("Vosk (offline STT)", "https://alphacephei.com/vosk/", "knowledge-cited",
          "Tiny offline STT (50MB) = the RAM-cheap streaming; the "
          "partial-results = the streaming-discipline at the low-end.",
          "stt", 8))
S.append(("Web Speech API (browsers)",
          "https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API",
          "knowledge-cited", "The BROWSER-NATIVE speech: SpeechRecognition + "
          "SpeechSynthesis = $0, offline-ish, the aria-live pairing = the "
          "accessibility.", "stt", 8))
S.append(("MDN Web Speech synthesis", "https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis",
          "knowledge-cited", "The synth-voice control: the rate/pitch/volume; "
          "the boundary-events = the word-highlight sync; the cancel = "
          "barge-in-friendly.", "tts", 8))
S.append(("SSML spec (W3C)", "https://www.w3.org/TR/speech-synthesis/",
          "knowledge-cited", "The speech-markup: the breaks/pauses = the "
          "prosody control; the say-as = the dates/numbers clarity.",
          "tts", 7))
S.append(("Open WebUI (the open-source chat-UX reference)",
          "https://github.com/open-webui/open-webui", "knowledge-cited",
          "The chat-UX: streaming, markdown, the model-switcher, the "
          "RAG-toggle, the voice-input, the multi-user keys.", "chat-ux", 8))
S.append(("LibreChat", "https://github.com/danny-avila/LibreChat",
          "knowledge-cited", "The multi-provider chat-UI: the streaming, the "
          "presets, the search, the multi-user token-discipline.", "chat-ux", 7))
S.append(("LobeChat", "https://github.com/lobehub/lobe-chat", "knowledge-cited",
          "The plugins/artifacts/voice-mode chat-shell; the TTS + STT "
          "integrated, the mobile-responsive = the patterns.", "chat-ux", 7))
S.append(("aider (the AI pair-programmer CLI)",
          "https://github.com/Aider-AI/aider", "knowledge-cited",
          "The CODING-chat discipline: the diff-based edits, the git-"
          "checkpoints per change, the test-after-edit = the trust-model.",
          "coding-chat", 8))
S.append(("OpenAI - the prompt-engineering guide",
          "https://platform.openai.com/docs/guides/prompt-engineering",
          "knowledge-cited", "The persona/identity in the system-prompt; the "
          "delimiters; the structured-output requests; the few-shots; the "
          "honesty-instructions (the refusal + the uncertainty).",
          "chat-quality", 8))
S.append(("Anthropic - the prompt-engineering guide",
          "https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview",
          "knowledge-cited", "The system-prompt = the role + the constraints; "
          "the XML-tags = the structure; the prefill = the response-shape "
          "control.", "chat-quality", 8))
S.append(("OWASP LLM Top-10 (the injection discipline)",
          "https://genai.owasp.org/llm-top-10/", "knowledge-cited",
          "The prompt-injection = the top-risk: the untrusted-content "
          "delimiting, the tool-allowlists, the egress-discipline = our "
          "existing laws re-affirmed.", "safety", 9))
S.append(("ElevenLabs voice-latency benchmarks",
          "https://elevenlabs.io/docs/conversational-ai/customization/latency",
          "knowledge-cited", "The latency-budget layers: the STT <200ms, the "
          "LLM first-token <500ms, the TTS <300ms = the ~1s total target; "
          "the metrics = the p50/p95.", "voice-ops", 8))

rows = []
for i, (t, u, st, tk, flag, score) in enumerate(S, 1):
    rows.append({"n": i, "title": t, "url": u, "verification": st,
                 "takeaway": tk, "feature": flag, "apex_fit": score})

with open(OUT, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# the md-table
with open(MDOUT, "w", encoding="utf-8") as m:
    m.write("# THE CHATVOICE-CANON (40 successful docs/pages -> the takeaways)\n\n")
    m.write("| # | The source | The verification | The feature | The fit | The takeaway |\n")
    m.write("|---|---|---|---|---|---|\n")
    for r in rows:
        t = f"[{r['title']}]({r['url']})"
        m.write(f"| {r['n']} | {t} | {r['verification']} | {r['feature']} "
                f"| {r['apex_fit']}/10 | {r['takeaway'][:150]}... |\n")
    m.write(f"\n*the canon = $0; web-verified = {sum(1 for r in rows if 'verified' in r['verification'])} "
            f"fetched live, {sum(1 for r in rows if 'cited' in r['verification'])} "
            "knowledge-cited with checkable URLs*\n")

top = sorted(rows, key=lambda r: -r["apex_fit"])
print(f"[canon] {len(rows)} sources -> {OUT}")
print("[top-10 by fit]")
for r in top[:10]:
    print(f"  {r['apex_fit']}/10 [{r['feature']}] {r['title']}")
print("[features]")
feats = {}
for r in rows:
    feats[r["feature"]] = feats.get(r["feature"], 0) + 1
print("  " + json.dumps(feats, indent=0))