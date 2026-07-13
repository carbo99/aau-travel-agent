import requests
from .geocode import geocode

OSRM_URL = "http://router.project-osrm.org/route/v1/driving"


def route(origin, destination):
    """Driving distance and time between two cities (OSRM public server)."""
    a = geocode(origin)
    b = geocode(destination)
    if not a or not b:
        return {"error": "could not geocode one of the cities"}

    coords = f"{a['lon']},{a['lat']};{b['lon']},{b['lat']}"
    r = requests.get(f"{OSRM_URL}/{coords}", params={"overview": "false"}, timeout=20)
    r.raise_for_status()
    data = r.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        return {"error": "no route found"}

    leg = data["routes"][0]
    km = round(leg["distance"] / 1000, 1)
    minutes = round(leg["duration"] / 60)
    hours = round(minutes / 60, 1)
    return {
        "travel_mode": "driving by car",
        "from": a["name"],
        "to": b["name"],
        "distance_km": km,
        "duration_min": minutes,
        "duration_text": f"about {hours} hours by car",
    }
