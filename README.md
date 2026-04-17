# 🚂 Belgian Public Transport Delay Analytics Platform

[![CI Pipeline](https://github.com/gentlefamous/belgian-transport-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/gentlefamous/belgian-transport-pipeline/actions/workflows/ci.yml)

## Problem Statement

Belgian train commuters face frequent delays but lack accessible, data-driven insights into delay patterns. This project builds an end-to-end data pipeline that ingests real-time departure data from the SNCB/NMBS railway network, identifies delay patterns by station, time of day, and route, and serves interactive analytics through a live dashboard.

The pipeline demonstrates production-grade data engineering practices including streaming ingestion, infrastructure-as-code, dimensional modeling, automated testing, and CI/CD.

## Architecture

- **Source:** iRail API provides live SNCB departure data.
- **Streaming layer:** Apache Kafka in KRaft mode ingests event streams through the `departures` topic and routes failures to a `dead_letter_queue`.
- **Storage layer:** Azure Data Lake Storage Gen2 stores raw and processed datasets for traceability and downstream processing.
- **Processing layer:** PySpark performs cleaning, deduplication, validation, and enrichment.
- **Transformation layer:** dbt Core with DuckDB models the data into staging, fact, dimension, and mart tables.
- **Presentation layer:** Streamlit exposes KPIs, delay heatmaps, and trend analysis in a dashboard.
- **Orchestration:** Apache Airflow
- **Infrastructure:** Terraform on Azure
- **CI/CD:** GitHub Actions


## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Ingestion | Python + iRail API | Real-time SNCB train departure data |
| Streaming | Apache Kafka (KRaft) | Event streaming with dead-letter queue |
| Storage | Azure Data Lake Gen2 | Raw and processed data lake containers |
| Processing | PySpark | Cleaning, deduplication, derived columns |
| Transformation | dbt Core | Dimensional modeling with 16 automated tests |
| Warehouse | DuckDB | Analytical query engine (dbt models are backend-portable to Databricks) |
| Orchestration | Apache Airflow | Pipeline scheduling with TaskFlow API |
| Infrastructure | Terraform | Azure resources as code with remote state |
| CI/CD | GitHub Actions | Linting, testing, Terraform validation on every push |
| Dashboard | Streamlit + Plotly | Interactive delay analytics with 5 chart types |
| Secrets | Azure Key Vault | GDPR-compliant credential management |

## Dashboard

The dashboard displays delay analytics across 5 major Belgian stations:

- **KPI cards** — total departures, delayed trains, delay rate, average delay
- **Delay by station** — horizontal bar chart ranking stations by delay rate
- **Delay by hour** — line chart showing when delays peak during the day
- **Delay by time period** — bar chart comparing morning, afternoon, evening, night
- **Delay heatmap** — station × hour matrix showing delay hotspots
- **Occupancy analysis** — relationship between crowding and delays

## Data Model

**Grain:** `fct_delays` has one row per departure event. `mart_delay_summary` aggregates to one row per station × hour combination.

**Partitioning:** `fct_delays` is partitioned by `departure_date` for efficient date-range filtering.

| Table | Type | Description |
|-------|------|-------------|
| `stg_departures` | Staging (view) | Cleaned and typed raw departure data with surrogate key |
| `dim_stations` | Dimension | One row per unique station with primary name extraction |
| `dim_time` | Dimension | One row per hour of day with peak hour and time period flags |
| `fct_delays` | Fact | One row per departure event — delays, cancellations, vehicle info |
| `mart_delay_summary` | Mart | Pre-computed delay metrics per station per hour for dashboard |

## Data Quality

Data quality is enforced at every layer:

- **Ingestion:** JSON schema validation before Kafka publish. Failed messages routed to dead-letter queue.
- **Processing:** PySpark deduplication on composite key (station_id + vehicle_id + scheduled_time). Null handling and type enforcement.
- **Transformation:** 16 dbt tests — unique keys, not_null constraints, accepted values, referential integrity between facts and dimensions.
- **CI/CD:** All 14 Python unit tests and 16 dbt tests run on every push via GitHub Actions.

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker & docker-compose
- Terraform
- Azure account (free tier)
- Java JDK 17 (for PySpark)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/gentlefamous/belgian-transport-pipeline.git
cd belgian-transport-pipeline

# 2. Set up environment
cp .env.example .env          # Fill in your Azure values
uv sync --extra dev           # Install all dependencies

# 3. Provision Azure infrastructure
cd terraform
terraform init
terraform apply               # Type 'yes' to confirm
cd ..

# 4. Start Kafka
docker compose up -d

# 5. Run the full pipeline
make pipeline

# 6. Launch the dashboard
make dashboard
```

### Available Make Commands

```bash
make help        # Show all commands
make ingest      # Fetch data from iRail API
make process     # Run PySpark cleaning
make dbt-run     # Build dbt models
make dbt-test    # Run dbt data quality tests
make pipeline    # Run full end-to-end pipeline
make dashboard   # Launch Streamlit dashboard
make test        # Run Python unit tests
make lint        # Check code quality
make format      # Auto-format code
make clean       # Stop Kafka + destroy Azure resources
```

### Tear Down

```bash
# Stop Kafka and destroy Azure resources
make clean
```

## Project Structure

```
belgian-transport-pipeline/
├── .github/workflows/ci.yml    # CI pipeline: lint + test + Terraform
├── ingestion/                   # iRail API client, Kafka producer/consumer
├── processing/                  # PySpark cleaning and deduplication
├── dbt_models/                  # dbt dimensional models + 16 tests
├── orchestration/               # Airflow DAG + local pipeline runner
├── dashboard/                   # Streamlit analytics dashboard
├── terraform/                   # Azure IaC (ADLS, Key Vault, Databricks, remote state)
├── tests/                       # 14 Python unit tests
├── docker-compose.yml           # Kafka (KRaft mode)
├── Makefile                     # Project commands
├── DECISIONS.md                 # 8 architectural decision records
└── README.md
```

## GDPR & Data Governance

This project processes publicly available transport schedule data from iRail. No personal data is collected or stored. Security measures implemented:

- All credentials stored in Azure Key Vault (never in code)
- `.gitignore` prevents secrets from being committed
- Secrets scanning enabled in CI pipeline
- ADLS containers set to private access
- Data retention policies documented

## Architectural Decisions

See [DECISIONS.md](DECISIONS.md) for detailed records explaining every tool choice, including:

1. Mono-repo with domain folders
2. uv + pyproject.toml over pip
3. Git Bash on Windows
4. Terraform remote state in Azure
5. Kafka with KRaft mode (no Zookeeper)
6. Batch consumer with dual flush triggers
7. Airflow with TaskFlow API
8. DuckDB for local dbt development

## License

MIT