import json
import re
import os

from . import llm, memory
from .tools import TOOLS
from .metrics import Timer, snapshot

# strict mode = we tell the model to use only the tool data, so it hallucinates less
# STRICT_SYNTHESIS=0 goes back to the old prompt (used it for the comparison in the report)
STRICT_SYNTHESIS = os.getenv("STRICT_SYNTHESIS", "1") == "1"

# take the cities/days/budget from the question and fix the tool args
# small models often pass wrong args, this way the tools don't break
# PARAM_EXTRACTION=0 turns it off (for the before/after test)
PARAM_EXTRACTION = os.getenv("PARAM_EXTRACTION", "1") == "1"

STRICT_SYSTEM = (
    "You are a travel planning assistant. Answer using ONLY the data in the "
    "tool results below. Do NOT invent hotel names, prices, flights, opening "
    "hours or attractions that are not in the tool results. If some information "
    "(hotels, weather, distance...) is not present, say it is not available "
    "instead of making it up. Keep the destination consistent with the user's "
    "request and do not mix up cities. All prices are in euros (\u20ac). When you "
    "mention travel time, use the travel_mode from the route result (it is a car "
    "drive, not a flight)."
)

LOOSE_SYSTEM = (
    "You are a helpful travel planning assistant. "
    "Use the tool results below to answer the user. "
    "Be concrete: mention temperatures, hotel names, distance and total cost "
    "when available. If something is missing just say so."
)

# tools description we pass to the model so it knows what it can call
TOOL_SPEC = """You can use these tools:
- weather(city, days): weather forecast for a city
- route(origin, destination): driving distance and time between two cities
- hotels(city, max_results): list of hotels in a city
- budget(days, people, distance_km, max_budget): estimate the trip cost
- geocode(city): coordinates of a city"""

PLANNER_PROMPT = """You are the planning step of a travel assistant.
{spec}

Look at the user request and decide which tools to call.
Reply ONLY with a JSON array of calls, nothing else. Example:
[{{"tool": "weather", "args": {{"city": "Vienna", "days": 3}}}},
 {{"tool": "route", "args": {{"origin": "Klagenfurt", "destination": "Vienna"}}}}]

If no tool is needed, reply with [].

User request: {query}"""


def _extract_json(text):
    """sometimes the model puts the json inside some text, so we take out the array"""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return []


def _keyword_fallback(query):
    """if the model gives a bad plan we guess the tools from the words in the query"""
    q = query.lower()
    plan = []
    if "weather" in q or "forecast" in q:
        plan.append({"tool": "weather", "args": {}})
    if "hotel" in q or "stay" in q or "accommodation" in q:
        plan.append({"tool": "hotels", "args": {}})
    if "route" in q or "distance" in q or "from" in q:
        plan.append({"tool": "route", "args": {}})
    if "budget" in q or "cost" in q or "€" in q or "euro" in q or "price" in q:
        plan.append({"tool": "budget", "args": {}})
    return plan


def _extract_params(query):
    """read the important info from the question so the tools always get good args
    (even when the small model gets them wrong)"""
    q = query.lower()
    params = {}

    # from X to Y  (or the other way, "to Y from X")
    m = re.search(r"from\s+([a-zà-ú\s]+?)\s+to\s+([a-zà-ú\s]+?)(?:\s+under|\s+for|\s+with|[.,]|$)", q)
    if m:
        params["origin"], params["destination"] = m.group(1).strip(), m.group(2).strip()
    else:
        m = re.search(r"to\s+([a-zà-ú\s]+?)\s+from\s+([a-zà-ú\s]+?)(?:\s+under|\s+for|\s+with|[.,]|$)", q)
        if m:
            params["destination"], params["origin"] = m.group(1).strip(), m.group(2).strip()
        else:
            # case like "Vienna from Klagenfurt" without the "to"
            m = re.search(r"([a-zà-ú]+)\s+from\s+([a-zà-ú]+)", q)
            if m:
                params["destination"], params["origin"] = m.group(1).strip(), m.group(2).strip()

    m = re.search(r"(\d+)\s*[- ]?day", q)          # number of days ("3-day" or "3 days")
    if m:
        params["days"] = int(m.group(1))
    elif "weekend" in q:
        params["days"] = 2

    m = re.search(r"(\d+)\s*(?:people|persons|adults|pax)", q)
    if m:
        params["people"] = int(m.group(1))

    # budget written in different ways: "under 500", "budget of 500", "€500", "500 euro"
    m = (re.search(r"(?:under|below|budget of|max)\s*€?\s*(\d+)", q)
         or re.search(r"€\s*(\d+)", q)
         or re.search(r"(\d+)\s*(?:euro|eur)", q))
    if m:
        params["max_budget"] = int(m.group(1))

    return params


