# Rough budget estimation. Prices are not in OSM data, so we use
# reasonable defaults for central-Europe city trips. Numbers can be
# overridden by the agent if the user gives more detail.

DEFAULTS = {
    "hotel_per_night": 80,    # EUR, mid-range double room
    "food_per_day": 35,       # EUR per person
    "fuel_per_km": 0.12,      # EUR (car) - used if a distance is given
    "activities_per_day": 20, # EUR per person
}


def budget(days, people=1, distance_km=0, hotel_per_night=None,
           food_per_day=None, max_budget=None):
    days = int(days)
    people = int(people)

    hotel = hotel_per_night if hotel_per_night is not None else DEFAULTS["hotel_per_night"]
    food = food_per_day if food_per_day is not None else DEFAULTS["food_per_day"]

    nights = max(days - 1, 0)
    hotel_total = hotel * nights
    food_total = food * days * people
    activities_total = DEFAULTS["activities_per_day"] * days * people
    transport_total = round(distance_km * 2 * DEFAULTS["fuel_per_km"], 1)  # round trip

    total = round(hotel_total + food_total + activities_total + transport_total, 1)

    result = {
        "days": days,
        "people": people,
        "hotel_total": hotel_total,
        "food_total": food_total,
        "activities_total": activities_total,
        "transport_total": transport_total,
        "estimated_total": total,
    }
    if max_budget is not None:
        result["max_budget"] = max_budget
        result["within_budget"] = total <= float(max_budget)
        result["remaining"] = round(float(max_budget) - total, 1)
    return result
