# Travel Planning Agent

Project for the course *Internet of Things and Cloud Computing*.

It is a small AI agent that plans trips. You ask something like
*"Plan a 3-day trip to Vienna from Klagenfurt under 500 euro"* and the agent chooses
some tools (weather, distance, hotels, budget), calls them, and writes an answer.
The model runs locally with Ollama. There is also a memory of the conversation, an
N8N workflow, and everything runs in Docker.


## What you need

- Python 3
- [Ollama](https://ollama.com) installed
- (optional) Docker, if you want to run it in containers
- (optional) N8N, if you want the workflow

## How to run (local)

1. Pull a model with Ollama:
   ```
   ollama pull llama3.2:1b
   ```
   (we also tested `phi3`)

2. Install the python libraries:
   ```
   pip install -r requirements.txt
   ```

3. Start the API:
   ```
   uvicorn app.main:app --reload --host 0.0.0.0
   ```
   Note: the `--host 0.0.0.0` is important, otherwise N8N cannot reach the agent.

   To use phi3 instead of llama (bigger and slower, but better answers):
   ```
   OLLAMA_MODEL=phi3 uvicorn app.main:app --reload --host 0.0.0.0
   ```
   (first do `ollama pull phi3`)

4. Test it:
   ```
   curl http://localhost:8000/health
   ```
   It should answer `{"status":"ok","model":"llama3.2:1b"}`.

You can also open `web/index.html` in the browser to use a simple chat page,
or go to `http://localhost:8000/docs` for the automatic FastAPI docs.

## How to run (Docker)

```
docker compose up --build
docker compose exec ollama ollama pull llama3.2:1b
```
This starts two containers: `agent` (our app) and `ollama` (the model).

## Cloud (GCP)

We also ran the project on a cloud VM to compare edge and cloud. Since everything is
in Docker, it works the same way on the VM:

1. Create a VM (we used GCP, e2-standard-4, 4 vCPU, 16 GB RAM, Ubuntu 22.04, 30 GB disk).
2. Connect with SSH and install Docker:
   ```
   sudo apt update
   sudo apt install -y docker.io docker-compose-v2 git
   sudo usermod -aG docker $USER
   ```
   (log out and back in after the last command)
3. Copy the project on the VM, then run the same commands as before:
   ```
   docker compose up --build
   docker compose exec ollama ollama pull llama3.2:1b
   ```
4. Run the benchmark again to compare the times. The results are in the report.

## Endpoints

- `POST /chat` – send a message, get the answer
- `POST /warmup` – load the model, returns the loading time
- `GET /health` – status
- `GET /history/{session_id}` – saved conversation

Example:
```
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo","message":"How far is Graz from Klagenfurt by car?"}'
```

## N8N

Import `n8n/travel_agent_workflow.json` in N8N. The agent must be running.
In the "Call Agent API" node use the url `http://127.0.0.1:8000/chat`
(with 127.0.0.1, not localhost – on macOS localhost went to IPv6 and it did not work).

## Benchmark

With the API and Ollama running:
```
python benchmark/run_benchmark.py
python benchmark/plot_results.py
```
It runs 12 interactions and saves `benchmark/results.csv` and the plots.

## Notes

- The small model is not perfect, sometimes it invents hotels or makes small mistakes
  in the numbers. We describe this in the report.
- The tools use free APIs with no key (Open-Meteo, OSRM, OpenStreetMap).
- We compared two models (llama3.2:1b and phi3) and also edge vs cloud, see the report.

## Folders

```
app/         the agent (FastAPI, tools, memory)
web/         simple chat page
n8n/         the N8N workflow
benchmark/   benchmark script and plots
report/      report
```
