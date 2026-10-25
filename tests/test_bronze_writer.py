import json

from src.ingestion import bronze_writer


def test_save_raw_response(tmp_path, monkeypatch):
    """Verify that Bronze snapshots are saved correctly."""

    # Redirect output to a temporary test directory
    monkeypatch.setattr(
        bronze_writer,
        "BRONZE_DIR",
        tmp_path,
    )

    sample_response = {
        "results": [
            {
                "value": 25.5,
                "period": {"datetimeFrom": {"utc": "2026-10-25T08:00:00Z"}},
            }
        ]
    }

    output_path = bronze_writer.save_raw_response(
        sensor_id=5047,
        response_data=sample_response,
    )

    # Verify file creation
    assert output_path.exists()
    assert output_path.suffix == ".json"

    # Read saved JSON
    saved_data = json.loads(output_path.read_text(encoding="utf-8"))

    # Verify ingestion metadata
    metadata = saved_data["metadata"]

    assert metadata["source"] == "openaq"
    assert metadata["sensor_id"] == 5047
    assert metadata["endpoint"] == "/v3/sensors/5047/hours"
    assert metadata["ingestion_id"]
    assert metadata["ingested_at_utc"]

    # Verify the original API response is preserved
    assert saved_data["response"] == sample_response
