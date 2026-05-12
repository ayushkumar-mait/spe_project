import pytest

from platform_common.models import build_job
from worker_service.processor import process_job


def test_process_cpu_job_returns_deterministic_checksum():
    job = build_job("cpu", {"iterations": 10}, job_id="job-1")

    result = process_job(job)

    assert result["iterations"] == 10
    assert result["checksum"] == sum((i * i) % 97 for i in range(10))


def test_process_report_job_counts_words_without_real_sleep():
    job = build_job("report", {"text": "Kafka worker worker chaos", "delay_seconds": 5})

    result = process_job(job, sleeper=lambda _seconds: None)

    assert result["word_count"] == 4
    assert result["top_terms"][0] == ("worker", 2)


def test_flaky_job_can_be_forced_to_fail():
    job = build_job("flaky", {"failure_rate": 0.9})

    with pytest.raises(RuntimeError):
        process_job(job, sleeper=lambda _seconds: None, random_fn=lambda: 0.1)

