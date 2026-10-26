"""Tests for incremental OpenAQ ingestion."""

from datetime import UTC, datetime

import pytest

from src.ingestion import openaq_measurements


def test_first_run_saves_watermark(monkeypatch):
    """The first successful run should save its completed window."""

    end_time = datetime(2026, 10, 26, tzinfo=UTC)
    saved_watermarks = []

    monkeypatch.setattr(
        openaq_measurements,
        "get_watermark",
        lambda sensor_id: None,
    )

    def fake_fetch(**kwargs):
        assert kwargs["date_from"] == "2026-10-25T00:00:00Z"
        assert kwargs["date_to"] == "2026-10-26T00:00:00Z"
        return {"results": [{"value": 12.0}]}

    monkeypatch.setattr(
        openaq_measurements,
        "get_hourly_measurements",
        fake_fetch,
    )

    monkeypatch.setattr(
        openaq_measurements,
        "save_raw_response",
        lambda **kwargs: "bronze.json",
    )

    monkeypatch.setattr(
        openaq_measurements,
        "save_watermark",
        lambda sensor_id, timestamp: saved_watermarks.append(timestamp),
    )

    count = openaq_measurements.ingest_incrementally(
        sensor_id=6658670,
        initial_lookback_days=1,
        end_time=end_time,
    )

    assert count == 1
    assert saved_watermarks == [end_time]


def test_existing_watermark_uses_lookback(monkeypatch):
    """Subsequent runs should overlap the previous watermark."""

    previous = datetime(2026, 10, 25, tzinfo=UTC)
    end_time = datetime(2026, 10, 26, tzinfo=UTC)

    monkeypatch.setattr(
        openaq_measurements,
        "get_watermark",
        lambda sensor_id: previous,
    )

    def fake_fetch(**kwargs):
        assert kwargs["date_from"] == "2026-10-24T00:00:00Z"
        return {"results": []}

    monkeypatch.setattr(
        openaq_measurements,
        "get_hourly_measurements",
        fake_fetch,
    )

    monkeypatch.setattr(
        openaq_measurements,
        "save_watermark",
        lambda sensor_id, timestamp: None,
    )

    count = openaq_measurements.ingest_incrementally(
        sensor_id=6658670,
        lookback_hours=24,
        end_time=end_time,
    )

    assert count == 0


def test_api_failure_does_not_advance_watermark(monkeypatch):
    """Failed API requests must not update the watermark."""

    saved_watermarks = []

    monkeypatch.setattr(
        openaq_measurements,
        "get_watermark",
        lambda sensor_id: None,
    )

    def failing_fetch(**kwargs):
        raise RuntimeError("API unavailable")

    monkeypatch.setattr(
        openaq_measurements,
        "get_hourly_measurements",
        failing_fetch,
    )

    monkeypatch.setattr(
        openaq_measurements,
        "save_watermark",
        lambda sensor_id, timestamp: saved_watermarks.append(timestamp),
    )

    with pytest.raises(RuntimeError, match="API unavailable"):
        openaq_measurements.ingest_incrementally(
            sensor_id=6658670,
            end_time=datetime(2026, 10, 26, tzinfo=UTC),
        )

    assert saved_watermarks == []


def test_bronze_failure_does_not_advance_watermark(monkeypatch):
    """Failed Bronze persistence must not update the watermark."""

    saved_watermarks = []

    monkeypatch.setattr(
        openaq_measurements,
        "get_watermark",
        lambda sensor_id: None,
    )

    monkeypatch.setattr(
        openaq_measurements,
        "get_hourly_measurements",
        lambda **kwargs: {"results": [{"value": 12.0}]},
    )

    def failing_save(**kwargs):
        raise OSError("Disk write failed")

    monkeypatch.setattr(
        openaq_measurements,
        "save_raw_response",
        failing_save,
    )

    monkeypatch.setattr(
        openaq_measurements,
        "save_watermark",
        lambda sensor_id, timestamp: saved_watermarks.append(timestamp),
    )

    with pytest.raises(OSError, match="Disk write failed"):
        openaq_measurements.ingest_incrementally(
            sensor_id=6658670,
            end_time=datetime(2026, 10, 26, tzinfo=UTC),
        )

    assert saved_watermarks == []


def test_second_page_failure_does_not_advance_watermark(monkeypatch):
    """Keep the existing watermark when a later API page fails."""

    end_time = datetime(2026, 10, 26, tzinfo=UTC)
    saved_pages = []
    saved_watermarks = []

    monkeypatch.setattr(
        openaq_measurements,
        "get_watermark",
        lambda sensor_id: None,
    )

    def fake_fetch(**kwargs):
        if kwargs["page"] == 1:
            # A full page means pagination must continue.
            return {"results": [{"value": 12.0}, {"value": 15.0}]}

        raise RuntimeError("Page 2 request failed")

    monkeypatch.setattr(
        openaq_measurements,
        "get_hourly_measurements",
        fake_fetch,
    )

    def fake_save(**kwargs):
        saved_pages.append(kwargs["response_data"])
        return "bronze.json"

    monkeypatch.setattr(
        openaq_measurements,
        "save_raw_response",
        fake_save,
    )

    monkeypatch.setattr(
        openaq_measurements,
        "save_watermark",
        lambda sensor_id, timestamp: saved_watermarks.append(timestamp),
    )

    with pytest.raises(RuntimeError, match="Page 2 request failed"):
        openaq_measurements.ingest_incrementally(
            sensor_id=6658670,
            limit=2,
            initial_lookback_days=1,
            end_time=end_time,
        )

    # Page 1 was safely persisted before page 2 failed.
    assert len(saved_pages) == 1

    # The watermark must not advance after partial ingestion.
    assert saved_watermarks == []
