"""Interactive command-line weather prediction launcher.

Run from this folder with:
    python interactive_predict.py
"""

from predict import list_known_cities, predict_weather


def ask_optional_float(label: str):
    """Prompt until the user enters a valid number."""
    while True:
        value = input(label).strip()
        try:
            return float(value)
        except ValueError:
            print("Please enter a number, for example 19.0760.")


def main():
    cities = list_known_cities()
    print("Weather Prediction System")
    print("Known cities: " + ", ".join(cities))
    print("Type 'quit' at the city prompt to close.\n")

    while True:
        city = input("City or place name: ").strip()
        if city.lower() in {"quit", "exit", "q"}:
            print("Goodbye.")
            break
        if not city:
            print("Please enter a city or place name.\n")
            continue

        # Known cities can be entered in any letter case.
        city = {known.lower(): known for known in cities}.get(city.lower(), city)

        date = input("Date (YYYY-MM-DD): ").strip()
        time = input("Time (HH:MM, press Enter for 12:00): ").strip() or "12:00"

        kwargs = {}
        if city not in cities:
            print("This is a new place, so its coordinates are needed.")
            kwargs["latitude"] = ask_optional_float("Latitude: ")
            kwargs["longitude"] = ask_optional_float("Longitude: ")

        try:
            result = predict_weather(city=city, date=date, time=time, **kwargs)
        except (ValueError, FileNotFoundError) as error:
            print(f"\nCould not create a prediction: {error}\n")
            continue

        print(f"\nPrediction for {city} on {date} at {time}")
        print(f"  Temperature:       {result['temperature_2m']} °C")
        print(f"  Humidity:          {result['relative_humidity_2m']} %")
        print(f"  Rainfall:          {result['rain']} mm")
        print(f"  Wind speed:        {result['wind_speed_10m']} km/h")
        print(f"  Cloud cover:       {result['cloud_cover']} %")
        print(f"  Solar radiation:   {result['shortwave_radiation']} W/m²\n")


if __name__ == "__main__":
    main()
