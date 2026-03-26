"""Kafka producer — publishes iRail departure events to Kafka topics."""

import json
import logging

from confluent_kafka import Producer

logger = logging.getLogger(__name__)


class DepartureProducer:
    """Publishes departure events to Kafka."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "belgian-transport-departures",
        dlq_topic: str = "belgian-transport-dlq",
    ):
        self.topic = topic
        self.dlq_topic = dlq_topic
        self.producer = Producer({"bootstrap.servers": bootstrap_servers})

    def _delivery_callback(self, err, msg):
        """Called once for each message produced to indicate delivery result."""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def publish_departures(self, departures: list[dict]) -> dict:
        """Publish departure events to Kafka.

        Args:
            departures: List of parsed departure dictionaries

        Returns:
            Dict with counts: {"published": n, "failed": n}
        """
        published = 0
        failed = 0

        for departure in departures:
            try:
                # Validate required fields before publishing
                if not departure.get("station_id") or not departure.get("vehicle_id"):
                    self._send_to_dlq(departure, "Missing required fields")
                    failed += 1
                    continue

                # Use station_id as the message key for partitioning
                key = departure["station_id"]
                value = json.dumps(departure)

                self.producer.produce(
                    topic=self.topic,
                    key=key,
                    value=value,
                    callback=self._delivery_callback,
                )
                published += 1

            except Exception as e:
                logger.error(f"Failed to produce message: {e}")
                self._send_to_dlq(departure, str(e))
                failed += 1

        # Wait for all messages to be delivered
        self.producer.flush()

        logger.info(f"Published {published} messages, {failed} to DLQ")
        return {"published": published, "failed": failed}

    def _send_to_dlq(self, departure: dict, reason: str) -> None:
        """Send a failed message to the dead-letter queue.

        Args:
            departure: The departure record that failed
            reason: Why it failed
        """
        try:
            dlq_message = {
                "original_message": departure,
                "failure_reason": reason,
            }
            self.producer.produce(
                topic=self.dlq_topic,
                value=json.dumps(dlq_message),
            )
            logger.warning(f"Sent message to DLQ: {reason}")
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")

    def close(self):
        """Flush remaining messages and clean up."""
        self.producer.flush()
