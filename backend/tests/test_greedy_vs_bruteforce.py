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
BRUTEFORCE_URL = BASE_URL + "/api/calculateBruteforce"

DATA_DIR = Path("tests/data")

REPORTS_DIR = Path("tests/reports")

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


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
        "route_segments": data.get(
            "route_segments",
            [],
        ),
        "visited_location_ids": data.get(
            "visited_location_ids",
            [],
        ),
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


def generate_markdown_report(results: list[dict]) -> str:

    lines = []

    lines.append("# Greedy vs Bruteforce Report\n")

    lines.append(
        "| File | Points | Greedy Places | Brute Places | Greedy Duration | Brute Duration | Avg/Place Greedy | Avg/Place Brute | Total Diff Score | Speedup |"
    )

    lines.append(
        "|---|---|---|---|---|---|---|---|---|---|"
    )

    for result in results:

        lines.append(
            f"| "
            f"{result['file']} | "
            f"{result['trip_points']} | "
            f"{result['greedy_places']} | "
            f"{result['brute_places']} | "
            f"{result['greedy_duration']} | "
            f"{result['brute_duration']} | "
            f"{result['greedy_avg']:.2f} min | "
            f"{result['brute_avg']:.2f} min | "
            f"{result['total_diff']:.2f} | "
            f"{result['speedup']:.2f}x |"
        )

    return "\n".join(lines)


def test_saved_requests(
    save_report: bool = False,
):
    print("Testing saved requests...\n")

    request_files = sorted(
        DATA_DIR.glob("test_*.json")
    )

    report_results = []

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

        greedy_route = greedy_result["visited_location_ids"]

        brute_route = bruteforce_result["visited_location_ids"]

        greedy_time = greedy_result["time_seconds"]

        brute_time = bruteforce_result["time_seconds"]

        greedy_trip_duration = greedy_result["total_duration_seconds"]

        brute_trip_duration = bruteforce_result["total_duration_seconds"]

        greedy_places_count = len(greedy_route)

        brute_places_count = len(brute_route)

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


        for segment in greedy_result[
            "route_segments"
        ]:
            print(
                f"  "
                f"{segment['from_location_id']} "
                f"-> "
                f"{segment['to_location_id']} "
                f"({segment['travel_mode']}, "
                f"{format_duration(segment['travel_duration_seconds'])})"
            )
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
        print("Segments:")

        for segment in bruteforce_result[
            "route_segments"
        ]:
            print(
                f"  "
                f"{segment['from_location_id']} "
                f"-> "
                f"{segment['to_location_id']} "
                f"({segment['travel_mode']}, "
                f"{format_duration(segment['travel_duration_seconds'])})"
            )

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

        else:
            speedup = 0

        print()

        # -------------------------------------------------
        # REPORT DATA
        # -------------------------------------------------

        report_results.append({
            "file": file_path.name,
            "trip_points": trip_points_count,
            "greedy_places": greedy_places_count,
            "brute_places": brute_places_count,
            "greedy_duration": format_duration(
                greedy_trip_duration
            ),
            "brute_duration": format_duration(
                brute_trip_duration
            ),
            "greedy_avg": (
                greedy_avg_per_place / 60
            ),
            "brute_avg": (
                brute_avg_per_place / 60
            ),
            "total_diff": total_difference_score,
            "speedup": speedup,
        })

    # -----------------------------------------------------
    # SAVE REPORT
    # -----------------------------------------------------

    if save_report:
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        report_path = (REPORTS_DIR / f"report_{timestamp}.md")

        markdown = generate_markdown_report(report_results)

        with open(report_path, "w", encoding="utf-8") as f:
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

    test_saved_requests(save_report=args.report)