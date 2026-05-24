from itertools import permutations
from datetime import datetime, timedelta, time
import os
from typing import List
from models import Graph, TripPoint
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# CONFIG
# =========================================================

OPENING_HOURS_PENALTY_WEIGHT = float(os.getenv("OPENING_HOURS_PENALTY_WEIGHT") or 60.0)
MAX_WAIT_HOURS = float(os.getenv("MAX_WAIT_HOURS") or 2)


# =========================================================
# HELPERS
# =========================================================

def calculate_visit_times(
    point: TripPoint,
    arrival_time: datetime,
    stay_duration: timedelta,
):

    if not point.opening_hours:

        leave_time = arrival_time + stay_duration

        return {
            "is_valid": True,
            "arrival_time": arrival_time,
            "leave_time": leave_time,
            "waiting_time_seconds": 0,
        }

    best_option = None

    for open_dt, close_dt in iter_open_periods(
        point,
        arrival_time,
    ):

        actual_arrival = max(
            arrival_time,
            open_dt,
        )

        leave_time = (
            actual_arrival + stay_duration
        )

        if leave_time > close_dt:
            continue

        waiting_time_seconds = max(0, int((actual_arrival - arrival_time).total_seconds()))

        max_wait_seconds = int(MAX_WAIT_HOURS * 60 * 60)

        if waiting_time_seconds > max_wait_seconds:
            continue

        if (
            best_option is None
            or waiting_time_seconds
            < best_option["waiting_time_seconds"]
        ):

            best_option = {
                "is_valid": True,
                "arrival_time": actual_arrival,
                "leave_time": leave_time,
                "waiting_time_seconds": waiting_time_seconds,
            }

    if best_option:
        return best_option

    return {
        "is_valid": False,
    }


def parse_datetime(datetime_str: str) -> datetime:
    return datetime.fromisoformat(datetime_str)


def minutes_to_timedelta(minutes: int) -> timedelta:
    return timedelta(minutes=minutes)


def seconds_to_timedelta(seconds: int) -> timedelta:
    return timedelta(seconds=seconds)


def get_stay_duration(point: TripPoint) -> timedelta:
    avg_minutes = (
        point.min_duration_minutes
        + point.max_duration_minutes
    ) // 2

    return minutes_to_timedelta(avg_minutes)


def to_google_day(dt: datetime) -> int:
    return (dt.weekday() + 1) % 7


# =========================================================
# OPENING HOURS
# =========================================================

def iter_open_periods(point: TripPoint, reference_date: datetime):

    if not point.opening_hours:
        return

    periods = point.opening_hours.get("periods", [])

    for period in periods:

        open_data = period.get("open")
        close_data = period.get("close")

        if not open_data or not close_data:
            continue

        open_day = open_data["day"]
        close_day = close_data["day"]

        current_day = to_google_day(reference_date)

        day_offset = (open_day - current_day) % 7

        open_dt = datetime.combine(
            reference_date.date(),
            time(
                hour=open_data["hours"],
                minute=open_data["minutes"]
            )
        )

        close_dt = datetime.combine(
            reference_date.date(),
            time(
                hour=close_data["hours"],
                minute=close_data["minutes"]
            )
        )

        open_dt += timedelta(days=day_offset)
        close_dt += timedelta(days=day_offset)

        if close_day != open_day:
            close_dt += timedelta(days=1)

        yield open_dt, close_dt


# =========================================================
# ROUTE COST
# =========================================================

def calculate_route_cost(
    graph: Graph,
    route: list[TripPoint],
    start_time: str,
    trip_end_time: str | None = None,
    trip_points: List[TripPoint] | None = None,
) -> tuple[bool, float, int]:

    index_by_id = {
        point.location_id: idx
        for idx, point in enumerate(trip_points)
    }

    current_time = parse_datetime(start_time)

    trip_end_datetime = (
        parse_datetime(trip_end_time)
        if trip_end_time
        else None
    )

    total_duration_seconds = 0

    for i in range(len(route) - 1):

        current_point = route[i]
        next_point = route[i + 1]

        current_index = index_by_id[
            current_point.location_id
        ]

        next_index = index_by_id[
            next_point.location_id
        ]

        edge = graph.get_edge(
            current_index,
            next_index,
        )

        if edge is None:
            return False, 0, 0

        travel_time = seconds_to_timedelta(
            edge.duration_seconds
        )

        arrival_time = (
            current_time + travel_time
        )

        stay_duration = get_stay_duration(
            next_point
        )

        visit_info = calculate_visit_times(
            next_point,
            arrival_time,
            stay_duration,
        )

        if not visit_info["is_valid"]:
            return False, 0, 0

        arrival_time = visit_info["arrival_time"]

        leave_time = visit_info["leave_time"]

        waiting_time_seconds = visit_info[
            "waiting_time_seconds"
        ]

        # ---------------------------------------------
        # HARD CONSTRAINTS
        # ---------------------------------------------

        if (
            trip_end_datetime
            and leave_time > trip_end_datetime
        ):
            return False, 0, 0

        # ---------------------------------------------
        # UPDATE STATE
        # ---------------------------------------------

        current_time = leave_time

        total_duration_seconds += edge.duration_seconds

        total_duration_seconds += waiting_time_seconds

        total_duration_seconds += int(stay_duration.total_seconds())

    total_cost = total_duration_seconds

    return (
        True,
        total_cost,
        total_duration_seconds,
    )


# =========================================================
# BRUTE FORCE SEARCH
# =========================================================

def calculate_route_order(
    graph: Graph,
    trip_points: List[TripPoint],
    start_location_id: str,
    trip_start_time: str,
    trip_end_time: str | None = None,
):

    points_by_id = {
        point.location_id: point
        for point in trip_points
    }

    start_point = points_by_id[
        start_location_id
    ]

    remaining_points = [
        point
        for point in trip_points
        if point.location_id != start_location_id
    ]

    best_route = None

    best_cost = float("inf")

    best_duration_seconds = 0

    # =====================================================
    # PARTIAL + FULL ROUTES
    # =====================================================

    for r in range(
        1,
        len(remaining_points) + 1
    ):

        for permutation in permutations(
            remaining_points,
            r,
        ):

            candidate_route = [
                start_point,
                *permutation,
            ]

            (
                is_valid,
                total_cost,
                total_duration_seconds,
            ) = calculate_route_cost(
                graph=graph,
                route=candidate_route,
                start_time=trip_start_time,
                trip_end_time=trip_end_time,
                trip_points=trip_points,
            )

            if not is_valid:
                continue

            # Prefer longer valid routes
            if (
                best_route is None
                or len(candidate_route) > len(best_route)
            ):
                best_route = candidate_route

                best_cost = total_cost

                best_duration_seconds = (
                    total_duration_seconds
                )

                continue

            # Same length -> optimize cost
            if (
                len(candidate_route)
                == len(best_route)
                and total_cost < best_cost
            ):

                best_route = candidate_route

                best_cost = total_cost

                best_duration_seconds = (
                    total_duration_seconds
                )

    # =====================================================
    # NO VALID ROUTE
    # =====================================================

    if best_route is None:
        return {
            "route_order": [],
            "total_duration_seconds": 0,
        }

    # =====================================================
    # RESULT
    # =====================================================

    return {
        "route_order": [
            point.location_id
            for point in best_route
        ],
        "total_duration_seconds": (
            best_duration_seconds
        ),
    }