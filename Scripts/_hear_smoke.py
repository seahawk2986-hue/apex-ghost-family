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
segs, _info = model.transcribe(audio, language="en", beam_size=1)
n = len(list(segs))
print(f"[smoke-transcribe] on silence: {n} segments (0 = the honest silence)")
del model
print("[RAM-after-unload]",
      round(psutil.virtual_memory().available / 2**30, 1), "GB free")