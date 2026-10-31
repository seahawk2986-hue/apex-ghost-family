import os
import sys
import json
import time
import logging
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ApexBridge")

app = FastAPI(title="Apex Network Bridge")
ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
I_FILE = os.path.join(ROOT, "inbound_adaptations.txt")
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
LOCAL_MODEL = "qwen2.5-coder:7b"

class ChatPayload(BaseModel):
    message: str

def query_local_weights(prompt_content):
    import requests
    payload = {
        "model": LOCAL_MODEL,
        "messages": [{"role": "user", "content": prompt_content}],
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 4096}
    }
    try:
        r = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=30.0)
        if r.status_code == 200:
            return r.json().get("message", {}).get("content", "").strip()
    except Exception as e:
        logger.error(f"Inference handshake exception: {str(e)}")
    return ""

def background_extract_and_evolve(friend_text: str):
    p = f"Extract structural technical facts, refactoring rules, or code directives from this agent packet: {friend_text}. Output ONLY the raw directive text content."
    raw_response = query_local_weights(p)
    try:
        with open(I_FILE, "w", encoding="utf-8") as f:
            f.write(raw_response)
        logger.info("🧠 Integration Bridge: Inbound directives flushed cleanly to disk cache matrix.")
    except Exception as e:
        logger.error(f"Disk storage synchronization error: {str(e)}")

@app.post("/chat")
async def process_incoming_agent_event(payload: ChatPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(background_extract_and_evolve, payload.message)
    return {"reply": "Transmission integrated successfully into the local volatile state array."}

if __name__ == "__main__":
    # Single-instance guard v2: PID registry (no enumeration - hang-proof).
    try:
        import psutil
        reg_path = os.path.join(R, "Config", "layer_pids.json")
        reg = {}
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                reg = json.load(f)
        except Exception:
            reg = {}
        ent = reg.get("bridge") or {}
        pid = ent.get("pid")
        dup = False
        if pid and pid != os.getpid() and psutil.pid_exists(pid):
            try:
                if "python" in (psutil.Process(pid).name() or "").lower():
                    dup = True
            except Exception:
                dup = False
        if dup:
            logger.info("Duplicate bridge instance detected (registry) - exiting cleanly.")
            sys.exit(0)
        reg["bridge"] = {"pid": os.getpid(), "started": time.strftime("%Y-%m-%d %H:%M:%S")}
        tmp = reg_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(reg, f)
        os.replace(tmp, reg_path)
    except Exception:
        pass
    import uvicorn
    uvicorn.run("optimized_agent:app", host="127.0.0.1", port=8081, reload=False, workers=1)
