import time
import psutil

_proc = psutil.Process()


class Timer:
    """Small helper to time a block of code."""
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self.start


def snapshot():
    """Current CPU and memory usage of this process + system memory."""
    return {
        "cpu_percent": _proc.cpu_percent(interval=0.1),
        "process_mem_mb": round(_proc.memory_info().rss / (1024 * 1024), 1),
        "system_mem_percent": psutil.virtual_memory().percent,
    }
