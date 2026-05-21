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

OPENING_HOURS_PENALTY_WEIGHT = float(
    os.getenv("OPENING_HOURS_PENALTY_WEIGHT") or 60.0
)


# =========================================================
# HELPERS
# =========================================================

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

def iter_open_periods(point: TripPoint,reference_date: datetime):

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

        day_offset = open_day - current_day

        open_dt = datetime.combine(
            reference_date.date(),
            time(hour=open_data["hours"], minute=open_data["minutes"])
        )

        close_dt = datetime.combine(
            reference_date.date(),
            time(hour=close_data["hours"], minute=close_data["minutes"])
        )

        open_dt += timedelta(days=day_offset)
        close_dt += timedelta(days=day_offset)

        if close_day != open_day:
            close_dt += timedelta(days=1)

        yield open_dt, close_dt


def calculate_opening_hours_penalty(
    point: TripPoint,
    arrival_time: datetime,
    leave_time: datetime,
) -> float:
    if not point.opening_hours:
        return 0

    best_penalty = float("inf")

    found_period = False

    for open_dt, close_dt in iter_open_periods(
        point,
        arrival_time,
    ):

        found_period = True

        # Perfect fit
        if (
            open_dt <= arrival_time
            and leave_time <= close_dt
        ):
            return 0

        penalty = 0

        # Arrived before opening
        if arrival_time < open_dt:
            penalty += (
                open_dt - arrival_time
            ).total_seconds() / 60

        # Leaving after closing
        if leave_time > close_dt:
            penalty += (
                leave_time - close_dt
            ).total_seconds() / 60

        best_penalty = min(
            best_penalty,
            penalty,
        )

    if not found_period:
        return 0

    return best_penalty


# =========================================================
# ROUTE COST
# =========================================================

def calculate_route_cost(
    graph: Graph,
    route: list[TripPoint],
    start_time: str,
    trip_end_time: str | None = None,
    trip_points: List[TripPoint] | None = None,
) -> tuple[bool, float]:

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

    total_opening_penalty = 0

    for i in range(len(route) - 1):

        current_point = route[i]
        next_point = route[i + 1]

        current_index = index_by_id[current_point.location_id]

        next_index = index_by_id[
            next_point.location_id
        ]

        edge = graph.get_edge(current_index, next_index)

        if edge is None:
            return False, 0

        travel_time = seconds_to_timedelta(edge.duration_seconds)

        arrival_time = (current_time + travel_time)

        stay_duration = get_stay_duration(next_point)

        leave_time = arrival_time + stay_duration

        # ---------------------------------------------
        # HARD CONSTRAINT
        # ---------------------------------------------

        if (
            trip_end_datetime
            and leave_time > trip_end_datetime
        ):
            return False, 0

        # ---------------------------------------------
        # SOFT CONSTRAINT
        # ---------------------------------------------

        opening_penalty = (
            calculate_opening_hours_penalty(
                next_point,
                arrival_time,
                leave_time,
            )
        )

        total_opening_penalty += (
            opening_penalty
        )

        current_time = leave_time

        total_duration_seconds += (
            edge.duration_seconds
        )

        total_duration_seconds += int(
            stay_duration.total_seconds()
        )

    total_cost = (
        total_duration_seconds
        + total_opening_penalty
        * OPENING_HOURS_PENALTY_WEIGHT
    )

    return True, total_cost

# =========================================================
# BRUTE FORCE SEARCH
# =========================================================

def calculate_route_order(
    graph: Graph,
    trip_points: List[TripPoint],
    start_location_id: str,
    trip_start_time: str,
    trip_end_time: str | None = None,
) -> list[str]:

    points_by_id = {
        point.location_id: point
        for point in trip_points
    }

    start_point = points_by_id[start_location_id]

    remaining_points = [
        point
        for point in trip_points
        if point.location_id != start_location_id
    ]

    best_route = None

    best_cost = float("inf")

    for permutation in permutations(remaining_points):

        candidate_route = [start_point, *permutation]

        is_valid, total_cost = (
            calculate_route_cost(
                graph=graph,
                route=candidate_route,
                start_time=trip_start_time,
                trip_end_time=trip_end_time,
                trip_points=trip_points,
            )
        )

        if not is_valid:
            continue

        if total_cost < best_cost:
            best_cost = total_cost
            best_route = candidate_route

    if best_route is None:
        return []

    return [point.location_id for point in best_route]