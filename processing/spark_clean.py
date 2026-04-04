"""PySpark job to clean and deduplicate raw departure data."""

import logging
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import BooleanType, LongType, StringType, StructField, StructType

logger = logging.getLogger(__name__)


# Expected schema for raw departure data
RAW_SCHEMA = StructType(
    [
        StructField("station_id", StringType(), False),
        StructField("station_name", StringType(), False),
        StructField("destination", StringType(), True),
        StructField("destination_id", StringType(), True),
        StructField("scheduled_time", StringType(), False),
        StructField("delay_seconds", LongType(), True),
        StructField("canceled", BooleanType(), True),
        StructField("vehicle_id", StringType(), False),
        StructField("vehicle_type", StringType(), True),
        StructField("platform", StringType(), True),
        StructField("occupancy", StringType(), True),
        StructField("ingested_at", StringType(), True),
    ]
)


def create_spark_session(app_name: str = "belgian-transport-clean") -> SparkSession:
    """Create a local Spark session.

    In production, this would connect to Azure Databricks.
    Locally, it runs Spark in single-node mode.
    """
    import os
    import sys

    os.environ["HADOOP_HOME"] = os.path.expanduser("~/hadoop")
    os.environ["PATH"] = os.environ["PATH"] + os.pathsep + os.path.join(os.environ["HADOOP_HOME"], "bin")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )


def clean_departures(spark: SparkSession, input_path: str, output_path: str) -> dict:
    """Read raw Parquet files, clean, deduplicate, and write processed output.

    Args:
        spark: Active SparkSession
        input_path: Path to raw Parquet files (e.g., 'data/raw/')
        output_path: Path for cleaned output (e.g., 'data/processed/')

    Returns:
        Dict with processing stats
    """
    # Read all raw Parquet files
    logger.info(f"Reading raw data from {input_path}...")
    raw_df = spark.read.schema(RAW_SCHEMA).parquet(input_path)

    raw_count = raw_df.count()
    logger.info(f"Raw records: {raw_count}")

    # Step 1: Convert scheduled_time from ISO string to timestamp
    cleaned_df = raw_df.withColumn("scheduled_time", F.to_timestamp("scheduled_time"))

    # Step 2: Convert ingested_at from ISO string to timestamp
    cleaned_df = cleaned_df.withColumn("ingested_at", F.to_timestamp("ingested_at"))

    # Step 3: Handle nulls — fill defaults for nullable fields
    cleaned_df = cleaned_df.fillna(
        {
            "delay_seconds": 0,
            "canceled": False,
            "platform": "unknown",
            "occupancy": "unknown",
            "vehicle_type": "unknown",
        }
    )

    # Step 4: Filter out invalid records (missing required fields)
    cleaned_df = cleaned_df.filter(
        F.col("station_id").isNotNull() & F.col("vehicle_id").isNotNull() & F.col("scheduled_time").isNotNull()
    )

    # Step 5: Deduplicate — same train at same station at same time = duplicate
    cleaned_df = cleaned_df.dropDuplicates(["station_id", "vehicle_id", "scheduled_time"])

    # Step 6: Add processing metadata
    cleaned_df = cleaned_df.withColumn("processed_at", F.current_timestamp())

    # Step 7: Add derived columns useful for analytics
    cleaned_df = (
        cleaned_df.withColumn("is_delayed", F.col("delay_seconds") > 0)
        .withColumn("delay_minutes", F.round(F.col("delay_seconds") / 60, 1))
        .withColumn("departure_hour", F.hour("scheduled_time"))
        .withColumn("departure_date", F.to_date("scheduled_time"))
        .withColumn("day_of_week", F.dayofweek("scheduled_time"))
    )

    clean_count = cleaned_df.count()
    dupes_removed = raw_count - clean_count
    logger.info(f"Clean records: {clean_count} (removed {dupes_removed} duplicates/invalids)")

    # Write processed data as Parquet, partitioned by date
    Path(output_path).mkdir(parents=True, exist_ok=True)
    cleaned_df.coalesce(1).write.mode("overwrite").partitionBy("departure_date").parquet(output_path)

    logger.info(f"Wrote processed data to {output_path}")

    return {
        "raw_count": raw_count,
        "clean_count": clean_count,
        "duplicates_removed": dupes_removed,
    }


def main() -> None:
    """Run the Spark cleaning job."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    spark = create_spark_session()

    try:
        stats = clean_departures(
            spark=spark,
            input_path="data/raw/",
            output_path="data/processed/",
        )
        logger.info(f"Processing complete: {stats}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
