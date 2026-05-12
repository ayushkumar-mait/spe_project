from __future__ import annotations

import json
import time
from typing import Protocol


class JobPublisher(Protocol):
    def publish(self, topic: str, message: dict) -> None:
        ...


class KafkaJobPublisher:
    def __init__(self, bootstrap_servers: str, max_attempts: int = 12, retry_seconds: float = 5.0) -> None:
        from kafka import KafkaProducer
        from kafka.errors import NoBrokersAvailable

        last_error: Exception | None = None
        for _attempt in range(max_attempts):
            try:
                self._producer = KafkaProducer(
                    bootstrap_servers=bootstrap_servers,
                    value_serializer=lambda value: json.dumps(value).encode("utf-8"),
                    key_serializer=lambda value: value.encode("utf-8"),
                    acks="all",
                    retries=5,
                )
                return
            except NoBrokersAvailable as exc:
                last_error = exc
                time.sleep(retry_seconds)
        raise RuntimeError(f"Kafka unavailable at {bootstrap_servers}") from last_error

    def publish(self, topic: str, message: dict) -> None:
        future = self._producer.send(topic, key=message["job_id"], value=message)
        future.get(timeout=10)
        self._producer.flush()


class InMemoryJobPublisher:
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict]] = []

    def publish(self, topic: str, message: dict) -> None:
        self.messages.append((topic, message))
