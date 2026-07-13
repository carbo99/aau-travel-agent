import os
import time
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")


def chat(messages, temperature=0.3):
    """Send a chat request to Ollama and return (text, elapsed_seconds)."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    start = time.perf_counter()
    r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
    r.raise_for_status()
    elapsed = time.perf_counter() - start
    data = r.json()
    return data["message"]["content"], elapsed


def warmup():
    # First call loads the model into memory, we use it to measure load time
    start = time.perf_counter()
    try:
        chat([{"role": "user", "content": "ok"}])
    except Exception as e:
        print("warmup failed:", e)
    return time.perf_counter() - start
