# Architectural Decision Log

This document records key technical decisions made during this project, the alternatives considered, and the reasoning behind each choice.

---

## Decision 1: Project Structure — Mono-repo with Domain Folders

**Date:** 2026-03-22
**Status:** Accepted

**Context:** Needed to decide how to organize the codebase — a single repository with domain-based folders, or multiple repositories per component.

**Decision:** Single repository with domain folders (ingestion/, processing/, dbt_models/, orchestration/, dashboard/, terraform/, tests/).

**Alternatives considered:**
- Multi-repo (separate repos for ingestion, processing, dashboard) — rejected because it adds CI/CD complexity without benefit for a single-developer project.
- Flat structure (all files in root) — rejected because it becomes unnavigable as the project grows.

**Reasoning:** A mono-repo with clear domain folders mirrors how production teams at Belgian consulting firms organize projects. Each folder has a single responsibility. A recruiter opening this repo can immediately understand the architecture from the folder names alone.

---

## Decision 2: uv + pyproject.toml over pip + requirements.txt

**Date:** 2026-03-22
**Status:** Accepted

**Context:** Needed to choose a Python dependency management approach.

**Decision:** Use uv as the package manager with pyproject.toml as the single configuration file.

**Alternatives considered:**
- pip + requirements.txt — rejected because it requires separate config files for each tool (pytest.ini, .flake8, setup.py) and has slower dependency resolution.
- Poetry + pyproject.toml — viable, but uv is significantly faster and gaining rapid adoption in the Python ecosystem.

**Reasoning:** pyproject.toml is the official Python packaging standard (PEP 621). It consolidates project metadata, dependencies, and tool configuration in one file. uv provides fast, reliable dependency resolution. Separating dev dependencies under [project.optional-dependencies] keeps production installs clean.

---

## Decision 3: Git Bash as Default Terminal on Windows

**Date:** 2026-03-22
**Status:** Accepted

**Context:** Working on Windows, needed to choose between PowerShell, CMD, or Git Bash for development.

**Decision:** Git Bash as the default VS Code terminal.

**Alternatives considered:**
- PowerShell — commands differ from Linux/Mac, making it harder to follow data engineering documentation and tutorials which assume Bash.
- WSL (Windows Subsystem for Linux) — more powerful but adds setup complexity. Can migrate later if needed.

**Reasoning:** All data engineering tooling (Docker, Terraform, CI/CD, Airflow) uses Bash commands. Using Git Bash ensures consistency between local development and the GitHub Actions CI environment, which runs on Ubuntu.

---



## Decision 4: Remote State in Azure Blob Storage

**Date:** 2026-03-23
**Status:** Accepted

**Context:** Terraform state tracks all managed resources. Storing it locally risks accidental deletion and prevents team collaboration.

**Decision:** Store Terraform state in a dedicated Azure Blob Storage account (`belgiantransporttfstate`) with the `tfstate` container.

**Alternatives considered:**
- Local state file — rejected because it's not backed up, can't be shared, and risks accidental deletion.
- Terraform Cloud — viable but adds another service dependency. Azure Blob Storage keeps everything within the Azure ecosystem.

**Reasoning:** Remote state is the production standard. It provides versioning, locking (prevents concurrent modifications), and durability. Using a separate storage account from the data lake keeps infrastructure concerns isolated from data concerns.


---

## Decision 5: Kafka with KRaft Mode over Zookeeper

**Date:** 2026-03-26
**Status:** Accepted

**Context:** Needed a streaming layer between the API and the data lake to decouple the producer from the consumer and enable message replay.

**Decision:** Apache Kafka running in Docker with KRaft mode (no Zookeeper).

**Alternatives considered:**
- Direct API-to-ADLS writes (what we had before) — rejected because it tightly couples ingestion to storage. If ADLS goes down, data is lost.
- Kafka with Zookeeper — rejected because Zookeeper is a legacy dependency removed in Kafka 3.x+. KRaft is simpler and the modern standard.
- Azure Event Hubs — viable for production but adds Azure cost. Local Kafka in Docker is free for development.
- Simple polling with Airflow — rejected because it doesn't provide message replay or consumer decoupling.

**Reasoning:** Kafka adds three production benefits: decoupling (producer and consumer fail independently), replay (messages kept for 24 hours), and fan-out (multiple consumers can read the same messages). KRaft mode eliminates the Zookeeper dependency, reducing our docker-compose from 2 services to 1. The dead-letter queue pattern handles malformed messages without crashing the pipeline.

---

## Decision 6: Batch Consumer with Configurable Flush

**Date:** 2026-03-26
**Status:** Accepted

**Context:** Needed to decide how the Kafka consumer writes data — one file per message or batched writes.

**Decision:** Batch consumer that flushes when batch_size (100) is reached or batch_timeout (60 seconds) elapses, whichever comes first.

**Alternatives considered:**
- One Parquet file per message — rejected because it creates thousands of tiny files, which degrades data lake query performance (the "small files problem").
- Time-only batching — rejected because it doesn't cap file size. A burst of messages could create excessively large files.

**Reasoning:** The dual trigger (size OR time) balances throughput with latency. During high activity, batches flush at 100 messages for consistent file sizes. During quiet periods, the timeout ensures data isn't stuck in memory indefinitely. This is the standard pattern in production streaming pipelines. 

---

## Decision 7: Airflow with TaskFlow API

**Date:** 2026-04-04
**Status:** Accepted

**Context:** Needed an orchestrator to schedule and automate the full pipeline: ingest → Kafka → Spark → dbt → test.

**Decision:** Apache Airflow using the TaskFlow API (@dag and @task decorators) with a local pipeline runner for Windows development.

**Alternatives considered:**
- Prefect — simpler API but less market adoption in Belgium. Airflow is the most requested orchestrator in Belgian job postings.
- Dagster — strong data asset model but smaller community. Better for greenfield projects.
- Cron jobs — too simple, no retry logic, no dependency management, no monitoring.

**Reasoning:** Airflow is the industry standard for data pipeline orchestration. The TaskFlow API (Airflow 2.x+) simplifies DAG creation with Python decorators instead of manual operator configuration. Since Airflow doesn't support Windows natively, we created a parallel `run_pipeline.py` script that executes the same steps sequentially for local development. The DAG is production-ready for deployment on Linux-based Airflow instances.

---

## Decision 8: DuckDB for Local dbt Development

**Date:** 2026-04-04
**Status:** Accepted

**Context:** Needed a database backend for dbt to build dimensional models locally without Azure costs.

**Decision:** DuckDB as the local dbt backend, with models written to be compatible with Databricks for production.

**Alternatives considered:**
- Databricks Community Edition — free but can't connect to ADLS, limited scheduling. Would require data upload for every run.
- Snowflake — 30-day trial creates time pressure. Not aligned with Belgian market stack.
- PostgreSQL in Docker — viable but adds container complexity for a simple analytical workload.

**Reasoning:** DuckDB runs as a single file with zero setup, reads Parquet natively, and has a SQL dialect compatible with Databricks. The dbt SQL models are identical regardless of backend — switching to Databricks means changing one config file, not rewriting models. This approach enables fast local development while keeping production code ready for Azure Databricks.

---
*New decisions will be added as the project progresses.*