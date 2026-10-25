# Indonesia Air Quality Analytics

An open-source, end-to-end data engineering and analytics project exploring air quality across Indonesia using publicly accessible environmental data.

The project aims to transform raw air quality measurements into reliable, analysis-ready datasets, interactive visualizations, and actionable insights through modern data engineering, analytics, and machine learning practices.

## Project Objectives

- Build a scalable and reproducible data pipeline for Indonesian air quality data.
- Apply modern data engineering practices, including layered data architecture, data quality checks, and automated testing.
- Analyze historical PM2.5 concentrations, trends, and geographical differences.
- Develop interactive dashboards to make environmental data more accessible.
- Explore forecasting and AI-assisted analytics as future capabilities.

## Architecture

The project follows a Medallion Architecture, separating raw data ingestion, transformation, and analytical consumption.

```text
1. OpenAQ API
2. Data Ingestion (Python)
3. Bronze Layer (Raw JSON)
4. Silver Layer (Cleaned & Standardized Data - DuckDB, Pandas) [TBD]
5. Gold Layer (Analytical Data Models - DuckDB, SQL) [TBD]
6. Dashboards & Analytics (Metabase / Looker Studio) [TBD]
7. ML Forecasting & AI-Assisted Analytics (scikit-learn / XGBoost, LLM / RAG) [TBD]
```

The current implementation covers OpenAQ ingestion and Bronze-layer storage. Downstream transformations, dashboards, machine learning, and AI-assisted analytics are planned or exploratory capabilities.

### Bronze Layer — Implemented

Responsible for ingesting and preserving raw API responses.

Current capabilities:

- OpenAQ API v3 integration with API key authentication.
- Hourly PM2.5 measurement ingestion.
- Paginated API retrieval.
- HTTP retry configuration with exponential backoff for transient failures.
- Raw JSON persistence with ingestion metadata.
- Unique filenames to preserve individual ingestion snapshots.
- Automated unit tests.

### Silver Layer — Planned

Will standardize and validate ingested measurements, including:

- Timestamp normalization to UTC.
- Data type validation and standardization.
- Duplicate detection and handling.
- Missing-value and data quality checks.
- Structured datasets for downstream processing.

### Gold Layer — Planned

Will provide analytics-ready datasets for:

- Daily and monthly PM2.5 trends.
- City and monitoring-station comparisons.
- Air quality threshold analysis.
- Historical trends and seasonal patterns.

## Technology Stack

| Category | Technologies | Status |
|---|---|---|
| Programming | Python 3.12, SQL | Python implemented; SQL planned |
| Data Source | OpenAQ API v3 | Implemented |
| Data Ingestion | Python, Requests | Implemented |
| Data Storage | JSON, DuckDB | JSON implemented; DuckDB planned for pipeline storage |
| Data Processing | Pandas, DuckDB | Planned for Silver/Gold layers |
| Data Architecture | Medallion (Bronze, Silver, Gold) | Bronze implemented |
| Data Quality & Testing | pytest, SQL validation | pytest implemented; SQL validation planned |
| Dashboard & BI | Metabase / Looker Studio | Evaluating |
| Machine Learning | scikit-learn, XGBoost | Planned |
| GenAI & LLM | LLM APIs, RAG | Exploratory |
| CI/CD | GitHub Actions | Planned |
| Environment Management | uv, python-dotenv | Implemented |
| Code Quality | Ruff | Implemented |
| Version Control | Git, GitHub | Implemented |

## Getting Started

### Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- An [OpenAQ API key](https://openaq.org/)

### 1. Clone the repository

```bash
git clone https://github.com/oswinrh/indonesia-air-quality-analytics.git
cd indonesia-air-quality-analytics
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Add your OpenAQ API key to `.env`:

```dotenv
OPENAQ_API_KEY=your_api_key_here
```

Never commit your actual API key to Git.

### 4. Run the ingestion pipeline

```bash
uv run python -m src.ingestion.openaq_measurements
```

The pipeline currently ingests hourly PM2.5 measurements from a Jakarta South monitoring station.

Raw API responses are saved under:

```text
data/bronze/openaq/sensor_id=5047/
```

Each saved JSON snapshot includes ingestion metadata and the original API response.

### 5. Run automated tests

```bash
uv run python -m pytest -v
```

### 6. Run code quality checks

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

## Project Structure

```text
indonesia-air-quality-analytics/
├── src/
│   ├── ingestion/
│   │   ├── openaq_client.py
│   │   ├── openaq_measurements.py
│   │   └── bronze_writer.py
│   └── main.py
├── tests/
│   ├── test_bronze_writer.py
│   └── test_openaq_measurements.py
├── data/
│   └── bronze/                 # Generated locally; Git-ignored
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

## Roadmap

- [x] Initialize repository and development environment.
- [x] Integrate OpenAQ API v3.
- [x] Implement raw Bronze-layer storage.
- [x] Support paginated hourly measurement ingestion.
- [x] Configure HTTP retries with exponential backoff.
- [x] Add automated ingestion and persistence tests.
- [ ] Implement date-range filtering and incremental ingestion.
- [ ] Develop Silver-layer transformations and data quality validation.
- [ ] Build Gold-layer analytical models.
- [ ] Create interactive air quality dashboards.
- [ ] Implement CI/CD using GitHub Actions.
- [ ] Explore PM2.5 forecasting and machine learning.
- [ ] Explore AI-assisted environmental analytics.

## Data Sources and Limitations

Air quality measurements are sourced from [OpenAQ](https://openaq.org/), which provides access to environmental monitoring data collected by various data providers.

The project currently focuses on PM2.5 measurements from a selected monitoring station in Jakarta.

Monitoring coverage, data availability, measurement frequency, and historical completeness vary across locations. Results should not be interpreted as a complete representation of air quality throughout Indonesia.

## License

License to be determined.
