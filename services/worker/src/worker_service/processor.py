from __future__ import annotations

import random
import time
from collections import Counter
from typing import Any, Callable

from platform_common.models import Job


Sleeper = Callable[[float], None]
RandomFn = Callable[[], float]


def process_job(
    job: Job,
    *,
    sleeper: Sleeper = time.sleep,
    random_fn: RandomFn = random.random,
) -> dict[str, Any]:
    payload = job.payload.get("payload", job.payload)

    if payload.get("force_fail"):
        raise RuntimeError("forced failure requested by payload")

    if job.job_type == "sleep":
        seconds = min(float(payload.get("seconds", 2)), 30.0)
        sleeper(seconds)
        return {"slept_seconds": seconds}

    if job.job_type == "cpu":
        iterations = min(int(payload.get("iterations", 250_000)), 5_000_000)
        checksum = sum((i * i) % 97 for i in range(iterations))
        return {"iterations": iterations, "checksum": checksum}

    if job.job_type == "report":
        text = str(payload.get("text", "distributed job processing platform"))
        words = [word.strip(".,;:!?").lower() for word in text.split() if word.strip()]
        counts = Counter(words)
        sleeper(min(float(payload.get("delay_seconds", 1)), 10.0))
        return {"word_count": len(words), "top_terms": counts.most_common(5)}

    if job.job_type == "flaky":
        failure_rate = min(max(float(payload.get("failure_rate", 0.3)), 0.0), 1.0)
        sleeper(min(float(payload.get("seconds", 1)), 10.0))
        if random_fn() < failure_rate:
            raise RuntimeError(f"flaky job failed with rate {failure_rate}")
        return {"failure_rate": failure_rate, "outcome": "survived"}

    sleeper(min(float(payload.get("seconds", 1)), 10.0))
    return {"echo": payload, "job_type": job.job_type}

