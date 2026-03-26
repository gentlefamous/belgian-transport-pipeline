"""Kafka consumer — reads departure events and writes Parquet to ADLS."""

import json
import logging
import signal
from datetime import datetime, timezone

from confluent_kafka import Consumer, KafkaError

from ingestion.storage import upload_to_adls, write_parquet_local

logger = logging.getLogger(__name__)


class DepartureConsumer:
    """Consumes departure events from Kafka and writes to storage."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "belgian-transport-departures",
        group_id: str = "departure-writer",
        batch_size: int = 100,
        batch_timeout_seconds: int = 60,
    ):
        self.topic = topic
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds
        self.running = True
        self.batch = []

        self.consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": True,
            }
        )

        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info("Shutdown signal received — flushing remaining batch...")
        self.running = False

    def consume(self, storage_account: str | None = None) -> None:
        """Start consuming messages and writing batches to storage.

        Args:
            storage_account: Azure storage account name for ADLS upload.
                           If None, writes locally only.
        """
        self.consumer.subscribe([self.topic])
        logger.info(f"Subscribed to {self.topic} — waiting for messages...")

        last_flush_time = datetime.now(timezone.utc)

        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    # Check if batch timeout reached
                    elapsed = (datetime.now(timezone.utc) - last_flush_time).total_seconds()
                    if self.batch and elapsed >= self.batch_timeout_seconds:
                        self._flush_batch(storage_account)
                        last_flush_time = datetime.now(timezone.utc)
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug("Reached end of partition")
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                    continue

                # Parse the message
                try:
                    departure = json.loads(msg.value().decode("utf-8"))
                    self.batch.append(departure)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message: {e}")
                    continue

                # Flush if batch is full
                if len(self.batch) >= self.batch_size:
                    self._flush_batch(storage_account)
                    last_flush_time = datetime.now(timezone.utc)

        finally:
            # Flush any remaining messages on shutdown
            if self.batch:
                self._flush_batch(storage_account)
            self.consumer.close()
            logger.info("Consumer shut down cleanly")

    def _flush_batch(self, storage_account: str | None = None) -> None:
        """Write the current batch to Parquet and optionally upload to ADLS."""
        if not self.batch:
            return

        logger.info(f"Flushing batch of {len(self.batch)} messages...")

        local_path = write_parquet_local(self.batch, output_dir="data/raw")

        if local_path and storage_account:
            upload_to_adls(local_path, storage_account)

        self.batch = []
