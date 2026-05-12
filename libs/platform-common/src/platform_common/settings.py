from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlatformSettings:
    service_name: str
    kafka_bootstrap_servers: str
    job_topic: str
    redis_url: str
    log_level: str
    vault_env_file: str


def load_settings(service_name: str) -> PlatformSettings:
    load_env_file(os.getenv("VAULT_ENV_FILE", "/vault/secrets/platform.env"))
    return PlatformSettings(
        service_name=service_name,
        kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092"),
        job_topic=os.getenv("JOB_TOPIC", "jobs"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        vault_env_file=os.getenv("VAULT_ENV_FILE", "/vault/secrets/platform.env"),
    )


def load_env_file(path: str) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))

