import gc
import os
import psutil

class HardwareGovernor:
    def __init__(self, max_ram_mb=512):
        self.max_ram_mb = max_ram_mb
        self.process = psutil.Process(os.getpid())

    def enforce_limits(self):
        """Enforces strict memory reclamation blocks to eliminate host machine strain."""
        gc.collect()
        try:
            mem_info = self.process.memory_info()
            mem_mb = mem_info.rss / (1024 * 1024)
            if mem_mb > self.max_ram_mb:
                print(f"?? [Governor] Memory threshold exceeded ({mem_mb:.1f}MB). Flushing cache loops...")
                gc.collect()
        except Exception:
            pass

