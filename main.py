from agent import weather_agent


def main() -> None:
    print("=" * 50)
    print("Weather Agent")
    print("Ask about weather or ask the agent to exit.")
    print("=" * 50)

    initial_state = {
        "user_input": "",
        "action": "",
        "response": "",
    }

    weather_agent.invoke(initial_state)

    print("\nAgent: Goodbye!")


if __name__ == "__main__":
    main()