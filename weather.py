from typing import Any

import requests


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def get_coordinates(city: str) -> dict[str, Any]:
    """Convert a city name into latitude and longitude."""

    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json",
    }

    response = requests.get(
        GEOCODING_URL,
        params=params,
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    results = data.get("results")

    if not results:
        raise ValueError(f"Could not find city: {city}")

    location = results[0]

    return {
        "name": location["name"],
        "country": location.get("country", "Unknown"),
        "latitude": location["latitude"],
        "longitude": location["longitude"],
    }


def get_weather(city: str) -> str:
    """Get the current weather for a city."""

    location = get_coordinates(city)

    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": (
            "temperature_2m,"
            "apparent_temperature,"
            "relative_humidity_2m,"
            "wind_speed_10m"
        ),
        "timezone": "auto",
    }

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    current = data.get("current")

    if not current:
        raise ValueError("Current weather data is unavailable.")

    return (
        f"Current weather in {location['name']}, "
        f"{location['country']}:\n"
        f"- Temperature: {current['temperature_2m']}°C\n"
        f"- Feels like: {current['apparent_temperature']}°C\n"
        f"- Humidity: {current['relative_humidity_2m']}%\n"
        f"- Wind speed: {current['wind_speed_10m']} km/h"
    )