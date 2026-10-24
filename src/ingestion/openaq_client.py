import os

import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")
BASE_URL = "https://api.openaq.org/v3"


def get_indonesia_locations():
    """Retrieve air quality monitoring locations in Indonesia."""

    if not API_KEY:
        raise RuntimeError("OPENAQ_API_KEY is missing. Check your .env file.")

    headers = {
        "X-API-Key": API_KEY,
        "Accept": "application/json",
    }

    params = {
        "iso": "ID",
        "limit": 100,
        "page": 1,
    }

    response = requests.get(
        f"{BASE_URL}/locations",
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def main():
    print("Indonesia Air Quality Analytics")
    print("Checking PM2.5 sensor availability...\n")

    data = get_indonesia_locations()
    locations = data.get("results", [])

    print(f"Total locations retrieved: {len(locations)}\n")

    pm25_locations = []

    for location in locations:
        sensors = location.get("sensors") or []

        pm25_sensors = [
            sensor
            for sensor in sensors
            if sensor.get("parameter", {}).get("name") == "pm25"
        ]

        if not pm25_sensors:
            continue

        pm25_locations.append(location)

        print(f"Station: {location.get('name')}")
        print(f"Location ID: {location.get('id')}")
        print(f"City: {location.get('locality') or 'Unknown'}")
        print(f"PM2.5 sensors: {len(pm25_sensors)}")

        for sensor in pm25_sensors:
            print(f"  Sensor ID: {sensor.get('id')}")
            print(f"  Unit: {sensor.get('parameter', {}).get('units')}")

        print("-" * 50)

    print("\nSummary")
    print(f"Total locations: {len(locations)}")
    print(f"Locations with PM2.5 sensors: {len(pm25_locations)}")


if __name__ == "__main__":
    main()
