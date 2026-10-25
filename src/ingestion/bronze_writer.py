import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze" / "openaq"


def save_raw_response(
    sensor_id: int,
    response_data: dict,
) -> Path:
    """Persist a raw OpenAQ response with ingestion metadata."""

    ingested_at = datetime.now(UTC)
    ingestion_id = uuid4().hex

    output_dir = BRONZE_DIR / f"sensor_id={sensor_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{ingested_at:%Y%m%dT%H%M%S%fZ}_{ingestion_id}.json"
    output_path = output_dir / filename

    payload = {
        "metadata": {
            "source": "openaq",
            "endpoint": f"/v3/sensors/{sensor_id}/hours",
            "sensor_id": sensor_id,
            "ingested_at_utc": ingested_at.isoformat(),
            "ingestion_id": ingestion_id,
        },
        "response": response_data,
    }

    # Write to a temporary file before publishing the snapshot.
    temporary_path = output_path.with_suffix(".tmp")

    try:
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

        temporary_path.replace(output_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    return output_path
