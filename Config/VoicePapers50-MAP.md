# VoicePapers50 -> Apex Feature Map
**(the source of record: `Config/VoicePapers50.jsonl` — 50 arXiv papers, $0, harvested 2026-11-01)**

## The paper clusters (what people like, per the papers)

| # | Cluster (papers) | The liked-UX the papers establish | Apex status |
|---|---|---|---|
| 1 | Backchannel / acknowledgements (8: e.g. *Aligning Backchannel and Dialogue Context Representations*, 2026) | Acking the user before answering = perceived responsiveness + trust | ✅ `ack-variety` rotation in `ApexEars.ps1` (4 acks, rotated) |
| 2 | Turn-taking prediction (8: e.g. *Turn-Taking Prediction for Natural Conversational Speech*, 2022) | The system must cede the floor at the right beat, resume after reply | ✅ wake→cmd grammar swap + 5s echo-window; follow_up window 10s |
| 3 | Interruption / barge-in (8: e.g. *Semantic-Aware Interruption Detection in Spoken Dialogue Systems*, 2026) | Mid-speech interruption must halt TTS instantly | ✅ shipped in the 44-canon round (chunked TTS + "stop" watcher) |
| 4 | Wake-word / keyword spotting (8: e.g. *Efficient Keyword Spotting with long-range interactions*, 2021) | Always-on listening gated by a keyword — never transcribe the whole day | ✅ SAPI grammar-wake, conf 0.40, 10-s follow-up |
| 5 | TTS naturalness (8 papers) | Sentence-chunked speech beats whole-block TTS for perceived delay + naturalness | ✅ chunker at [.!?] + 160-char pack; **NEW**: `-Rate` pacing (long → +1) |
| 6 | Voice-UI design (8: e.g. *VUI in Clinical Settings*, 2023) | Repair requests ("say that again"), confirmations for destructive acts | ✅ **NEW**: `repair-retry` (one "Say that again?") + `confirm-gate` (delete/wipe/kill = spoken confirm; "Apex do it" releases) |
| 7 | Low latency (2: e.g. *PSLM: Parallel Generation of Text and Speech*, 2024) | First-audio latency dominates satisfaction; disclose waits honestly | ✅ ttft-metrics receipt + **NEW** `one-sec` data-driven backchannel (last ttft > 8s → "One second.") |
| 8 | Self-echo protection (from turn-taking/echo literature in-cluster) | A voice agent must NOT consume its own TTS as a command | ✅ **NEW** `echo-guard` (low-conf rows suppressed 5-7s after Apex speaks) |
| 9 | Rich-vocabulary parity (the founder's law, supported by the naturalness + VUI clusters) | Voice replies = same depth as the typed app | ✅ **NEW** shared rich-vocab directive in BOTH prompt-builders; voice-lane = prose-only (no markdown spoken aloud) + `Speak-Clean` flattener (backstop) |
| 10 | Emotion sensing (in the harvest tag `emotion`; 0 unique new ids beyond dedupe) | Emotion-adaptive replies = liked but model-heavy | ⬜ parked: would add a model = RAM law; revisit only with a founder unlock + free tiny model |

## Implemented TODAY (this round) — all pure code/state

- `ack-variety`, `echo-guard`, `repair-retry`, `confirm-gate`, `one-sec`, `Speak-Clean`, `-Rate` pacing, prose-vocab (both lanes) — in `Scripts/ApexEars.ps1`, `Scripts/ApexSpeak.ps1`, `run_apex_evolution.py`
- **RAM delta: 0.00 MB** (a few string vars + bounded metrics read per command; no new model, no new process, no VRAM touched)
- Files written: `Config/VoicePapers50.jsonl` (the 50 papers), this map