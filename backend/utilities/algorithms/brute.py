from itertools import permutations
from datetime import timedelta
from typing import List

from models import Graph, TripPoint

from utilities.algorithms.greedy import (
    parse_time,
    get_stay_duration,
    seconds_to_timedelta,
    is_place_open,
)


def calculate_route_time(
    graph: Graph,
    route: list[TripPoint],
    start_time: str,
    trip_end_time: str | None = None,
    trip_points: List[TripPoint] | None = None,
) -> tuple[bool, int]:
    """
    Calculates total route duration in seconds.

    Returns:
    (
        is_valid_route,
        total_duration_seconds
    )
    """
    index_by_id = {
        point.location_id: idx
        for idx, point in enumerate(trip_points)
    }

    current_time = parse_time(start_time)

    trip_end_datetime = (
        parse_time(trip_end_time)
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
        # print(f"Edge from {route[i].location_name} to {next_point.location_name}: {edge}")

        if edge is None:
            return False, 0

        travel_time = seconds_to_timedelta(
            edge.duration_seconds
        )

        arrival_time = current_time + travel_time

        stay_duration = get_stay_duration(
            next_point
        )

        leave_time = (
            arrival_time + stay_duration
        )

        if not is_place_open(
            next_point,
            arrival_time,
            leave_time,
        ):
            return False, 0

        if (
            trip_end_datetime
            and leave_time > trip_end_datetime
        ):
            return False, 0

        current_time = leave_time

        total_duration_seconds += (
            edge.duration_seconds
        )

        total_duration_seconds += int(
            stay_duration.total_seconds()
        )

    return True, total_duration_seconds


def calculate_optimal_route_bruteforce(
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

    start_point = points_by_id[
        start_location_id
    ]

    remaining_points = [
        point
        for point in trip_points
        if point.location_id != start_location_id
    ]

    best_route = None

    best_duration = float("inf")

    for permutation in permutations(
        remaining_points
    ):
        candidate_route = [
            start_point,
            *permutation,
        ]

        is_valid, total_duration = (
            calculate_route_time(
                graph=graph,
                route=candidate_route,
                start_time=trip_start_time,
                trip_end_time=trip_end_time,
                trip_points=trip_points,
            )
        )

        if not is_valid:
            continue

        if total_duration < best_duration:

            best_duration = total_duration

            best_route = candidate_route

    if best_route is None:
        return []

    return [
        point.location_id
        for point in best_route
    ]