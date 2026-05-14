from platform_common.models import Job, JobStatus, build_job
from platform_common.repository import InMemoryJobRepository


def test_build_job_defaults_to_queued_status():
    job = build_job("sleep", {"seconds": 1}, job_id="job-1", trace_id="trace-1")

    assert job.job_id == "job-1"
    assert job.trace_id == "trace-1"
    assert job.status == JobStatus.QUEUED
    assert job.to_dict()["status"] == "queued"


def test_repository_tracks_metrics_and_recent_jobs():
    repo = InMemoryJobRepository()
    repo.save(build_job("sleep", {"seconds": 1}, job_id="job-1"))
    repo.save(build_job("cpu", {"iterations": 5}, job_id="job-2"))

    repo.update("job-1", JobStatus.RUNNING, increment_attempts=True)
    repo.update("job-2", JobStatus.FAILED, error="boom", increment_attempts=True)

    metrics = repo.metrics()
    assert metrics.running == 1
    assert metrics.failed == 1
    assert metrics.backlog == 1
    assert repo.list_recent(limit=1)[0].job_id == "job-2"


def test_job_from_dict_accepts_retry_metadata_and_ignores_unknown_keys():
    job = Job.from_dict(
        {
            "job_id": "job-3",
            "job_type": "delivery_order",
            "payload": {"order_id": "job-3"},
            "status": "queued",
            "trace_id": "trace-3",
            "retry_of": "job-1",
            "recovery_status": "resubmitted",
        }
    )

    assert job.retry_of == "job-1"
    assert job.status == JobStatus.QUEUED