def _patch_plan(plan, params):
    """put the values from the query into the tool args when they are missing or wrong"""
    for step in plan:
        name = step.get("tool")
        args = step.setdefault("args", {})
        if name == "route":
            if params.get("origin"):
                args["origin"] = params["origin"]
            if params.get("destination"):
                args["destination"] = params["destination"]
        elif name in ("weather", "hotels"):
            if not args.get("city") and params.get("destination"):
                args["city"] = params["destination"]
        elif name == "budget":
            args["days"] = params.get("days", args.get("days", 2))
            args["people"] = params.get("people", args.get("people", 1))
            if params.get("max_budget"):
                args["max_budget"] = params["max_budget"]
            # remove the distance the model guessed, run_tools puts the real one
            args.pop("distance_km", None)
    return plan


def run_tools(plan):
    results = []
    tool_time = 0.0
    used = []
    known_distance = None  # gets filled when route runs, then budget uses it

    # route has to run before budget, so budget uses the real distance and not
    # a random number from the model
    plan = sorted(plan, key=lambda s: {"route": 0, "budget": 2}.get(s.get("tool"), 1))

    for step in plan:
        name = step.get("tool")
        args = step.get("args", {}) or {}
        if name not in TOOLS:
            continue

        # use the real distance instead of the one the model guessed
        if name == "budget" and known_distance is not None:
            args["distance_km"] = known_distance

        with Timer() as t:
            try:
                out = TOOLS[name](**args)
            except TypeError:
                # wrong args -> skip this tool instead of crashing everything
                out = {"error": f"could not call {name} with args {args}"}
            except Exception as e:
                out = {"error": str(e)}
        tool_time += t.elapsed

        if name == "route" and isinstance(out, dict):
            known_distance = out.get("distance_km")

        results.append({"tool": name, "result": out})
        used.append(name)
    return results, used, tool_time


def answer(session_id, query):
    metrics = {"llm_time": 0.0, "tool_time": 0.0}

    history = memory.get_history(session_id)

    # step 1 - planning
    plan_msg = [{"role": "user",
                 "content": PLANNER_PROMPT.format(spec=TOOL_SPEC, query=query)}]
    plan_text, t1 = llm.chat(plan_msg, temperature=0.1)
    metrics["llm_time"] += t1

    plan = _extract_json(plan_text)
    if not plan:
        plan = _keyword_fallback(query)

    # fix the args from the question so the tools don't fail
    if PARAM_EXTRACTION:
        plan = _patch_plan(plan, _extract_params(query))

    # step 2 - run the tools
    tool_results, used, tool_time = run_tools(plan)
    metrics["tool_time"] = round(tool_time, 3)

    # step 3 - final answer
    system = STRICT_SYSTEM if STRICT_SYNTHESIS else LOOSE_SYSTEM
    context = "Tool results:\n" + json.dumps(tool_results, indent=2)

    messages = [{"role": "system", "content": system}]
    messages += history
    messages.append({"role": "user", "content": f"{query}\n\n{context}"})

    final_text, t2 = llm.chat(messages, temperature=0.4)
    metrics["llm_time"] = round(metrics["llm_time"] + t2, 3)

    # save this turn in the memory
    memory.add_message(session_id, "user", query)
    memory.add_message(session_id, "assistant", final_text)

    metrics["total_time"] = round(metrics["llm_time"] + metrics["tool_time"], 3)
    metrics["resources"] = snapshot()

    return {
        "response": final_text,
        "tools_used": used,
        "plan": plan,
        "metrics": metrics,
    }
