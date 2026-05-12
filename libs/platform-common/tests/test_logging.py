from __future__ import annotations

import json
import logging

from platform_common.logging import JsonFormatter, configure_json_logging


def test_json_formatter_includes_context_fields() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="event happened",
        args=(),
        exc_info=None,
    )
    record.service = "job-api"
    record.event = "job_submitted"
    record.job_id = "job-123"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["service"] == "job-api"
    assert payload["event"] == "job_submitted"
    assert payload["job_id"] == "job-123"


def test_configured_logger_merges_service_and_message_extra(capfd) -> None:
    logger = configure_json_logging("worker", "INFO")

    logger.info("job_processing_started", extra={"event": "job_processing_started", "job_id": "job-456"})

    payload = json.loads(capfd.readouterr().out)
    assert payload["service"] == "worker"
    assert payload["event"] == "job_processing_started"
    assert payload["job_id"] == "job-456"
