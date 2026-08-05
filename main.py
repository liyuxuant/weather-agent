from agent import create_weather_agent


def main() -> None:
    """
    Run the weather agent in the terminal.
    """

    try:
        agent = create_weather_agent()

    except ValueError as error:
        print(f"Setup error: {error}")
        return

    print("=" * 50)
    print("Weather Agent")
    print("Ask about the current weather in any city.")
    print("Type 'quit' or 'exit' to stop.")
    print("=" * 50)

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in {"quit", "exit"}:
            print("Agent: Goodbye!")
            break

        if not user_input:
            print("Agent: Please enter a question.")
            continue

        try:
            result = agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": user_input,
                        }
                    ]
                }
            )

            final_message = result["messages"][-1]

            print(f"\nAgent: {final_message.content}")

        except Exception as error:
            print(f"\nAgent error: {error}")


if __name__ == "__main__":
    main()