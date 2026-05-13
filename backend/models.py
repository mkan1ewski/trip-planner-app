from pydantic import BaseModel

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

class CalculateRouteRequest(BaseModel):
    trip_start_location_id: str | None = None
    trip_start_time: str | None = None
    trip_end_time: str | None = None
    travel_modes: list[str] = ["DRIVE"]
    trip_points: list[TripPoint]
