"""iRail API client for fetching Belgian train departure data."""

import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

# Stations we'll monitor — major Belgian hubs
DEFAULT_STATIONS = [
    "Brussels-South",
    "Brussels-North",
    "Brussels-Central",
    "Gent-Sint-Pieters",
    "Antwerpen-Centraal",
]


class IRailClient:
    """Client for the iRail API (https://api.irail.be)."""

    def __init__(self, base_url: str = "https://api.irail.be"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def get_liveboard(self, station: str, lang: str = "en") -> dict | None:
        """Fetch live departures for a given station.

        Args:
            station: Station name (e.g., 'Brussels-South')
            lang: Language for station names ('en', 'nl', 'fr', 'de')

        Returns:
            Parsed JSON response or None if request failed
        """
        try:
            response = self.session.get(
                f"{self.base_url}/liveboard/",
                params={"station": station, "format": "json", "lang": lang},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching liveboard for {station}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {station}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {station}: {e}")
            return None

    def parse_departures(self, liveboard: dict) -> list[dict]:
        """Parse raw liveboard response into clean departure records.

        Args:
            liveboard: Raw JSON response from get_liveboard()

        Returns:
            List of cleaned departure dictionaries
        """
        station_info = liveboard.get("stationinfo", {})
        departures = liveboard.get("departures", {}).get("departure", [])

        parsed = []
        for dep in departures:
            parsed.append(
                {
                    "station_id": station_info.get("id", ""),
                    "station_name": station_info.get("standardname", ""),
                    "destination": dep.get("station", ""),
                    "destination_id": dep.get("stationinfo", {}).get("id", ""),
                    "scheduled_time": datetime.fromtimestamp(
                        int(dep.get("time", 0)), tz=timezone.utc
                    ).isoformat(),
                    "delay_seconds": int(dep.get("delay", 0)),
                    "canceled": dep.get("canceled", "0") == "1",
                    "vehicle_id": dep.get("vehicle", ""),
                    "vehicle_type": dep.get("vehicleinfo", {}).get("type", ""),
                    "platform": dep.get("platform", ""),
                    "occupancy": dep.get("occupancy", {}).get("name", "unknown"),
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                }
            )

        return parsed

    def fetch_all_stations(self, stations: list[str] | None = None) -> list[dict]:
        """Fetch and parse departures for multiple stations.

        Args:
            stations: List of station names. Defaults to DEFAULT_STATIONS.

        Returns:
            Combined list of parsed departures from all stations
        """
        stations = stations or DEFAULT_STATIONS
        all_departures = []

        for station in stations:
            logger.info(f"Fetching departures for {station}...")
            liveboard = self.get_liveboard(station)

            if liveboard is None:
                logger.warning(f"Skipping {station} — no data returned")
                continue

            departures = self.parse_departures(liveboard)
            all_departures.extend(departures)
            logger.info(f"Got {len(departures)} departures from {station}")

        logger.info(f"Total departures fetched: {len(all_departures)}")
        return all_departures