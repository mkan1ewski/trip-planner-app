import json
import time
import argparse
from pathlib import Path

import requests
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL")

GREEDY_URL = BASE_URL + "/api/calculate"

DATA_DIR = Path("tests/data")
REPORTS_DIR = Path("tests/reports")

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_payload(file_path: Path) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def measure_request(url: str, payload: dict):
    start = time.perf_counter()

    response = requests.post(url, json=payload)

    elapsed = time.perf_counter() - start

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"

    return {
        "visited_location_ids": data.get("visited_location_ids", []),
        "total_duration_seconds": data.get("total_duration_seconds", 0),
        "time_seconds": elapsed,
    }


def format_duration(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return f"{hours}h {minutes}min"


def generate_markdown_report(results: list[dict]) -> str:
    lines = [
        "# Greedy Efficiency Report\n",
        "| File | Points | Visited Places | Trip Duration | Avg/Place | Request Time |",
        "|---|---|---|---|---|---|",
    ]

    for result in results:
        lines.append(
            f"| "
            f"{result['file']} | "
            f"{result['trip_points']} | "
            f"{result['visited_places']} | "
            f"{result['trip_duration']} | "
            f"{result['avg_per_place']:.2f} min | "
            f"{result['request_time']:.4f}s |"
        )

    return "\n".join(lines)


def test_saved_requests(save_report: bool = False):
    print("Testing greedy efficiency...\n")

    request_files = sorted(
        DATA_DIR.glob("efficiency_test*.json")
    )

    report_results = []

    for file_path in request_files:

        payload = load_payload(file_path)

        trip_points_count = len(payload["trip_points"])

        print("=" * 80)
        print(f"FILE: {file_path.name}")
        print(f"Trip points total: {trip_points_count}")

        greedy_result = measure_request(
            GREEDY_URL,
            payload,
        )

        greedy_route = greedy_result["visited_location_ids"]

        greedy_time = greedy_result["time_seconds"]

        greedy_trip_duration = greedy_result[
            "total_duration_seconds"
        ]

        greedy_places_count = len(greedy_route)

        greedy_avg_per_place = (
            greedy_trip_duration / greedy_places_count
            if greedy_places_count > 0
            else 0
        )

        print("\nGREEDY")

        print(f"Request time: {greedy_time:.4f}s")

        print(
            f"Visited places: {greedy_places_count}"
        )

        print(
            "Trip duration:",
            format_duration(greedy_trip_duration),
        )

        print(
            "Avg per place:",
            f"{greedy_avg_per_place / 60:.2f} min",
        )

        print(f"Route: {greedy_route}")
        print()

        report_results.append({
            "file": file_path.name,
            "trip_points": trip_points_count,
            "visited_places": greedy_places_count,
            "trip_duration": format_duration(
                greedy_trip_duration
            ),
            "avg_per_place": (
                greedy_avg_per_place / 60
            ),
            "request_time": greedy_time,
        })

    if save_report:

        timestamp = time.strftime(
            "%Y%m%d_%H%M%S"
        )

        report_path = (
            REPORTS_DIR
            / f"efficiency_report_{timestamp}.md"
        )

        markdown = generate_markdown_report(
            report_results
        )

        with open(
            report_path,
            "w",
            encoding="utf-8",
        ) as f:
            f.write(markdown)

        print(
            f"\nReport saved to: {report_path}"
        )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--report",
        action="store_true",
        help="Save markdown report",
    )

    args = parser.parse_args()

    test_saved_requests(
        save_report=args.report
    )