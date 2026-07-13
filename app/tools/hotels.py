import requests
from .geocode import geocode

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def hotels(city, max_results=5):
    """Find hotels near a city using OpenStreetMap data (Overpass API)."""
    loc = geocode(city)
    if not loc:
        return {"error": f"could not find location: {city}"}

    # search hotels within ~4km of the city center
    query = (
        f'[out:json][timeout:25];'
        f'node["tourism"="hotel"](around:4000,{loc["lat"]},{loc["lon"]});'
        f'out {max_results * 3};'
    )
    r = requests.post(OVERPASS_URL, data={"data": query}, timeout=40)
    r.raise_for_status()
    elements = r.json().get("elements", [])

    found = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        found.append({
            "name": name,
            "stars": tags.get("stars", "n/a"),
            "address": tags.get("addr:street", ""),
        })
        if len(found) >= max_results:
            break

    return {"city": loc["name"], "hotels": found}
