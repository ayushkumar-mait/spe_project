from __future__ import annotations

import json
import os
import signal
import time
from typing import Any

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

from platform_common.logging import configure_json_logging
from platform_common.models import Job, JobStatus
from platform_common.repository import JobRepository, RedisJobRepository
from platform_common.settings import load_settings
from worker_service.health import start_health_server
from worker_service.processor import process_job


RUNNING = True


def main() -> None:
    settings = load_settings("worker")
    logger = configure_json_logging("worker", settings.log_level)
    start_health_server(int(os.getenv("HEALTH_PORT", "8080")))
    repo = RedisJobRepository(settings.redis_url)

    consumer = _create_consumer(settings, logger)

    def stop(_signum: int, _frame: Any) -> None:
        global RUNNING
        RUNNING = False
        logger.info("worker_shutdown_requested", extra={"event": "shutdown"})

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    logger.info("worker_started", extra={"event": "startup"})
    for message in consumer:
        if not RUNNING:
            break
        handle_message(message.value, repo, logger)
        consumer.commit()

    consumer.close()
    logger.info("worker_stopped", extra={"event": "shutdown"})


def handle_message(message: dict[str, Any], repo: JobRepository, logger: Any) -> None:
    job = Job.from_dict(message)

    if job.payload.get("payload", {}).get("crash_worker"):
        logger.error(
            "worker_crash_requested",
            extra={"event": "worker_crash_requested", "job_id": job.job_id, "trace_id": job.trace_id},
        )
        os._exit(2)

    if repo.get(job.job_id) is None:
        repo.save(job)

    logger.info(
        "job_processing_started",
        extra={"event": "job_processing_started", "job_id": job.job_id, "trace_id": job.trace_id},
    )
    repo.update(job.job_id, JobStatus.RUNNING, increment_attempts=True)
    try:
        result = process_job(job)
    except Exception as exc:
        repo.update(job.job_id, JobStatus.FAILED, error=str(exc))
        logger.exception(
            "job_processing_failed",
            extra={"event": "job_processing_failed", "job_id": job.job_id, "trace_id": job.trace_id},
        )
        return

    repo.update(job.job_id, JobStatus.COMPLETED, result=result)
    logger.info(
        "job_processing_completed",
        extra={
            "event": "job_processing_completed",
            "job_id": job.job_id,
            "trace_id": job.trace_id,
            "result": result,
        },
    )


def _create_consumer(settings: Any, logger: Any) -> KafkaConsumer:
    last_error: Exception | None = None
    for attempt in range(1, 13):
        try:
            return KafkaConsumer(
                settings.job_topic,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=os.getenv("KAFKA_CONSUMER_GROUP", "job-workers"),
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
            )
        except NoBrokersAvailable as exc:
            last_error = exc
            logger.warning(
                "kafka_unavailable_retrying",
                extra={"event": "kafka_unavailable_retrying", "attempt": attempt},
            )
            time.sleep(5)
    raise RuntimeError(f"Kafka unavailable at {settings.kafka_bootstrap_servers}") from last_error


if __name__ == "__main__":
    main()
