from unittest.mock import patch

import pytest

from src.ingestion import openaq_measurements


@pytest.fixture
def mock_api_key(monkeypatch):
    monkeypatch.setenv("OPENAQ_API_KEY", "test-api-key")


def test_get_hourly_measurements(mock_api_key):
    """Verify API endpoint, authentication, and pagination parameters."""

    mock_data = {"results": [{"value": 25.5}]}

    with patch("src.ingestion.openaq_measurements.create_session") as mock_session:
        mock_get = mock_session.return_value.__enter__.return_value.get
        mock_get.return_value.json.return_value = mock_data

        result = openaq_measurements.get_hourly_measurements(
            sensor_id=5047,
            page=2,
            limit=100,
        )

        assert result == mock_data

        mock_get.assert_called_once_with(
            "https://api.openaq.org/v3/sensors/5047/hours",
            headers={
                "X-API-Key": "test-api-key",
                "Accept": "application/json",
            },
            params={
                "limit": 100,
                "page": 2,
            },
            timeout=30,
        )


def test_ingest_multiple_pages(monkeypatch):
    """Verify pagination and Bronze persistence."""

    pages = [
        {"results": [{"value": 10}, {"value": 20}]},
        {"results": [{"value": 30}]},
    ]

    saved_pages = []

    def fake_fetch(sensor_id, page, limit, date_from=None, date_to=None):
        return pages[page - 1]

    def fake_save(sensor_id, response_data):
        saved_pages.append(response_data)
        return "test.json"

    monkeypatch.setattr(
        openaq_measurements,
        "get_hourly_measurements",
        fake_fetch,
    )
    monkeypatch.setattr(
        openaq_measurements,
        "save_raw_response",
        fake_save,
    )

    total = openaq_measurements.ingest_hourly_measurements(
        sensor_id=5047,
        max_pages=5,
        limit=2,
    )

    assert total == 3
    assert len(saved_pages) == 2
    assert saved_pages == pages


def test_ingest_empty_page(monkeypatch):
    """Verify ingestion stops when the API returns no measurements."""

    monkeypatch.setattr(
        openaq_measurements,
        "get_hourly_measurements",
        lambda sensor_id, page, limit, date_from=None, date_to=None: {"results": []},
    )

    total = openaq_measurements.ingest_hourly_measurements(
        sensor_id=5047,
    )

    assert total == 0


def test_invalid_pagination():
    """Verify invalid pagination arguments are rejected."""

    with pytest.raises(ValueError):
        openaq_measurements.ingest_hourly_measurements(
            sensor_id=5047,
            max_pages=0,
        )


def test_create_session_retry_configuration():
    """Verify retries, backoff, and retryable HTTP status codes."""

    session = openaq_measurements.create_session()

    try:
        adapter = session.get_adapter("https://")
        retry = adapter.max_retries

        assert retry.total == 3
        assert retry.backoff_factor == 1
        assert set(retry.status_forcelist) == {429, 500, 502, 503, 504}
        assert set(retry.allowed_methods) == {"GET"}
        assert retry.respect_retry_after_header is True
    finally:
        session.close()


def test_create_session_does_not_retry_unauthorized():
    """Verify authentication failures are not retried."""

    session = openaq_measurements.create_session()

    try:
        retry = session.get_adapter("https://").max_retries

        assert 401 not in retry.status_forcelist
        assert 403 not in retry.status_forcelist
    finally:
        session.close()
