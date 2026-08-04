from weather import get_weather


def main() -> None:
    city = input("Enter a city: ").strip()

    try:
        result = get_weather(city)
        print(result)

    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()