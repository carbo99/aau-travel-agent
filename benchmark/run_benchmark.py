import csv
import time
import requests

API = "http://localhost:8000"

# (session_id, prompt). Same session id = the agent should remember context.
INTERACTIONS = [
    ("s1", "What's the weather in Vienna for the next 3 days?"),
    ("s1", "And what about Salzburg?"),                       # memory follow-up
    ("s1", "Which of the two cities is warmer?"),             # uses memory
    ("s2", "How far is Vienna from Klagenfurt by car?"),
    ("s2", "Find me a few hotels in Vienna."),
    ("s2", "Plan a 3-day trip to Vienna from Klagenfurt under 500 euro."),
    ("s2", "Is that within my budget?"),                      # memory follow-up
    ("s3", "Suggest hotels in Graz and the weather there."),
    ("s3", "What is the capital of Austria?"),                # no tool needed
    ("s3", "Estimate the cost for 2 people for 4 days in Graz."),
    ("s4", "Plan a weekend trip to Venice from Klagenfurt."),
    ("s4", "How much would it cost for 3 people?"),
]


def main():
    # warm up + measure model load time
    w = requests.post(f"{API}/warmup").json()
    print("model load time:", w.get("load_time_sec"), "s")

    rows = []
    for i, (sid, prompt) in enumerate(INTERACTIONS, 1):
        t0 = time.perf_counter()
        try:
            r = requests.post(f"{API}/chat",
                              json={"session_id": sid, "message": prompt},
                              timeout=180)
            wall = time.perf_counter() - t0
            data = r.json()
            m = data["metrics"]
            res = m["resources"]
            print(f"[{i:02d}] {prompt[:45]:45} -> tools={data['tools_used']} "
                  f"total={m['total_time']}s")
            rows.append({
                "n": i,
                "session": sid,
                "prompt": prompt,
                "tools_used": "|".join(data["tools_used"]),
                "llm_time": m["llm_time"],
                "tool_time": m["tool_time"],
                "total_time": m["total_time"],
                "wall_time": round(wall, 3),
                "cpu_percent": res["cpu_percent"],
                "process_mem_mb": res["process_mem_mb"],
                "system_mem_percent": res["system_mem_percent"],
            })
        except Exception as e:
            # don't lose the whole run because of one bad request
            wall = round(time.perf_counter() - t0, 3)
            print(f"[{i:02d}] {prompt[:45]:45} -> FAILED ({e})")
            rows.append({
                "n": i, "session": sid, "prompt": prompt, "tools_used": "ERROR",
                "llm_time": "", "tool_time": "", "total_time": "",
                "wall_time": wall, "cpu_percent": "", "process_mem_mb": "",
                "system_mem_percent": "",
            })

    with open("benchmark/results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print("\nsaved benchmark/results.csv")


if __name__ == "__main__":
    main()
