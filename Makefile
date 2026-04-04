.PHONY: help ingest process dbt-run dbt-test pipeline test lint format clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

ingest: ## Fetch departures from iRail and write to ADLS
	uv run python -m ingestion.main

process: ## Run PySpark cleaning on raw data
	uv run python -m processing.spark_clean

dbt-run: ## Build dbt models
	cd dbt_models/belgian_transport && dbt run

dbt-test: ## Run dbt tests
	cd dbt_models/belgian_transport && dbt test

pipeline: ## Run the full end-to-end pipeline
	uv run python -m orchestration.run_pipeline

dashboard: ## Launch the Streamlit dashboard
	uv run streamlit run dashboard/app.py

test: ## Run all Python unit tests
	uv run pytest tests/ -v

lint: ## Run flake8 linting
	uv run flake8 ingestion/ processing/ orchestration/ tests/ dashboard/ --max-line-length 120

format: ## Auto-format code with black
	uv run black ingestion/ processing/ orchestration/ tests/ dashboard/ --line-length 120

clean: ## Stop Kafka and destroy Azure resources
	docker compose down
	cd terraform && terraform destroy