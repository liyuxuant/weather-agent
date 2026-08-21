from dotenv import load_dotenv

# Load .env BEFORE importing the agent.
load_dotenv()

from agent import weather_agent


def main():
    print("=" * 60)
    print("LinkedIn Job Search Agent")
    print("=" * 60)

    print("\nExamples:")
    print("- Find me 3 Python Developer jobs on LinkedIn")
    print("- Search LinkedIn for 5 Java Engineer jobs")
    print("- Find 2 Data Engineer jobs")

    print("\nType 'exit' to stop.")

    while True:
        print()

        user_input = input("You: ").strip()

        if user_input.lower() in {
            "exit",
            "quit",
        }:
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            result = weather_agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": user_input,
                        }
                    ]
                }
            )

            messages = result["messages"]
            final_message = messages[-1]

            print("\nAgent:")
            print(final_message.content)

        except Exception as error:
            print("\nAgent error:")
            print(error)


if __name__ == "__main__":
    main()