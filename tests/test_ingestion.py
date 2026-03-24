"""Tests for the iRail ingestion module."""

from unittest.mock import MagicMock, patch

from ingestion.irail_client import IRailClient


# Sample API response for testing
MOCK_LIVEBOARD = {
    "stationinfo": {
        "id": "BE.NMBS.008814001",
        "standardname": "Brussel-Zuid/Bruxelles-Midi",
    },
    "departures": {
        "departure": [
            {
                "station": "Gent-Sint-Pieters",
                "stationinfo": {"id": "BE.NMBS.008892007"},
                "time": "1774364580",
                "delay": "120",
                "canceled": "0",
                "vehicle": "BE.NMBS.IC1234",
                "vehicleinfo": {"type": "IC"},
                "platform": "5",
                "occupancy": {"name": "low"},
            },
            {
                "station": "Antwerpen-Centraal",
                "stationinfo": {"id": "BE.NMBS.008821006"},
                "time": "1774364700",
                "delay": "0",
                "canceled": "1",
                "vehicle": "BE.NMBS.S32101",
                "vehicleinfo": {"type": "S"},
                "platform": "3",
                "occupancy": {"name": "high"},
            },
        ]
    },
}


class TestIRailClient:
    """Tests for IRailClient."""

    def test_parse_departures_returns_correct_count(self):
        """Verify we get the right number of parsed departures."""
        client = IRailClient()
        result = client.parse_departures(MOCK_LIVEBOARD)
        assert len(result) == 2

    def test_parse_departures_extracts_station_name(self):
        """Verify station name is extracted correctly."""
        client = IRailClient()
        result = client.parse_departures(MOCK_LIVEBOARD)
        assert result[0]["station_name"] == "Brussel-Zuid/Bruxelles-Midi"

    def test_parse_departures_converts_delay_to_int(self):
        """Verify delay is converted from string to integer."""
        client = IRailClient()
        result = client.parse_departures(MOCK_LIVEBOARD)
        assert result[0]["delay_seconds"] == 120
        assert isinstance(result[0]["delay_seconds"], int)

    def test_parse_departures_converts_canceled_to_bool(self):
        """Verify canceled field is converted to boolean."""
        client = IRailClient()
        result = client.parse_departures(MOCK_LIVEBOARD)
        assert result[0]["canceled"] is False
        assert result[1]["canceled"] is True

    def test_parse_departures_includes_ingested_at(self):
        """Verify ingestion timestamp is added."""
        client = IRailClient()
        result = client.parse_departures(MOCK_LIVEBOARD)
        assert "ingested_at" in result[0]

    @patch.object(IRailClient, "get_liveboard", return_value=None)
    def test_fetch_all_stations_handles_failed_request(self, mock_get):
        """Verify pipeline continues when a station request fails."""
        client = IRailClient()
        result = client.fetch_all_stations(["Brussels-South"])
        assert result == []

    @patch.object(IRailClient, "get_liveboard", return_value=MOCK_LIVEBOARD)
    def test_fetch_all_stations_returns_departures(self, mock_get):
        """Verify departures are returned for successful requests."""
        client = IRailClient()
        result = client.fetch_all_stations(["Brussels-South"])
        assert len(result) == 2