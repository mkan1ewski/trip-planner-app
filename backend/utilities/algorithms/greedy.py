from datetime import datetime, timedelta, time
import os
from typing import List
from models import Graph, TripPoint
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# CONFIG
# =========================================================
TRAVEL_TIME_WEIGHT = float(os.getenv("TRAVEL_TIME_WEIGHT") or 1.0)
URGENCY_WEIGHT = float(os.getenv("URGENCY_WEIGHT") or 21)
TIME_WINDOW_PENALTY_WEIGHT = float(os.getenv("TIME_WINDOW_PENALTY_WEIGHT") or 7.0)
ATTRACTIVENESS_WEIGHT = float(os.getenv("ATTRACTIVENESS_WEIGHT") or 4.0)
MAX_WAIT_HOURS = float(os.getenv("MAX_WAIT_HOURS") or 2)


# =========================================================
# HELPERS
# =========================================================

def parse_time(time_str: str, start_date: datetime) -> datetime:
    """
    Converts HH:MM into datetime.
    """
    return datetime.combine(start_date, datetime.strptime(time_str, "%H:%M").time())

def parse_datetime(datetime_str: str) -> datetime:
    """
    Converts ISO datetime-local string into datetime.

    Example:
    2025-08-10T14:30
    """

    return datetime.fromisoformat(datetime_str)

def to_google_day(dt: datetime) -> int:
    return (dt.weekday() + 1) % 7

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

        open_dt = datetime.combine(
            reference_date.date(),
            time(hour=open_data["hours"], minute=open_data["minutes"]),
        )

        close_dt = datetime.combine(
            reference_date.date(),
            time(hour=close_data["hours"], minute=close_data["minutes"])
        )

        current_day = to_google_day(reference_date)

        day_offset = (open_day - current_day) % 7

        open_dt += timedelta(days=day_offset)
        close_dt += timedelta(days=day_offset)

        if close_day != open_day:
            close_dt += timedelta(days=1)

        yield open_dt, close_dt

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

        actual_arrival = max(arrival_time, open_dt)

        leave_time = actual_arrival + stay_duration

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
    
def get_closing_datetime(point: TripPoint, arrival_time: datetime) -> datetime | None:
    for open_dt, close_dt in iter_open_periods(point, arrival_time):
        if open_dt <= arrival_time <= close_dt:
            return close_dt

    return None

def minutes_to_timedelta(minutes: int) -> timedelta:
    return timedelta(minutes=minutes)


def seconds_to_timedelta(seconds: int) -> timedelta:
    return timedelta(seconds=seconds)


def get_stay_duration(point: TripPoint) -> timedelta:
    """
    Currently uses average stay duration.
    """

    avg_minutes = (
        point.min_duration_minutes
        + point.max_duration_minutes
    ) // 2

    return minutes_to_timedelta(avg_minutes)

# =========================================================
# TIME WINDOW PENALTY
# =========================================================

def calculate_time_window_penalty(
    point: TripPoint,
    arrival_time: datetime,
) -> float:

    preferred_start = (
        parse_time(
            point.time_window_start,
            arrival_time,
        )
        if point.time_window_start
        else None
    )

    preferred_end = (
        parse_time(
            point.time_window_end,
            arrival_time,
        )
        if point.time_window_end
        else None
    )

    if preferred_start is None and preferred_end is None:
        return 0

    if preferred_start and preferred_end:
        if preferred_start <= arrival_time <= preferred_end:
            return 0

        if arrival_time < preferred_start:
            diff = preferred_start - arrival_time

            return -(diff.total_seconds() / 60)

        diff = arrival_time - preferred_end
        return diff.total_seconds() / 60

    if preferred_start:
        if arrival_time >= preferred_start:
            return 0

        diff = preferred_start - arrival_time

        return -(diff.total_seconds() / 60)

    if preferred_end:
        if arrival_time <= preferred_end:
            return 0

        diff = arrival_time - preferred_end
        return diff.total_seconds() / 60

    return 0


# =========================================================
# URGENCY
# =========================================================

def calculate_urgency(point: TripPoint, arrival_time: datetime) -> float:
    """
    Urgency based on remaining opening time.

    Smaller remaining time -> higher urgency.
    """
    closing_datetime = get_closing_datetime(point, arrival_time)

    if not closing_datetime:
        return 0

    remaining_minutes = (closing_datetime - arrival_time).total_seconds() / 60

    if remaining_minutes <= 0:
        return 999999
    
    return 1000 / remaining_minutes

# =========================================================
# COST FUNCTION
# =========================================================

def calculate_cost(
    edge_duration_seconds: int,
    urgency: float,
    time_window_penalty: float,
    attractiveness: float,
) -> float:
    # print("-" * 100)
    # print(f"travel_time_cost: {TRAVEL_TIME_WEIGHT * edge_duration_seconds}")
    # print(f"urgency_cost: {URGENCY_WEIGHT * urgency}")
    # print(f"time_window_penalty_cost: {TIME_WINDOW_PENALTY_WEIGHT * time_window_penalty}")
    # print(f"attractiveness_cost: {ATTRACTIVENESS_WEIGHT * attractiveness}")
    # print(f"total_cost: {TRAVEL_TIME_WEIGHT * edge_duration_seconds - URGENCY_WEIGHT * urgency + TIME_WINDOW_PENALTY_WEIGHT * time_window_penalty - ATTRACTIVENESS_WEIGHT * attractiveness}")
    return (
        TRAVEL_TIME_WEIGHT
        * edge_duration_seconds
        - URGENCY_WEIGHT
        * urgency
        - TIME_WINDOW_PENALTY_WEIGHT
        * time_window_penalty
        - ATTRACTIVENESS_WEIGHT
        * attractiveness
    )


