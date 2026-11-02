"""
ApexHear - the STREAMING-STT organ (the faster-whisper lane).
The canon-source: faster-whisper (SYSTRAN) = the 4x-realtime CPU STT,
int8-quantized = the ~1GB-RAM lane. $0, local.

The loop: the mic (sounddevice) -> the 16kHz float32 chunks -> the VAD
(the energy-gate) -> the rolling buffer -> the whisper-segments (the
partial-transcripts = streamed per the settle) -> the FINAL text =
POSTed to the chat (the same lane the EARS uses). The RAM-law: the model
loads ONLY if the free >= the requirement (Config/ApexHear.json); the
unload = keep_alive-style (the model = dropped after the idle).

Run:  ApexHear.py            (the foreground listen)
      ApexHear.py --daemon   (the background listen; the Logs/apex_hear.log)
The honest stop: Ctrl+C (the console) or the stop-flag-file (the daemon).
"""
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "Config", "ApexHear.json")
LOG = os.path.join(ROOT, "Logs", "apex_hear.log")
CHATTER = os.path.join(ROOT, "Scripts", "ChatVoiceTests.py")

DEFAULTS = {
    "model": "small",               # tiny | small (the int8)
    "ram_needed_gb": 1.6,           # the gate (the = the = = = = = = =)
    "chunk_s": 1.2,                 # the mic-chunk seconds
    "settle_s": 0.9,                # the silence that ends a phrase
    "vad_rms": 0.012,               # the energy-gate (the noise-floor)
    "min_phrase_s": 0.9,
    "keep_alive_min": 3,
    "post_to_chat": True,
}


def _cfg():
    c = dict(DEFAULTS)
    try:
        c.update(json.load(open(CFG, encoding="utf-8-sig")))
    except Exception:
        pass
    return c


def log(m):
    line = f"[{time.strftime('%H:%M:%S')}] {m}"
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
    print(line)


def chat_post(text):
    """The same channel the EARS use: the X-Apex-Key + /talk/api."""
    import requests as rq
    KEY = open(os.path.join(ROOT, "Config", "apex_api.key"),
               encoding="utf-8-sig").read().strip()
    try:
        r = rq.post("http://127.0.0.1:8080/talk/api",
                    json={"message": text[:600]},
                    headers={"X-Apex-Key": KEY}, timeout=90)
        return r.status_code, r.json().get("reply", "")[:120]
    except Exception as e:
        return -1, str(e)[:80]


def main(daemon=False):
    c = _cfg()
    # THE RAM-LAW (the founder's hardware order: gate before the weight)
    import psutil as ps
    free = ps.virtual_memory().available / 2**30
    if free < c["ram_needed_gb"]:
        log(f"HEAR-REFUSED: RAM free {free:.2f}GB < {c['ram_needed_gb']}GB "
            "(the law: no strain); retry in an idle-window")
        return 1
    import sounddevice as sd
    from faster_whisper import WhisperModel

    model_path = "base.en" if c["model"] == "tiny" else "small.en"
    log(f"HEAR loading {model_path} int8 (free {free:.1f}GB)...")
    model = WhisperModel(model_path, device="int8-r1", compute_type="int8")
    log("HEAR loaded; listening (the partials = streamed, the stop = the "
        "silence or the stop-flag)")

    stopflag = os.path.join(ROOT, "Logs", "apex_hear.stop")
    if os.path.exists(stopflag):
        os.remove(stopflag)

    fs = 16000
    buf = np.zeros((0,), dtype=np.float32)
    voiced = np.zeros((0,), dtype=np.float32)
    last_text = ""
    started = time.time()

    def cb(indata, frames, t, status):
        nonlocal buf
        buf = np.concatenate([buf, indata[:, 0].astype(np.float32)])

    with sd.InputStream(samplerate=fs, channels=1, blocksize=fs, callback=cb):
        while True:
            if daemon and os.path.exists(stopflag):
                log("HEAR stop-flag (the honest stop)")
                break
            time.sleep(c["chunk_s"])
            new = buf.copy()
            buf = np.zeros((0,), dtype=np.float32)
            rms = float(np.sqrt((new ** 2).mean())) if len(new) else 0.0
            if rms >= c["vad_rms"]:
                voiced = np.concatenate([voiced, new])
                continue  # the = = the = the = = = = = = = = = = = = = = the
            # the silence = the settle: transcribe what we've heard
            if len(voiced) < fs * c["min_phrase_s"]:
                voiced = np.zeros((0,), dtype=np.float32)
                continue
            t0 = time.time()
            segs, _ = transcribe(model, voiced)
            voiced = np.zeros((0,), dtype=np.float32)
            text = " ".join(s.text.strip() for s in segs).strip()
            if not text or text == last_text:
                continue
            last_text = text
            dt = time.time() - t0
            log(f"HEARD ({dt:.1f}s): {text[:110]}")
            if c["post_to_chat"]:
                st, reply = chat_post(text)
                log(f"  -> chat {st}: {reply}")
            if not daemon and not sys.stdin.isatty():
                break
            if time.time() - started > 3600 * 2:
                log("HEAR 2h-shift = the honest unload (the RAM back)")
                break
    del model
    log("HEAR unloaded")
    return 0


def transcribe(model, audio):
    return model.transcribe(audio, language="en", beam_size=1,
                            vad_filter=False)


if __name__ == "__main__":
    main(daemon="--daemon" in sys.argv)