import logging
import os

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.ingestion.bronze_writer import save_raw_response

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
) -> dict:
    """Fetch a single page of hourly measurements from OpenAQ."""

    api_key = os.getenv("OPENAQ_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAQ_API_KEY is missing from .env")

    with create_session() as session:
        response = session.get(
            f"{BASE_URL}/sensors/{sensor_id}/hours",
            headers={
                "X-API-Key": api_key,
                "Accept": "application/json",
            },
            params={
                "limit": limit,
                "page": page,
            },
            timeout=30,
        )

        response.raise_for_status()
        return response.json()


def ingest_hourly_measurements(
    sensor_id: int,
    max_pages: int = 3,
    limit: int = 100,
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


def main() -> None:
    """Run OpenAQ hourly measurement ingestion."""

    # Jakarta South — US Diplomatic Post
    sensor_id = 5047

    logger.info("Starting OpenAQ ingestion for sensor %s", sensor_id)

    total = ingest_hourly_measurements(
        sensor_id=sensor_id,
        max_pages=3,
        limit=100,
    )

    logger.info(
        "Ingestion completed | Sensor %s | Total records %s",
        sensor_id,
        total,
    )


if __name__ == "__main__":
    main()