# =========================================================
# MAIN GREEDY ALGORITHM
# =========================================================

def calculate_route_order(
    graph: Graph,
    trip_points: List[TripPoint],
    start_location_id: str,
    trip_start_time: str,
    trip_end_time: str | None = None,
):
    index_by_id = {
        point.location_id: idx
        for idx, point in enumerate(trip_points)
    }

    current_time = parse_datetime(trip_start_time)

    trip_end_datetime = (
        parse_datetime(trip_end_time)
        if trip_end_time
        else None
    )

    total_duration_seconds = 0
    current_location_id = start_location_id

    start_point = next(point for point in trip_points if point.location_id == start_location_id)

    start_stay_duration = get_stay_duration(start_point)

    start_visit_info = calculate_visit_times(start_point, current_time, start_stay_duration)

    if not start_visit_info["is_valid"]:
        return {
            "route_segments": [],
            "visited_location_ids": [],
            "total_duration_seconds": 0,
        }

    current_time = start_visit_info["leave_time"]

    total_duration_seconds += (start_visit_info["waiting_time_seconds"])

    total_duration_seconds += int(start_stay_duration.total_seconds())

    visited = set()

    route_segments = []


    # -----------------------------------------------------
    # GREEDY LOOP
    # -----------------------------------------------------

    while True:

        visited.add(current_location_id)

        current_index = index_by_id[current_location_id]

        best_candidate = None
        best_cost = float("inf")
        best_visit_info = None

        # -------------------------------------------------
        # CHECK ALL POSSIBLE DESTINATIONS
        # -------------------------------------------------
        for candidate in trip_points:

            if candidate.location_id in visited:
                continue

            candidate_index = index_by_id[candidate.location_id]

            if (edge := graph.get_edge(current_index, candidate_index)) is None:
                continue

            travel_time = seconds_to_timedelta(edge.duration_seconds)

            arrival_time = current_time + travel_time

            stay_duration = get_stay_duration(candidate)

            visit_info = calculate_visit_times(
                candidate,
                arrival_time,
                stay_duration,
            )

            if not visit_info["is_valid"]:
                continue

            arrival_time = visit_info["arrival_time"]

            leave_time = visit_info["leave_time"]

            waiting_time_seconds = visit_info[
                "waiting_time_seconds"
            ]

            # ---------------------------------------------
            # HARD CONSTRAINT:
            # trip end
            # ---------------------------------------------

            exceeds_trip_end = (
                trip_end_datetime
                and leave_time > trip_end_datetime
            )

            if exceeds_trip_end:
                continue
            # ---------------------------------------------
            # SOFT CONSTRAINTS
            # ---------------------------------------------

            urgency = calculate_urgency(candidate, arrival_time)

            time_penalty = calculate_time_window_penalty(candidate, arrival_time)

            attractiveness = (candidate.rating or 5) * 100
            cost = calculate_cost(
                edge_duration_seconds=edge.duration_seconds,
                urgency=urgency,
                time_window_penalty=time_penalty,
                attractiveness=attractiveness,
            )

            # ---------------------------------------------
            # BEST CANDIDATE
            # ---------------------------------------------

            if cost < best_cost:
                best_cost = cost
                best_candidate = candidate
                best_visit_info = visit_info

        # -------------------------------------------------
        # NO MORE VALID CANDIDATES
        # -------------------------------------------------

        if best_candidate is None:
            break

        # -------------------------------------------------
        # MOVE TO NEXT POINT
        # -------------------------------------------------

        next_index = index_by_id[best_candidate.location_id]

        edge = graph.get_edge(current_index, next_index)

        route_segments.append({
            "from_location_id": current_location_id,
            "to_location_id": best_candidate.location_id,
            "travel_mode": edge.travel_mode,
            "travel_duration_seconds": edge.duration_seconds,
            "distance_meters": edge.distance_meters,
        })

        stay_duration = get_stay_duration(best_candidate)
        waiting_time_seconds = best_visit_info["waiting_time_seconds"]

        leave_time = best_visit_info["leave_time"]

        total_duration_seconds += edge.duration_seconds

        total_duration_seconds += waiting_time_seconds

        total_duration_seconds += int(stay_duration.total_seconds())

        current_time = leave_time

        current_location_id = best_candidate.location_id

    return {
        "route_segments": route_segments,
        "visited_location_ids": [
            segment["from_location_id"]
            for segment in route_segments
        ] + (
            [route_segments[-1]["to_location_id"]]
            if route_segments
            else [start_location_id]
        ),
        "total_duration_seconds": total_duration_seconds,
    }