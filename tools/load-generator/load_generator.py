from __future__ import annotations

import argparse
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib import request


def submit_order(base_url: str, index: int) -> dict:
    restaurants = ["Campus Canteen", "Metro Biryani", "Green Bowl", "Pizza Corner"]
    addresses = ["Hostel Gate", "Library Block", "Main Auditorium", "Lab Complex"]
    items = [
        ["Paneer Roll", "Cold Coffee"],
        ["Veg Biryani", "Raita"],
        ["Rice Bowl", "Lassi"],
        ["Margherita Pizza", "Iced Tea"],
    ]
    selection = random.randrange(len(restaurants))
    body = json.dumps(
        {
            "customerName": f"Customer {index}",
            "restaurantName": restaurants[selection],
            "pickupAddress": f"{restaurants[selection]} Pickup Counter",
            "deliveryAddress": random.choice(addresses),
            "items": items[selection],
            "priority": random.randint(1, 10),
            "estimatedDistanceKm": round(random.uniform(0.5, 8.0), 2),
            "simulateSeconds": random.randint(1, 4),
        }
    ).encode("utf-8")
    req = request.Request(
        f"{base_url.rstrip('/')}/orders",
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
    parser = argparse.ArgumentParser(description="Generate delivery order load against the Order API service.")
    parser.add_argument("--url", default="http://localhost:8000", help="Order API base URL")
    parser.add_argument("--jobs", type=int, default=25, help="Number of delivery orders to submit")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrent submitters")
    args = parser.parse_args()

    submitted = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(submit_order, args.url, index) for index in range(args.jobs)]
        for future in as_completed(futures):
            result = future.result()
            submitted.append(result)
            print(json.dumps(result))

    print(json.dumps({"submitted_orders": len(submitted), "api_url": args.url}))


if __name__ == "__main__":
    main()
