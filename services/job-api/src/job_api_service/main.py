from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

from platform_common.logging import configure_json_logging
from platform_common.models import JobStatus, build_job
from platform_common.queueing import JobPublisher, KafkaJobPublisher
from platform_common.repository import JobRepository, RedisJobRepository
from platform_common.settings import PlatformSettings, load_settings


class SubmitJobRequest(BaseModel):
    job_type: str = Field(
        default="sleep",
        description="Type of work. Supported demo values: sleep, cpu, report, flaky.",
    )
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)


class SubmitJobResponse(BaseModel):
    job_id: str
    status: str
    trace_id: str | None


def create_app(
    repo: JobRepository | None = None,
    publisher: JobPublisher | None = None,
    settings: PlatformSettings | None = None,
) -> FastAPI:
    settings = settings or load_settings("job-api")
    logger = configure_json_logging("job-api", settings.log_level)

    app = FastAPI(
        title="Job API Service",
        version="1.0.0",
        description="Accepts distributed jobs and publishes them for async workers.",
    )
    app.state.repo = repo
    app.state.publisher = publisher
    app.state.settings = settings

    @app.on_event("startup")
    def startup() -> None:
        if app.state.repo is None:
            app.state.repo = RedisJobRepository(settings.redis_url)
        if app.state.publisher is None:
            app.state.publisher = KafkaJobPublisher(settings.kafka_bootstrap_servers)
        logger.info("job_api_started", extra={"event": "startup"})

    def get_repo() -> JobRepository:
        return app.state.repo

    def get_publisher() -> JobPublisher:
        return app.state.publisher

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "service": "job-api"}

    @app.get("/readyz")
    def readyz(response: Response, repo: JobRepository = Depends(get_repo)) -> dict[str, str]:
        ping = getattr(repo, "ping", None)
        if callable(ping) and not ping():
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "not-ready"}
        return {"status": "ready"}

    @app.post("/submit-job", response_model=SubmitJobResponse, status_code=status.HTTP_202_ACCEPTED)
    def submit_job(
        request: SubmitJobRequest,
        repo: JobRepository = Depends(get_repo),
        publisher: JobPublisher = Depends(get_publisher),
    ) -> SubmitJobResponse:
        payload = _model_to_dict(request)
        job = build_job(request.job_type, payload)
        repo.save(job)
        try:
            publisher.publish(settings.job_topic, job.to_dict())
        except Exception as exc:
            repo.update(job.job_id, JobStatus.FAILED, error=f"publish failed: {exc}")
            logger.exception(
                "job_publish_failed",
                extra={"event": "job_publish_failed", "job_id": job.job_id, "trace_id": job.trace_id},
            )
            raise HTTPException(status_code=503, detail="queue unavailable") from exc

        logger.info(
            "job_submitted",
            extra={
                "event": "job_submitted",
                "job_id": job.job_id,
                "trace_id": job.trace_id,
                "job_type": job.job_type,
                "priority": request.priority,
            },
        )
        return SubmitJobResponse(job_id=job.job_id, status=job.status.value, trace_id=job.trace_id)

    @app.get("/jobs/{job_id}")
    def get_job(job_id: str, repo: JobRepository = Depends(get_repo)) -> dict[str, Any]:
        job = repo.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return job.to_dict()

    @app.get("/jobs")
    def list_jobs(limit: int = 50, repo: JobRepository = Depends(get_repo)) -> list[dict[str, Any]]:
        return [job.to_dict() for job in repo.list_recent(limit=limit)]

    @app.get("/metrics")
    def metrics(repo: JobRepository = Depends(get_repo)) -> dict[str, int]:
        return repo.metrics().to_dict()

    return app


def _model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


app = create_app()

