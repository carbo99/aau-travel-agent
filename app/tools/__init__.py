from .weather import weather
from .routing import route
from .hotels import hotels
from .budget import budget
from .geocode import geocode

# registry the agent uses to look up and call tools by name
TOOLS = {
    "weather": weather,
    "route": route,
    "hotels": hotels,
    "budget": budget,
    "geocode": geocode,
}
