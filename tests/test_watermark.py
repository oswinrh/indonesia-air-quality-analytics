"""Tests for per-sensor watermark persistence."""

from datetime import UTC, datetime

import pytest

from src.ingestion import watermark


def test_missing_watermark_returns_none(tmp_path, monkeypatch):
    """A new sensor should have no existing watermark."""
    monkeypatch.setattr(watermark, "WATERMARK_DIR", tmp_path)

    assert watermark.get_watermark(6658670) is None


def test_save_and_read_watermark(tmp_path, monkeypatch):
    """A saved watermark should be retrieved in UTC."""
    monkeypatch.setattr(watermark, "WATERMARK_DIR", tmp_path)

    timestamp = datetime(2026, 10, 25, 23, 0, tzinfo=UTC)

    watermark.save_watermark(6658670, timestamp)

    assert watermark.get_watermark(6658670) == timestamp


def test_watermarks_are_sensor_specific(tmp_path, monkeypatch):
    """Saving one sensor's state must not affect another sensor."""
    monkeypatch.setattr(watermark, "WATERMARK_DIR", tmp_path)

    timestamp = datetime(2026, 10, 25, tzinfo=UTC)

    watermark.save_watermark(6658670, timestamp)

    assert watermark.get_watermark(14336462) is None


def test_naive_timestamp_is_rejected(tmp_path, monkeypatch):
    """Watermarks must use timezone-aware timestamps."""
    monkeypatch.setattr(watermark, "WATERMARK_DIR", tmp_path)

    with pytest.raises(ValueError, match="timezone"):
        watermark.save_watermark(6658670, datetime(2026, 10, 25))
