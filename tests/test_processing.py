"""Tests for PySpark processing module."""

from processing.spark_clean import clean_departures, create_spark_session


class TestSparkClean:
    """Tests for the Spark cleaning job."""

    def setup_method(self):
        """Create a Spark session for tests."""
        self.spark = create_spark_session("test-clean")

    def teardown_method(self):
        """Stop Spark session after each test."""
        self.spark.stop()

    def test_clean_removes_duplicates(self, tmp_path):
        """Verify duplicate records are removed."""
        from pyspark.sql import Row

        # Create test data with a duplicate
        data = [
            Row(
                station_id="S1",
                station_name="Brussels",
                destination="Ghent",
                destination_id="D1",
                scheduled_time="2026-03-26T15:00:00+00:00",
                delay_seconds=0,
                canceled=False,
                vehicle_id="V1",
                vehicle_type="IC",
                platform="5",
                occupancy="low",
                ingested_at="2026-03-26T15:01:00+00:00",
            ),
            Row(
                station_id="S1",
                station_name="Brussels",
                destination="Ghent",
                destination_id="D1",
                scheduled_time="2026-03-26T15:00:00+00:00",
                delay_seconds=0,
                canceled=False,
                vehicle_id="V1",
                vehicle_type="IC",
                platform="5",
                occupancy="low",
                ingested_at="2026-03-26T15:02:00+00:00",
            ),
        ]

        df = self.spark.createDataFrame(data)
        input_path = str(tmp_path / "raw")
        output_path = str(tmp_path / "processed")
        df.write.parquet(input_path)

        stats = clean_departures(self.spark, input_path, output_path)

        assert stats["raw_count"] == 2
        assert stats["clean_count"] == 1
        assert stats["duplicates_removed"] == 1

    def test_clean_filters_invalid_records(self, tmp_path):
        """Verify records with missing required fields are removed."""
        from pyspark.sql import Row

        data = [
            Row(
                station_id="S1",
                station_name="Brussels",
                destination="Ghent",
                destination_id="D1",
                scheduled_time="2026-03-26T15:00:00+00:00",
                delay_seconds=0,
                canceled=False,
                vehicle_id="V1",
                vehicle_type="IC",
                platform="5",
                occupancy="low",
                ingested_at="2026-03-26T15:01:00+00:00",
            ),
            Row(
                station_id=None,
                station_name="Unknown",
                destination="Ghent",
                destination_id="D1",
                scheduled_time="2026-03-26T16:00:00+00:00",
                delay_seconds=0,
                canceled=False,
                vehicle_id="V2",
                vehicle_type="IC",
                platform="3",
                occupancy="low",
                ingested_at="2026-03-26T16:01:00+00:00",
            ),
        ]

        df = self.spark.createDataFrame(data)
        input_path = str(tmp_path / "raw")
        output_path = str(tmp_path / "processed")
        df.write.parquet(input_path)

        stats = clean_departures(self.spark, input_path, output_path)

        assert stats["raw_count"] == 2
        assert stats["clean_count"] == 1

    def test_clean_adds_derived_columns(self, tmp_path):
        """Verify derived columns are added to output."""
        from pyspark.sql import Row

        data = [
            Row(
                station_id="S1",
                station_name="Brussels",
                destination="Ghent",
                destination_id="D1",
                scheduled_time="2026-03-26T15:00:00+00:00",
                delay_seconds=120,
                canceled=False,
                vehicle_id="V1",
                vehicle_type="IC",
                platform="5",
                occupancy="low",
                ingested_at="2026-03-26T15:01:00+00:00",
            ),
        ]

        df = self.spark.createDataFrame(data)
        input_path = str(tmp_path / "raw")
        output_path = str(tmp_path / "processed")
        df.write.parquet(input_path)

        clean_departures(self.spark, input_path, output_path)

        result = self.spark.read.parquet(output_path)
        row = result.collect()[0]

        assert row["is_delayed"] is True
        assert row["delay_minutes"] == 2.0
        assert row["departure_hour"] in (15, 16, 17)
