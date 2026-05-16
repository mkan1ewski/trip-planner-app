from datetime import datetime, timedelta
from typing import List

from models import Graph, TripPoint


# =========================================================
# CONFIG
# =========================================================

TRAVEL_TIME_WEIGHT = 1.0
URGENCY_WEIGHT = 500.0
TIME_WINDOW_PENALTY_WEIGHT = 5.0


# =========================================================
# HELPERS
# =========================================================

def parse_time(time_str: str) -> datetime:
    """
    Converts HH:MM into datetime.
    """

    return datetime.strptime(time_str, "%H:%M")


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
# OPENING HOURS
# =========================================================

def is_place_open(
    point: TripPoint,
    arrival_time: datetime,
    leave_time: datetime,
) -> bool:
    """
    Simplified opening-hours validation.

    Currently:
    - if no opening hours -> assume open
    """

    if not point.opening_hours:
        return True

    # TODO:
    # parse google opening_hours structure

    return True


# =========================================================
# TIME WINDOW PENALTY
# =========================================================

def calculate_time_window_penalty(
    point: TripPoint,
    arrival_time: datetime,
) -> float:

    if (
        point.time_window_start is None
        or point.time_window_end is None
    ):
        return 0

    preferred_start = parse_time(
        point.time_window_start
    )

    preferred_end = parse_time(
        point.time_window_end
    )

    # inside preferred window
    if preferred_start <= arrival_time <= preferred_end:
        return 0

    # too early
    if arrival_time < preferred_start:
        diff = preferred_start - arrival_time
        return diff.total_seconds() / 60

    # too late
    diff = arrival_time - preferred_end
    return diff.total_seconds() / 60


# =========================================================
# URGENCY
# =========================================================

def calculate_urgency(
    point: TripPoint,
    arrival_time: datetime,
) -> float:
    """
    Placeholder urgency implementation.

    Future:
    urgency should depend on:
    - closing time
    - remaining opening time
    """

    if not point.time_window_end:
        return 0

    preferred_end = parse_time(
        point.time_window_end
    )

    remaining_minutes = (
        preferred_end - arrival_time
    ).total_seconds() / 60

    if remaining_minutes <= 0:
        return 999999

    return 1 / remaining_minutes


# =========================================================
# COST FUNCTION
# =========================================================

def calculate_cost(
    edge_duration_seconds: int,
    urgency: float,
    time_window_penalty: float,
) -> float:

    return (
        TRAVEL_TIME_WEIGHT
        * edge_duration_seconds
        + URGENCY_WEIGHT
        * urgency
        + TIME_WINDOW_PENALTY_WEIGHT
        * time_window_penalty
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
) -> list[str]:

    # -----------------------------------------------------
    # PREPARE
    # -----------------------------------------------------

    points_by_id = {
        point.location_id: point
        for point in trip_points
    }

    index_by_id = {
        point.location_id: idx
        for idx, point in enumerate(trip_points)
    }

    id_by_index = {
        idx: point.location_id
        for idx, point in enumerate(trip_points)
    }

    current_time = parse_time(trip_start_time)

    trip_end_datetime = (
        parse_time(trip_end_time)
        if trip_end_time
        else None
    )

    current_location_id = start_location_id

    visited = set()

    route_order = []

    # -----------------------------------------------------
    # GREEDY LOOP
    # -----------------------------------------------------

    while True:

        visited.add(current_location_id)

        route_order.append(current_location_id)

        current_index = index_by_id[
            current_location_id
        ]

        best_candidate = None
        best_cost = float("inf")

        # -------------------------------------------------
        # CHECK ALL POSSIBLE DESTINATIONS
        # -------------------------------------------------

        for candidate in trip_points:

            if candidate.location_id in visited:
                continue

            candidate_index = index_by_id[
                candidate.location_id
            ]

            edge = graph.get_edge(
                current_index,
                candidate_index,
            )

            if edge is None:
                continue

            travel_time = seconds_to_timedelta(
                edge.duration_seconds
            )

            arrival_time = (
                current_time + travel_time
            )

            stay_duration = get_stay_duration(
                candidate
            )

            leave_time = (
                arrival_time + stay_duration
            )

            # ---------------------------------------------
            # HARD CONSTRAINT:
            # trip end
            # ---------------------------------------------

            if (
                trip_end_datetime
                and leave_time > trip_end_datetime
            ):
                continue

            # ---------------------------------------------
            # HARD CONSTRAINT:
            # opening hours
            # ---------------------------------------------

            if not is_place_open(
                candidate,
                arrival_time,
                leave_time,
            ):
                continue

            # ---------------------------------------------
            # SOFT CONSTRAINTS
            # ---------------------------------------------

            urgency = calculate_urgency(
                candidate,
                arrival_time,
            )

            time_penalty = (
                calculate_time_window_penalty(
                    candidate,
                    arrival_time,
                )
            )

            cost = calculate_cost(
                edge_duration_seconds=edge.duration_seconds,
                urgency=urgency,
                time_window_penalty=time_penalty,
            )

            # ---------------------------------------------
            # BEST CANDIDATE
            # ---------------------------------------------

            if cost < best_cost:
                best_cost = cost
                best_candidate = candidate

        # -------------------------------------------------
        # NO MORE VALID CANDIDATES
        # -------------------------------------------------

        if best_candidate is None:
            break

        # -------------------------------------------------
        # MOVE TO NEXT POINT
        # -------------------------------------------------

        next_index = index_by_id[
            best_candidate.location_id
        ]

        edge = graph.get_edge(
            current_index,
            next_index,
        )

        travel_time = seconds_to_timedelta(
            edge.duration_seconds
        )

        stay_duration = get_stay_duration(
            best_candidate
        )

        current_time = (
            current_time
            + travel_time
            + stay_duration
        )

        current_location_id = (
            best_candidate.location_id
        )

    return route_order