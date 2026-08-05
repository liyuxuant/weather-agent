import os
from typing import Any

import requests
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from weather import get_weather


load_dotenv()


@tool
def weather_tool(city: str) -> str:
    """
    Get the current weather for a city.

    Args:
        city: The city name, such as Durham, Beijing, or London.
    """

    try:
        return get_weather(city)

    except ValueError as error:
        return f"Could not get weather: {error}"

    except requests.Timeout:
        return "The weather request timed out."

    except requests.RequestException as error:
        return f"Network error: {error}"

    except KeyError as error:
        return f"Unexpected weather data: missing {error}"


def create_weather_agent() -> Any:
    """
    Create and return the weather agent.
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing. "
            "Please add it to the .env file."
        )

    model = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
    )

    agent = create_agent(
        model=model,
        tools=[weather_tool],
        system_prompt=(
            "You are a helpful weather assistant. "
            "When the user asks about current weather, "
            "temperature, humidity, or wind, use weather_tool. "
            "Do not invent weather information. "
            "Use the tool observation to answer."
        ),
    )

    return agent