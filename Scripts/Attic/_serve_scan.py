"""THE SERVE-SCANNER: the family's long-running serves (the OLD-code's
in-memory = the chat-lock's not-yet-live = the restart = the cure)."""
import psutil

for p in psutil.process_iter(["pid", "name", "cmdline"]):
    try:
        cl = " ".join(p.info["cmdline"] or [])[:120]
        low = cl.lower()
        if "apex" in low or "uvicorn" in low or "evolution" in low \
                or "fastapi" in low or "lmstudio" in low or ":1234" in cl:
            print(f"pid {p.info['pid']}: {p.info['name']}: {cl}")
    except Exception:
        pass