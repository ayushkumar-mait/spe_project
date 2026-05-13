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

    if job.job_type == "delivery_order":
        seconds = min(float(payload.get("simulate_seconds", 2)), 30.0)
        distance_km = max(float(payload.get("estimated_distance_km", 3.0)), 0.1)
        items = payload.get("items", [])
        sleeper(seconds)
        return {
            "order_id": payload.get("order_id", job.job_id),
            "order_status": "ready_for_dispatch",
            "assigned_rider": _select_rider(job.job_id),
            "estimated_delivery_minutes": int(12 + distance_km * 4),
            "items_count": len(items) if isinstance(items, list) else 0,
            "processed_steps": [
                "payment_verified",
                "restaurant_confirmed",
                "rider_assigned",
                "route_calculated",
                "customer_notified",
            ],
        }

    if job.job_type == "flaky":
        failure_rate = min(max(float(payload.get("failure_rate", 0.3)), 0.0), 1.0)
        sleeper(min(float(payload.get("seconds", 1)), 10.0))
        if random_fn() < failure_rate:
            raise RuntimeError(f"flaky job failed with rate {failure_rate}")
        return {"failure_rate": failure_rate, "outcome": "survived"}

    sleeper(min(float(payload.get("seconds", 1)), 10.0))
    return {"echo": payload, "job_type": job.job_type}


def _select_rider(job_id: str) -> str:
    riders = ["Rider-Asha", "Rider-Rahul", "Rider-Neha", "Rider-Arjun"]
    return riders[sum(ord(char) for char in job_id) % len(riders)]
