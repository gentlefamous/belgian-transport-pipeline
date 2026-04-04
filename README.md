# Belgian Public Transport AI Intelligence Platform

[![CI Pipeline](https://github.com/gentlefamous/belgian-transport-pipeline/actions/workflows/ci.yml/badge.svg)]
(https://github.com/gentlefamous/belgian-transport-pipeline/actions/workflows/ci.yml)

An end-to-end data engineering pipeline that ingests real-time Belgian public transport data (SNCB trains + De Lijn buses), transforms it into analytical models, and serves insights through an interactive dashboard.

Built with the Belgian enterprise data stack: **Kafka** · **PySpark** · **Databricks** · **dbt** · **Airflow** · **Terraform** · **GitHub Actions**

---

## Architecture

*Architecture diagram will be added here*

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Ingestion | Python + iRail API + De Lijn GTFS-RT | Real-time Belgian transport data |
| Streaming | Apache Kafka (KRaft mode) | Event streaming pipeline |
| Processing | PySpark on Databricks | Data cleaning and transformation |
| Transformation | dbt Core | Dimensional modeling and testing |
| Orchestration | Apache Airflow | Pipeline scheduling and monitoring |
| Infrastructure | Terraform | Azure resources as code |
| CI/CD | GitHub Actions | Automated testing and deployment |
| Dashboard | Streamlit | Interactive analytics interface |
| Secrets | Azure Key Vault | GDPR-compliant credential management |

## Data Model

*Dimensional model diagram will be added here*

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker & docker-compose
- Terraform
- Azure account (free tier)
- Git

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
uv run python -m orchestration.run_pipeline

# 6. Launch the dashboard
uv run streamlit run dashboard/app.py
```

### Running Individual Components
```bash
# Ingest data from iRail API
uv run python -m ingestion.main

# Run PySpark cleaning
uv run python -m processing.spark_clean

# Run dbt models and tests
cd dbt_models/belgian_transport
dbt run
dbt test

# Run all unit tests
uv run pytest tests/ -v

# Run code quality checks
uv run flake8 ingestion/ processing/ orchestration/ tests/ --max-line-length 120
uv run black --check ingestion/ processing/ orchestration/ tests/ --line-length 120
```

### Tear Down
```bash
# Stop Kafka
docker compose down

# Destroy Azure resources (saves costs)
cd terraform && terraform destroy
```

## Problem Statement

Belgian train commuters face delays but lack accessible, data-driven insights into delay patterns. This project builds an end-to-end data pipeline that ingests real-time departure data from the SNCB/NMBS railway network, identifies delay patterns by station, time of day, and route, and serves interactive analytics through a live dashboard. The pipeline demonstrates production-grade data engineering practices including streaming ingestion, infrastructure-as-code, dimensional modeling, automated testing, and CI/CD.

## Project Structure
```
belgian-transport-pipeline/
├── .github/workflows/    # CI/CD pipelines
├── ingestion/            # Kafka producer + API scripts
├── processing/           # PySpark transformation jobs
├── dbt_models/           # dbt dimensional models + tests
├── orchestration/        # Airflow DAGs
├── dashboard/            # Streamlit app
├── terraform/            # Infrastructure as Code (Azure)
├── tests/                # Unit tests
├── DECISIONS.md          # Architectural decision log
└── README.md
```


## GDPR & Data Governance

This project processes publicly available transport schedule data from iRail and De Lijn. No personal data is collected or stored. Security measures implemented:

- All credentials stored in Azure Key Vault (never in code)
- `.gitignore` prevents secrets from being committed
- Secrets scanning enabled in CI pipeline
- Data retention policies documented

## Decisions

See [DECISIONS.md](DECISIONS.md) for detailed architectural decision records explaining every tool choice.

## License

MIT