from typing import Literal, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from weather import get_weather


load_dotenv()
from langgraph.graph import END, START, StateGraph

from weather import get_weather


class AgentState(TypedDict):
    user_input: str
    action: str
    response: str


model = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
)


def input_node(state: AgentState) -> AgentState:
    """
    Get input from the user.
    """

    user_input = input("\nYou: ").strip()

    return {
        **state,
        "user_input": user_input,
    }


def decision_node(state: AgentState) -> AgentState:
    """
    Let the LLM decide what action the user wants.
    """

    prompt = f"""
You are an intent classifier.

Classify the user's input into exactly one of these categories:

weather
exit
other

Rules:

weather:
The user wants to know current weather information
for a city.

exit:
The user wants to stop, quit, leave, or end the program.

other:
Anything else.

User input:
{state["user_input"]}

Return only one word:
weather
exit
other
"""

    response = model.invoke(prompt)

    action = response.content.strip().lower()

    return {
        **state,
        "action": action,
    }


def weather_node(state: AgentState) -> AgentState:
    """
    Ask the LLM to extract the city and call the weather function.
    """

    prompt = f"""
Extract only the city name from this user request.

User request:
{state["user_input"]}

Return only the city name.
"""

    response = model.invoke(prompt)

    city = response.content.strip()

    try:
        weather = get_weather(city)

        print(f"\nAgent:\n{weather}")

        return {
            **state,
            "response": weather,
        }

    except Exception as error:
        message = f"Could not get weather: {error}"

        print(f"\nAgent: {message}")

        return {
            **state,
            "response": message,
        }


def other_node(state: AgentState) -> AgentState:
    """
    Ignore unsupported requests.
    """

    print("\nAgent: Request ignored.")

    return {
        **state,
        "response": "Request ignored.",
    }


def route_action(
    state: AgentState,
) -> Literal["weather", "exit", "other"]:
    """
    Route based on the LLM's decision.
    """

    action = state["action"]

    if action == "weather":
        return "weather"

    if action == "exit":
        return "exit"

    return "other"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("input", input_node)
    graph.add_node("decision", decision_node)
    graph.add_node("weather", weather_node)
    graph.add_node("other", other_node)

    graph.add_edge(START, "input")
    graph.add_edge("input", "decision")

    graph.add_conditional_edges(
        "decision",
        route_action,
        {
            "weather": "weather",
            "exit": END,
            "other": "other",
        },
    )

    graph.add_edge("weather", "input")
    graph.add_edge("other", "input")

    return graph.compile()


weather_agent = build_graph()