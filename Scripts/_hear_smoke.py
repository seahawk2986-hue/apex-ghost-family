"""THE HEAR-SMOKE: the whisper-brain loads (int8), transcribes a
synthetic-silence buffer (0 segments = the honest silence), unloads."""
import time

import numpy as np
import psutil

free = psutil.virtual_memory().available / 2**30
print(f"[RAM-gate] {free:.2f}GB free - need 1.6GB:",
      "GO" if free >= 1.6 else "HOLD")
if free < 1.6:
    raise SystemExit(0)

from faster_whisper import WhisperModel  # noqa: E402

t0 = time.time()
model = WhisperModel("base.en", device="cpu", compute_type="int8")
print(f"[model-load] {time.time() - t0:.1f}s (int8)")
audio = np.zeros(16000 * 2, dtype=np.float32)
kw = dict(language="en", beam_size=1, condition_on_previous_text=False,
          no_speech_threshold=0.6, log_prob_threshold=-1.0)

segs, info = model.transcribe(audio, **kw)
segs = list(segs)
print(f"[A: cure-params only] {len(segs)} segment(s);"
      f" no_speech_prob={info.no_speech_prob if hasattr(info, 'no_speech_prob') else '?'}")
for s in segs:
    print(f"    phantom: '{s.text}' avg_logprob={s.avg_logprob:.2f}")

kw2 = dict(kw, vad_filter=True,
           vad_parameters={"min_silence_duration_ms": 400})
segs2, _ = model.transcribe(audio, **kw2)
segs2 = list(segs2)
print(f"[B: +vad_filter=True] {len(segs2)} segment(s) "
      f"({'THE CURE' if len(segs2) == 0 else 'STILL LEAKS'})")
del model
print("[RAM-after-unload]",
      round(psutil.virtual_memory().available / 2**30, 1), "GB free")