from __future__ import annotations

import argparse
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib import request


def submit_job(base_url: str, index: int) -> dict:
    job_type = random.choice(["sleep", "cpu", "report", "flaky"])
    payload = {
        "sleep": {"seconds": random.uniform(0.2, 2.0)},
        "cpu": {"iterations": random.randint(50_000, 300_000)},
        "report": {"text": f"job {index} chaos platform worker worker", "delay_seconds": 0.3},
        "flaky": {"failure_rate": 0.15, "seconds": 0.2},
    }[job_type]
    body = json.dumps({"job_type": job_type, "payload": payload, "priority": random.randint(1, 10)}).encode("utf-8")
    req = request.Request(
        f"{base_url.rstrip('/')}/submit-job",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.time()
    with request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))
    result["client_latency_ms"] = round((time.time() - started) * 1000, 2)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate load against the Job API service.")
    parser.add_argument("--url", default="http://localhost:8000", help="Job API base URL")
    parser.add_argument("--jobs", type=int, default=25, help="Number of jobs to submit")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrent submitters")
    args = parser.parse_args()

    submitted = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(submit_job, args.url, index) for index in range(args.jobs)]
        for future in as_completed(futures):
            result = future.result()
            submitted.append(result)
            print(json.dumps(result))

    print(json.dumps({"submitted": len(submitted), "api_url": args.url}))


if __name__ == "__main__":
    main()

