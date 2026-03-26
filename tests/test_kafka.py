"""Tests for Kafka producer and consumer components."""

from unittest.mock import MagicMock, patch

from ingestion.kafka_producer import DepartureProducer

SAMPLE_DEPARTURE = {
    "station_id": "BE.NMBS.008814001",
    "station_name": "Brussel-Zuid/Bruxelles-Midi",
    "destination": "Gent-Sint-Pieters",
    "destination_id": "BE.NMBS.008892007",
    "scheduled_time": "2026-03-26T15:00:00+00:00",
    "delay_seconds": 120,
    "canceled": False,
    "vehicle_id": "BE.NMBS.IC1234",
    "vehicle_type": "IC",
    "platform": "5",
    "occupancy": "low",
    "ingested_at": "2026-03-26T15:00:00+00:00",
}


class TestDepartureProducer:
    """Tests for DepartureProducer."""

    @patch("ingestion.kafka_producer.Producer")
    def test_publish_departures_returns_correct_count(self, mock_producer_class):
        """Verify published count matches input."""
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        producer = DepartureProducer()
        result = producer.publish_departures([SAMPLE_DEPARTURE, SAMPLE_DEPARTURE])

        assert result["published"] == 2
        assert result["failed"] == 0

    @patch("ingestion.kafka_producer.Producer")
    def test_publish_sends_to_dlq_on_missing_fields(self, mock_producer_class):
        """Verify messages with missing required fields go to DLQ."""
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        bad_departure = {"destination": "Gent", "delay_seconds": 0}

        producer = DepartureProducer()
        result = producer.publish_departures([bad_departure])

        assert result["published"] == 0
        assert result["failed"] == 1

    @patch("ingestion.kafka_producer.Producer")
    def test_publish_uses_station_id_as_key(self, mock_producer_class):
        """Verify station_id is used as the Kafka message key."""
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        producer = DepartureProducer()
        producer.publish_departures([SAMPLE_DEPARTURE])

        call_kwargs = mock_producer.produce.call_args
        assert call_kwargs[1]["key"] == "BE.NMBS.008814001"

    @patch("ingestion.kafka_producer.Producer")
    def test_publish_empty_list_returns_zeros(self, mock_producer_class):
        """Verify empty input produces nothing."""
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        producer = DepartureProducer()
        result = producer.publish_departures([])

        assert result["published"] == 0
        assert result["failed"] == 0
