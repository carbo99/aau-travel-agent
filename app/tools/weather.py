import requests
from .geocode import geocode

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# weather codes -> short text (subset of WMO codes)
WMO = {
    0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "fog", 51: "light drizzle", 61: "rain", 63: "rain",
    65: "heavy rain", 71: "snow", 73: "snow", 75: "heavy snow",
    80: "showers", 81: "showers", 95: "thunderstorm",
}


def weather(city, days=3):
    loc = geocode(city)
    if not loc:
        return {"error": f"could not find location: {city}"}

    r = requests.get(
        FORECAST_URL,
        params={
            "latitude": loc["lat"],
            "longitude": loc["lon"],
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "forecast_days": min(max(days, 1), 7),
            "timezone": "auto",
        },
        timeout=20,
    )
    r.raise_for_status()
    d = r.json()["daily"]

    forecast = []
    for i in range(len(d["time"])):
        code = d["weather_code"][i]
        forecast.append({
            "date": d["time"][i],
            "t_max": d["temperature_2m_max"][i],
            "t_min": d["temperature_2m_min"][i],
            "rain_mm": d["precipitation_sum"][i],
            "summary": WMO.get(code, "unknown"),
        })
    return {"city": loc["name"], "forecast": forecast}
