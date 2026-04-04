"""Run the full pipeline locally without Airflow.

This script executes the same steps as the Airflow DAG
but runs them sequentially in a single process.
Useful for local testing and debugging.
"""

import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    """Execute the full pipeline."""
    logger.info("=== Starting Belgian Transport Pipeline ===")

    # Step 1: Ingest
    logger.info("Step 1/5: Ingesting departures from iRail...")
    from ingestion.irail_client import IRailClient
    from ingestion.kafka_producer import DepartureProducer

    client = IRailClient()
    departures = client.fetch_all_stations()
    logger.info(f"Fetched {len(departures)} departures")

    producer = DepartureProducer()
    result = producer.publish_departures(departures)
    producer.close()
    logger.info(f"Published: {result['published']}, Failed: {result['failed']}")

    # Step 2: Consume
    logger.info("Step 2/5: Consuming from Kafka to Parquet...")
    from ingestion.kafka_consumer import DepartureConsumer
    import threading

    consumer = DepartureConsumer(batch_size=100, batch_timeout_seconds=10)
    thread = threading.Thread(target=lambda: consumer.consume(storage_account=None), daemon=True)
    thread.start()
    time.sleep(15)
    consumer.running = False
    thread.join(timeout=10)
    logger.info("Kafka consumption complete")

    # Step 3: Spark cleaning
    logger.info("Step 3/5: Running PySpark cleaning...")
    from processing.spark_clean import clean_departures, create_spark_session

    spark = create_spark_session()
    try:
        stats = clean_departures(spark, "data/raw/", "data/processed/")
        logger.info(f"Spark cleaning: {stats}")
    finally:
        spark.stop()

    # Step 4: dbt build
    logger.info("Step 4/5: Running dbt models...")
    import subprocess

    dbt_run = subprocess.run(
        ["dbt", "run"],
        cwd="dbt_models/belgian_transport",
        capture_output=True,
        text=True,
    )
    if dbt_run.returncode != 0:
        logger.error(f"dbt run failed: {dbt_run.stderr}")
        raise Exception("dbt run failed")
    logger.info("dbt models built successfully")

    # Step 5: dbt tests
    logger.info("Step 5/5: Running dbt tests...")
    dbt_test = subprocess.run(
        ["dbt", "test"],
        cwd="dbt_models/belgian_transport",
        capture_output=True,
        text=True,
    )
    if dbt_test.returncode != 0:
        logger.error(f"dbt test failed: {dbt_test.stderr}")
        raise Exception("dbt test failed")
    logger.info("All dbt tests passed")

    logger.info("=== Pipeline Complete ===")


if __name__ == "__main__":
    main()
