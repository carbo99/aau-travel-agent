"""
Quick plots from the benchmark CSV. Needs matplotlib + pandas:
    pip install matplotlib pandas
"""
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("benchmark/results.csv")

# latency breakdown per interaction
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(df["n"], df["llm_time"], label="LLM time")
ax.bar(df["n"], df["tool_time"], bottom=df["llm_time"], label="Tool time")
ax.set_xlabel("interaction #")
ax.set_ylabel("seconds")
ax.set_title("Latency breakdown per interaction")
ax.legend()
plt.tight_layout()
plt.savefig("benchmark/latency.png", dpi=120)

# memory over time
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df["n"], df["process_mem_mb"], marker="o")
ax.set_xlabel("interaction #")
ax.set_ylabel("process memory (MB)")
ax.set_title("Memory usage over interactions")
plt.tight_layout()
plt.savefig("benchmark/memory.png", dpi=120)

print("saved benchmark/latency.png and benchmark/memory.png")
