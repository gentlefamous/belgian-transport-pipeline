"""Main ingestion script — fetch departures and write to storage."""

import logging
import os
import sys

from dotenv import load_dotenv

from ingestion.irail_client import IRailClient
from ingestion.storage import upload_to_adls, write_parquet_local

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the ingestion pipeline."""
    load_dotenv()

    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "belgiantransportdevdl")

    # Step 1: Fetch departures
    client = IRailClient()
    departures = client.fetch_all_stations()

    if not departures:
        logger.error("No departures fetched — exiting")
        sys.exit(1)

    logger.info(f"Fetched {len(departures)} departures from {len(set(d['station_name'] for d in departures))} stations")

    # Step 2: Write to local Parquet
    local_path = write_parquet_local(departures)

    if local_path is None:
        logger.error("Failed to write local Parquet — exiting")
        sys.exit(1)

    # Step 3: Upload to ADLS
    adls_path = upload_to_adls(local_path, storage_account)

    if adls_path:
        logger.info(f"Ingestion complete — data landed at adls://raw/{adls_path}")
    else:
        logger.warning("ADLS upload failed — data saved locally only")


if __name__ == "__main__":
    main()