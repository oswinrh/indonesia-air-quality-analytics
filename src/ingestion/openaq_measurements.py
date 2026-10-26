import logging
import os
from datetime import UTC, datetime, timedelta

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.ingestion.bronze_writer import save_raw_response
from src.ingestion.watermark import get_watermark, save_watermark

load_dotenv()

BASE_URL = "https://api.openaq.org/v3"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    """Create an HTTP session with retry handling."""

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("https://", adapter)

    return session


def get_hourly_measurements(
    sensor_id: int,
    page: int = 1,
    limit: int = 100,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """Fetch hourly measurements with optional date filtering."""

    api_key = os.getenv("OPENAQ_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAQ_API_KEY is missing from .env")

    params = {
        "limit": limit,
        "page": page,
    }

    if date_from:
        params["datetime_from"] = date_from

    if date_to:
        params["datetime_to"] = date_to

    with create_session() as session:
        response = session.get(
            f"{BASE_URL}/sensors/{sensor_id}/hours",
            headers={
                "X-API-Key": api_key,
                "Accept": "application/json",
            },
            params=params,
            timeout=30,
        )

        response.raise_for_status()
        return response.json()


def ingest_hourly_measurements(
    sensor_id: int,
    max_pages: int = 3,
    limit: int = 100,
    date_from: str | None = None,
    date_to: str | None = None,
) -> int:
    """Fetch paginated measurements and persist each page to Bronze."""

    if max_pages < 1 or limit < 1:
        raise ValueError("max_pages and limit must be positive integers")

    total_measurements = 0

    for page in range(1, max_pages + 1):
        data = get_hourly_measurements(
            sensor_id=sensor_id,
            page=page,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
        )

        measurements = data.get("results", [])
        count = len(measurements)

        if count == 0:
            logger.info("No more measurements available.")
            break

        # Persist each page immediately to the Bronze layer
        output_path = save_raw_response(
            sensor_id=sensor_id,
            response_data=data,
        )

        total_measurements += count

        logger.info(
            "Sensor %s | Page %s | Records %s | Saved %s",
            sensor_id,
            page,
            count,
            output_path,
        )

        if count < limit:
            break

    return total_measurements


def ingest_incrementally(
    sensor_id: int,
    lookback_hours: int = 24,
    initial_lookback_days: int = 7,
    limit: int = 100,
    end_time: datetime | None = None,
) -> int:
    """Ingest a complete UTC time window using a per-sensor watermark.

    On the first run, fetch measurements from the initial lookback period.

    On subsequent runs, resume from the saved watermark with an overlap
    to accommodate delayed or corrected measurements.

    Advance the watermark only after every API page has been fetched
    and all non-empty responses have been persisted to Bronze.
    """

    if lookback_hours < 0 or initial_lookback_days < 1 or limit < 1:
        raise ValueError("Invalid incremental ingestion configuration.")

    # Use a fixed UTC endpoint for the current ingestion run.
    window_end = end_time or datetime.now(UTC)

    if window_end.tzinfo is None:
        raise ValueError("end_time must include a timezone.")

    window_end = window_end.astimezone(UTC)

    # Read the last successfully completed ingestion timestamp.
    previous_watermark = get_watermark(sensor_id)

    if previous_watermark is None:
        # First run: retrieve a configurable historical window.
        window_start = window_end - timedelta(days=initial_lookback_days)
    else:
        # Subsequent runs: re-fetch an overlap to capture delayed data.
        window_start = previous_watermark - timedelta(hours=lookback_hours)

    if window_start >= window_end:
        logger.info(
            "Sensor %s | No new ingestion window available.",
            sensor_id,
        )
        return 0

    date_from = window_start.isoformat().replace("+00:00", "Z")
    date_to = window_end.isoformat().replace("+00:00", "Z")

    logger.info(
        "Sensor %s | Incremental window %s to %s",
        sensor_id,
        date_from,
        date_to,
    )

    total_measurements = 0
    page = 1

    while True:
        # Retrieve one page from the requested UTC window.
        data = get_hourly_measurements(
            sensor_id=sensor_id,
            page=page,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
        )

        measurements = data.get("results", [])

        if not isinstance(measurements, list):
            raise TypeError("Invalid OpenAQ response: results must be a list.")

        count = len(measurements)

        if count == 0:
            break

        # Save each page before considering the ingestion successful.
        output_path = save_raw_response(
            sensor_id=sensor_id,
            response_data=data,
        )

        total_measurements += count

        logger.info(
            "Sensor %s | Page %s | Records %s | Saved %s",
            sensor_id,
            page,
            count,
            output_path,
        )

        # A short page indicates the end of the available results.
        if count < limit:
            break

        page += 1

    # Every requested page has been processed successfully.
    # Save the completed window boundary as the checkpoint.
    save_watermark(sensor_id, window_end)

    logger.info(
        "Sensor %s | Watermark updated to %s",
        sensor_id,
        date_to,
    )

    return total_measurements


def main():
    """Run incremental PM2.5 ingestion for an active OpenAQ sensor.

    Automatically calculate the ingestion window using the saved
    watermark and persist all retrieved measurements to Bronze.
    """

    # Active PM2.5 monitoring sensor in Depok, Indonesia.
    sensor_id = 6658670

    logger.info("Starting incremental ingestion for sensor %s", sensor_id)

    # The first run retrieves the previous seven days.
    # Subsequent runs overlap the previous 24 hours.
    total = ingest_incrementally(
        sensor_id=sensor_id,
        lookback_hours=24,
        initial_lookback_days=7,
        limit=100,
    )

    logger.info(
        "Incremental ingestion completed | Sensor %s | Total records %s",
        sensor_id,
        total,
    )


if __name__ == "__main__":
    main()
