import os
from datetime import UTC, datetime, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")
BASE_URL = "https://api.openaq.org/v3"


def get_indonesia_locations():
    """Retrieve all available air quality monitoring locations in Indonesia."""

    if not API_KEY:
        raise RuntimeError("OPENAQ_API_KEY is missing. Check your .env file.")

    headers = {
        "X-API-Key": API_KEY,
        "Accept": "application/json",
    }

    locations = []
    page = 1
    limit = 100

    while True:
        response = requests.get(
            f"{BASE_URL}/locations",
            headers=headers,
            params={
                "iso": "ID",
                "limit": limit,
                "page": page,
            },
            timeout=30,
        )
        response.raise_for_status()

        results = response.json().get("results", [])

        if not results:
            break

        locations.extend(results)

        if len(results) < limit:
            break

        page += 1

    return locations


def main():
    print("Indonesia Air Quality Analytics")
    print("Discovering Indonesian PM2.5 monitoring stations...\n")

    locations = get_indonesia_locations()

    now = datetime.now(UTC)
    freshness_threshold = now - timedelta(days=7)

    total_pm25 = 0
    active_locations = []

    for location in locations:
        sensors = location.get("sensors") or []

        pm25_sensors = [
            sensor
            for sensor in sensors
            if sensor.get("parameter", {}).get("name") == "pm25"
        ]

        if not pm25_sensors:
            continue

        total_pm25 += len(pm25_sensors)

        last_record = location.get("datetimeLast")
        last_utc = (last_record or {}).get("utc")

        if not last_utc:
            continue

        last_datetime = datetime.fromisoformat(last_utc)

        if last_datetime < freshness_threshold:
            continue

        active_locations.append(location)

        print(f"Station: {location.get('name')}")
        print(f"Location ID: {location.get('id')}")
        print(f"Last measurement: {last_utc}")

        for sensor in pm25_sensors:
            print(f"  PM2.5 sensor ID: {sensor.get('id')}")

        print("-" * 50)

    print("\nSummary")
    print(f"Total Indonesian locations: {len(locations)}")
    print(f"Total PM2.5 sensors: {total_pm25}")
    print(f"Locations reporting within 7 days: {len(active_locations)}")


if __name__ == "__main__":
    main()
