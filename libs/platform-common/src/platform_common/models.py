from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERED = "recovered"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class Job:
    job_id: str
    job_type: str
    payload: dict[str, Any]
    status: JobStatus = JobStatus.QUEUED
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    result: dict[str, Any] | None = None
    error: str | None = None
    attempts: int = 0
    trace_id: str | None = None
    retry_of: str | None = None
    recovery_job_id: str | None = None
    recovery_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        allowed = {item.name for item in fields(cls)}
        normalized = {key: value for key, value in dict(data).items() if key in allowed}
        normalized["status"] = JobStatus(normalized.get("status", JobStatus.QUEUED))
        return cls(**normalized)


def build_job(
    job_type: str,
    payload: dict[str, Any],
    *,
    job_id: str | None = None,
    trace_id: str | None = None,
) -> Job:
    return Job(
        job_id=job_id or str(uuid4()),
        job_type=job_type,
        payload=payload,
        trace_id=trace_id or str(uuid4()),
    )
