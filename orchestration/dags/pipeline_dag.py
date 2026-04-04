"""Main pipeline DAG — orchestrates the full Belgian transport data pipeline.

Flow: Ingest → Process → Transform → Test
Schedule: Every 6 hours
"""

from datetime import datetime, timedelta

from airflow.sdk import dag, task


default_args = {
    "owner": "lukmon",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=30),
}


@dag(
    dag_id="belgian_transport_pipeline",
    default_args=default_args,
    description="End-to-end Belgian public transport data pipeline",
    schedule="0 */6 * * *",  # Every 6 hours
    start_date=datetime(2026, 3, 1),
    catchup=False,
    tags=["belgian-transport", "production"],
)
def belgian_transport_pipeline():
    """Belgian Public Transport Pipeline.

    Fetches live departure data from iRail API,
    streams through Kafka, cleans with PySpark,
    transforms with dbt, and validates with dbt tests.
    """

    @task()
    def ingest_departures() -> dict:
        """Fetch departures from iRail and publish to Kafka."""
        from ingestion.irail_client import IRailClient
        from ingestion.kafka_producer import DepartureProducer

        client = IRailClient()
        departures = client.fetch_all_stations()

        if not departures:
            raise ValueError("No departures fetched — pipeline cannot continue")

        producer = DepartureProducer()
        result = producer.publish_departures(departures)
        producer.close()

        return {
            "departures_fetched": len(departures),
            "published": result["published"],
            "failed": result["failed"],
        }

    @task()
    def consume_to_parquet(ingest_result: dict) -> str:
        """Consume Kafka messages and write to local Parquet."""
        import time

        from ingestion.kafka_consumer import DepartureConsumer

        consumer = DepartureConsumer(
            batch_size=100,
            batch_timeout_seconds=15,
        )

        # Run consumer for a short window to drain the topic
        import threading

        def run_consumer():
            consumer.consume(storage_account=None)

        thread = threading.Thread(target=run_consumer, daemon=True)
        thread.start()

        # Wait enough time for messages to be consumed
        time.sleep(20)
        consumer.running = False
        thread.join(timeout=10)

        return f"Consumed {ingest_result['published']} messages to Parquet"

    @task()
    def run_spark_cleaning(consume_result: str) -> dict:
        """Run PySpark job to clean and deduplicate raw data."""
        from processing.spark_clean import clean_departures, create_spark_session

        spark = create_spark_session()
        try:
            stats = clean_departures(
                spark=spark,
                input_path="data/raw/",
                output_path="data/processed/",
            )
            return stats
        finally:
            spark.stop()

    @task()
    def run_dbt_build(spark_result: dict) -> str:
        """Run dbt models to build dimensional tables."""
        import subprocess

        result = subprocess.run(
            ["dbt", "run"],
            cwd="dbt_models/belgian_transport",
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise Exception(f"dbt run failed: {result.stderr}")

        return f"dbt build complete — processed {spark_result['clean_count']} records"

    @task()
    def run_dbt_tests(dbt_result: str) -> str:
        """Run dbt tests to validate data quality."""
        import subprocess

        result = subprocess.run(
            ["dbt", "test"],
            cwd="dbt_models/belgian_transport",
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise Exception(f"dbt test failed: {result.stderr}")

        return "All dbt tests passed"

    @task()
    def pipeline_complete(test_result: str) -> str:
        """Final task — log pipeline completion."""
        from datetime import datetime, timezone

        completion_time = datetime.now(timezone.utc).isoformat()
        message = f"Pipeline completed successfully at {completion_time}. {test_result}"
        print(message)
        return message

    # Define the task dependencies (the DAG flow)
    ingest_result = ingest_departures()
    consume_result = consume_to_parquet(ingest_result)
    spark_result = run_spark_cleaning(consume_result)
    dbt_result = run_dbt_build(spark_result)
    test_result = run_dbt_tests(dbt_result)
    pipeline_complete(test_result)


# Instantiate the DAG
belgian_transport_pipeline()
