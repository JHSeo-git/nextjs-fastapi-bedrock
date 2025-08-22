import random
from typing import Literal

from langchain_core.tools import tool


@tool(
    name_or_callable="get_current_weather",
    description="Get the current weather in a given location",
)
def get_current_weather(location: str, unit: Literal["celsius", "fahrenheit"]) -> str:
    """Get the current weather in a given location.

    Args:
        location: The city and state, e.g. "San Francisco, CA".
        unit: The temperature unit, either "celsius" or "fahrenheit".
    """
    return _get_current_weather(location, unit)


def _get_current_weather(location, unit="fahrenheit"):
    if unit == "celsius":
        temperature = random.randint(-34, 43)
    else:
        temperature = random.randint(-30, 110)

    return {
        "temperature": temperature,
        "unit": unit,
        "location": location,
    }
