from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Protocol

from platform_common.models import Job, JobStatus


class JobRepository(Protocol):
    def save(self, job: Job) -> None:
        ...

    def get(self, job_id: str) -> Job | None:
        ...

    def update(
        self,
        job_id: str,
        status: JobStatus,
        *,
        result: dict | None = None,
        error: str | None = None,
        increment_attempts: bool = False,
    ) -> Job:
        ...

    def list_recent(self, limit: int = 100) -> list[Job]:
        ...

    def metrics(self) -> "JobMetrics":
        ...

    def mark_recovered(self, job_id: str, recovery_job_id: str) -> Job | None:
        ...


@dataclass(frozen=True)
class JobMetrics:
    queued: int
    running: int
    completed: int
    failed: int
    recovered: int
    cancelled: int
    total: int

    @property
    def backlog(self) -> int:
        return self.queued + self.running

    def to_dict(self) -> dict[str, int]:
        return {
            "queued": self.queued,
            "running": self.running,
            "completed": self.completed,
            "failed": self.failed,
            "recovered": self.recovered,
            "cancelled": self.cancelled,
            "total": self.total,
            "backlog": self.backlog,
        }


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._order: list[str] = []

    def save(self, job: Job) -> None:
        self._jobs[job.job_id] = job
        self._order.append(job.job_id)

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def update(
        self,
        job_id: str,
        status: JobStatus,
        *,
        result: dict | None = None,
        error: str | None = None,
        increment_attempts: bool = False,
    ) -> Job:
        job = self._jobs[job_id]
        job.status = status
        job.updated_at = _utc_now()
        job.result = result
        job.error = error
        if increment_attempts:
            job.attempts += 1
        return job

    def list_recent(self, limit: int = 100) -> list[Job]:
        ids = list(reversed(self._order[-limit:]))
        return [self._jobs[job_id] for job_id in ids]

    def metrics(self) -> JobMetrics:
        return _metrics_from_jobs(self._jobs.values())

    def mark_recovered(self, job_id: str, recovery_job_id: str) -> Job | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        job.status = JobStatus.RECOVERED
        job.recovery_job_id = recovery_job_id
        job.recovery_status = "completed"
        job.updated_at = _utc_now()
        return job


class RedisJobRepository:
    def __init__(self, redis_url: str, namespace: str = "jobs") -> None:
        import redis

        self._client = redis.Redis.from_url(redis_url, decode_responses=True)
        self._namespace = namespace

    def save(self, job: Job) -> None:
        pipe = self._client.pipeline()
        pipe.set(self._job_key(job.job_id), json.dumps(job.to_dict()))
        pipe.lpush(self._list_key(), job.job_id)
        pipe.ltrim(self._list_key(), 0, 499)
        pipe.execute()

    def get(self, job_id: str) -> Job | None:
        raw = self._client.get(self._job_key(job_id))
        if not raw:
            return None
        return Job.from_dict(json.loads(raw))

    def update(
        self,
        job_id: str,
        status: JobStatus,
        *,
        result: dict | None = None,
        error: str | None = None,
        increment_attempts: bool = False,
    ) -> Job:
        job = self.get(job_id)
        if job is None:
            raise KeyError(f"job not found: {job_id}")
        job.status = status
        job.updated_at = _utc_now()
        job.result = result
        job.error = error
        if increment_attempts:
            job.attempts += 1
        self._client.set(self._job_key(job_id), json.dumps(job.to_dict()))
        return job

    def list_recent(self, limit: int = 100) -> list[Job]:
        job_ids = self._client.lrange(self._list_key(), 0, limit - 1)
        jobs = [self.get(job_id) for job_id in job_ids]
        return [job for job in jobs if job is not None]

    def metrics(self) -> JobMetrics:
        return _metrics_from_jobs(self.list_recent(limit=500))

    def mark_recovered(self, job_id: str, recovery_job_id: str) -> Job | None:
        job = self.get(job_id)
        if job is None:
            return None
        job.status = JobStatus.RECOVERED
        job.recovery_job_id = recovery_job_id
        job.recovery_status = "completed"
        job.updated_at = _utc_now()
        self._client.set(self._job_key(job_id), json.dumps(job.to_dict()))
        return job

    def ping(self) -> bool:
        return bool(self._client.ping())

    def _job_key(self, job_id: str) -> str:
        return f"{self._namespace}:{job_id}"

    def _list_key(self) -> str:
        return f"{self._namespace}:recent"


def _metrics_from_jobs(jobs: Iterable[Job]) -> JobMetrics:
    counter = Counter(job.status for job in jobs)
    return JobMetrics(
        queued=counter[JobStatus.QUEUED],
        running=counter[JobStatus.RUNNING],
        completed=counter[JobStatus.COMPLETED],
        failed=counter[JobStatus.FAILED],
        recovered=counter[JobStatus.RECOVERED],
        cancelled=counter[JobStatus.CANCELLED],
        total=sum(counter.values()),
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
