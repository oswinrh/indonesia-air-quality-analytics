"""Manage per-sensor ingestion watermarks."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

WATERMARK_DIR = Path("data/state")


def get_watermark(sensor_id: int) -> datetime | None:
    """Return the last successfully ingested timestamp for a sensor.

    Returns None when no watermark has been saved.
    """
    path = WATERMARK_DIR / f"sensor_{sensor_id}.json"

    if not path.exists():
        return None

    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    timestamp = datetime.fromisoformat(data["last_ingested_at"])

    if timestamp.tzinfo is None:
        raise ValueError("Watermark timestamp must include a timezone.")

    return timestamp.astimezone(UTC)


def save_watermark(sensor_id: int, timestamp: datetime) -> None:
    """Atomically persist a sensor's last ingested UTC timestamp."""
    if timestamp.tzinfo is None:
        raise ValueError("Watermark timestamp must include a timezone.")

    timestamp = timestamp.astimezone(UTC)

    WATERMARK_DIR.mkdir(parents=True, exist_ok=True)
    path = WATERMARK_DIR / f"sensor_{sensor_id}.json"
    temporary_path = path.with_suffix(".json.tmp")

    payload = {
        "sensor_id": sensor_id,
        "last_ingested_at": timestamp.isoformat().replace("+00:00", "Z"),
        "updated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }

    try:
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
            file.write("\n")

        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)
