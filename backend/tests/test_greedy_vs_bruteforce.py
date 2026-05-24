import json
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL")

GREEDY_URL = BASE_URL + "/api/calculate"
BRUTEFORCE_URL = BASE_URL + "/api/calculateBruteforce"

DATA_DIR = Path("tests/data")


def load_payload(file_path: Path) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def measure_request(url: str, payload: dict):
    start = time.perf_counter()

    response = requests.post(url, json=payload)

    end = time.perf_counter()

    elapsed = end - start

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"

    return {
        "route_order": data["route_order"],
        "total_duration_seconds": data.get(
            "total_duration_seconds",
            0,
        ),
        "time_seconds": elapsed,
    }


def format_duration(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return f"{hours}h {minutes}min"


def test_saved_requests():
    print("Testing saved requests...\n")

    request_files = sorted(
        DATA_DIR.glob("test_*.json")
    )

    for file_path in request_files:

        payload = load_payload(file_path)

        trip_points_count = len(
            payload["trip_points"]
        )

        print("=" * 80)
        print(f"FILE: {file_path.name}")

        print(
            f"Trip points total: {trip_points_count}"
        )

        # -------------------------------------------------
        # GREEDY
        # -------------------------------------------------

        greedy_result = measure_request(
            GREEDY_URL,
            payload,
        )

        # -------------------------------------------------
        # BRUTEFORCE
        # -------------------------------------------------

        bruteforce_result = measure_request(
            BRUTEFORCE_URL,
            payload,
        )

        # -------------------------------------------------
        # RESULTS
        # -------------------------------------------------

        greedy_route = greedy_result[
            "route_order"
        ]

        brute_route = bruteforce_result[
            "route_order"
        ]

        greedy_time = greedy_result[
            "time_seconds"
        ]

        brute_time = bruteforce_result[
            "time_seconds"
        ]

        greedy_trip_duration = greedy_result[
            "total_duration_seconds"
        ]

        brute_trip_duration = bruteforce_result[
            "total_duration_seconds"
        ]

        greedy_places_count = len(
            greedy_route
        )

        brute_places_count = len(
            brute_route
        )

        greedy_avg_per_place = (
            greedy_trip_duration
            / greedy_places_count
            if greedy_places_count > 0
            else 0
        )

        brute_avg_per_place = (
            brute_trip_duration
            / brute_places_count
            if brute_places_count > 0
            else 0
        )

        same_result = (
            greedy_route == brute_route
        )

        duration_difference_seconds = (
            greedy_trip_duration
            - brute_trip_duration
        )

        duration_difference_minutes = (
            duration_difference_seconds
            / 60
        )

        avg_difference_seconds = (
            greedy_avg_per_place
            - brute_avg_per_place
        )

        avg_difference_minutes = (
            avg_difference_seconds
            / 60
        )

        visited_places_difference = (
            greedy_places_count
            - brute_places_count
        )

        total_difference_score = (
            duration_difference_minutes
            + avg_difference_minutes
            + visited_places_difference
        )

        # -------------------------------------------------
        # GREEDY REPORT
        # -------------------------------------------------

        print("\nGREEDY")

        print(
            f"Request time: {greedy_time:.4f}s"
        )

        print(
            f"Visited places: {greedy_places_count}"
        )

        print(
            "Trip duration:",
            format_duration(
                greedy_trip_duration
            ),
        )

        print(
            "Avg per place:",
            f"{greedy_avg_per_place / 60:.2f} min",
        )

        print(f"Route: {greedy_route}")

        # -------------------------------------------------
        # BRUTEFORCE REPORT
        # -------------------------------------------------

        print("\nBRUTEFORCE")

        print(
            f"Request time: {brute_time:.4f}s"
        )

        print(
            f"Visited places: {brute_places_count}"
        )

        print(
            "Trip duration:",
            format_duration(
                brute_trip_duration
            ),
        )

        print(
            "Avg per place:",
            f"{brute_avg_per_place / 60:.2f} min",
        )

        print(f"Route: {brute_route}")

        # -------------------------------------------------
        # COMPARISON
        # -------------------------------------------------

        print("\nCOMPARISON")

        print(
            f"Same result: {same_result}"
        )

        print(
            "Visited places difference:",
            visited_places_difference,
        )

        print(
            "Trip duration difference:",
            f"{duration_difference_minutes:.2f} min",
        )

        print(
            "Avg/place difference:",
            f"{avg_difference_minutes:.2f} min",
        )

        print(
            "Total difference score:",
            f"{total_difference_score:.2f}",
        )

        if brute_time > 0:

            speedup = (
                brute_time / greedy_time
            )

            print(
                f"Greedy speedup: {speedup:.2f}x"
            )

        print()


if __name__ == "__main__":
    test_saved_requests()