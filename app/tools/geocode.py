import requests

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"


def geocode(city):
    """Turn a city name into coordinates using the Open-Meteo geocoding API."""
    r = requests.get(
        GEO_URL,
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=20,
    )
    r.raise_for_status()
    results = r.json().get("results")
    if not results:
        return None
    top = results[0]
    return {
        "name": top["name"],
        "country": top.get("country", ""),
        "lat": top["latitude"],
        "lon": top["longitude"],
    }
