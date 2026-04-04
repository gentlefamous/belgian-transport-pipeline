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
- uv (package manager)
- Docker & docker-compose
- Terraform
- Azure account (free tier)

### Setup
```bash
git clone https://github.com/gentlefamous/belgian-transport-pipeline.git
cd belgian-transport-pipeline
cp .env.example .env 
uv sync --extra dev
```

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