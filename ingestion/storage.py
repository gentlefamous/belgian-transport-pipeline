"""Write departure data to Azure Data Lake Storage as Parquet files."""

import logging
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

# Schema definition — enforces consistent types across all Parquet files
DEPARTURES_SCHEMA = pa.schema(
    [
        pa.field("station_id", pa.string()),
        pa.field("station_name", pa.string()),
        pa.field("destination", pa.string()),
        pa.field("destination_id", pa.string()),
        pa.field("scheduled_time", pa.string()),
        pa.field("delay_seconds", pa.int32()),
        pa.field("canceled", pa.bool_()),
        pa.field("vehicle_id", pa.string()),
        pa.field("vehicle_type", pa.string()),
        pa.field("platform", pa.string()),
        pa.field("occupancy", pa.string()),
        pa.field("ingested_at", pa.string()),
    ]
)


def write_parquet_local(departures: list[dict], output_dir: str = "data/raw") -> str | None:
    """Write departures to a local Parquet file.

    Args:
        departures: List of parsed departure dictionaries
        output_dir: Local directory to write the file

    Returns:
        Path to the created Parquet file, or None if no data
    """
    if not departures:
        logger.warning("No departures to write")
        return None

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Filename includes timestamp for uniqueness
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = f"{output_dir}/departures_{timestamp}.parquet"

    # Convert list of dicts to PyArrow table with enforced schema
    table = pa.Table.from_pylist(departures, schema=DEPARTURES_SCHEMA)
    pq.write_table(table, filepath)

    logger.info(f"Wrote {len(departures)} records to {filepath}")
    return filepath


def upload_to_adls(
    local_path: str,
    storage_account: str,
    container: str = "raw",
    directory: str = "departures",
) -> str | None:
    """Upload a local file to Azure Data Lake Storage Gen2.

    Args:
        local_path: Path to the local file
        storage_account: Azure storage account name
        container: ADLS container name
        directory: Directory within the container

    Returns:
        ADLS path of the uploaded file, or None on failure
    """
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.filedatalake import DataLakeServiceClient

        credential = DefaultAzureCredential()
        service_client = DataLakeServiceClient(
            account_url=f"https://{storage_account}.dfs.core.windows.net",
            credential=credential,
        )

        file_system_client = service_client.get_file_system_client(container)
        filename = Path(local_path).name
        adls_path = f"{directory}/{filename}"

        file_client = file_system_client.get_file_client(adls_path)

        with open(local_path, "rb") as f:
            file_client.upload_data(f, overwrite=True)

        logger.info(f"Uploaded {local_path} → adls://{container}/{adls_path}")
        return adls_path

    except Exception as e:
        logger.error(f"Failed to upload to ADLS: {e}")
        return None
