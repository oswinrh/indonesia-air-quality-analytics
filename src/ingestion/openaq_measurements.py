import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.openaq.org/v3"


def get_hourly_measurements(sensor_id: int, limit: int = 10):
    """Fetch hourly air quality measurements from OpenAQ."""

    api_key = os.getenv("OPENAQ_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAQ_API_KEY is missing from .env")

    url = f"{BASE_URL}/sensors/{sensor_id}/hours"

    response = requests.get(
        url,
        headers={
            "X-API-Key": api_key,
            "Accept": "application/json",
        },
        params={
            "limit": limit,
            "page": 1,
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def main():
    # Jakarta South — US Diplomatic Post
    sensor_id = 5047

    print(f"Fetching PM2.5 measurements for sensor {sensor_id}...\n")

    data = get_hourly_measurements(sensor_id)
    measurements = data.get("results", [])

    print(f"Retrieved {len(measurements)} measurements.\n")

    for measurement in measurements:
        period = measurement.get("period") or {}
        datetime_from = (period.get("datetimeFrom") or {}).get("utc")
        datetime_to = (period.get("datetimeTo") or {}).get("utc")

        print(f"PM2.5: {measurement.get('value')} µg/m³")
        print(f"From: {datetime_from}")
        print(f"To: {datetime_to}")
        print("-" * 40)


if __name__ == "__main__":
    main()
