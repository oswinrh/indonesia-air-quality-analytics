
from datetime import UTC, datetime

import duckdb
import pandas as pd


def main():
    print("Indonesia Air Quality Analytics")
    print("Starting data pipeline...")

    # Sample data for testing the pipeline
    data = {
        "city": ["Jakarta", "Bandung", "Surabaya", "Medan", "Semarang"],
        "pm25": [42.5, 28.3, 35.1, 31.8, 26.4],
    }

    df = pd.DataFrame(data)

    # Load data into DuckDB
    con = duckdb.connect(":memory:")
    con.register("air_quality", df)

    result = con.execute("""
        SELECT
            city,
            pm25
        FROM air_quality
        ORDER BY pm25 DESC
    """).df()

    print("\nSample air quality measurements:")
    print(result.to_string(index=False))

    print("\nPipeline completed successfully!")
    print("Timestamp:", datetime.now(UTC).isoformat())

    con.close()


if __name__ == "__main__":
    main()
