from dataclasses import dataclass, field
from enum import Enum
from typing import Dict
from pydantic import BaseModel, Field

class TravelMode(str, Enum):
    DRIVE = "DRIVE"
    WALK = "WALK"
    TRANSIT = "TRANSIT"

class Coordinates(BaseModel):
    latitude: float
    longitude: float

class TripPoint(BaseModel):
    location_id: str
    location_name: str
    min_duration_minutes: int
    max_duration_minutes: int
    time_window_start: str | None = None
    time_window_end: str | None = None
    coordinates: Coordinates
    opening_hours: dict | None = None
    rating: float | None = None

class CalculateRouteRequest(BaseModel):
    trip_start_location_id: str | None = None
    trip_start_time: str | None = None
    trip_end_time: str | None = None
    travel_mode: TravelMode = Field(
        default=TravelMode.DRIVE
    )
    trip_points: list[TripPoint]

@dataclass
class Edge:
    origin_index: int
    destination_index: int
    duration_seconds: int
    distance_meters: int
    travel_mode: TravelMode


@dataclass
class Graph:
    graph: Dict[int, Dict[int, Edge]] = field(default_factory=dict)

    def add_edge(self, edge: Edge) -> None:
        if edge.origin_index not in self.graph:
            self.graph[edge.origin_index] = {}

        self.graph[edge.origin_index][edge.destination_index] = edge

    def get_edge(self, origin: int, destination: int) -> Edge | None:
        return self.graph.get(origin, {}).get(destination)

    def get_neighbors(self, origin: int) -> Dict[int, Edge]:
        return self.graph.get(origin, {})