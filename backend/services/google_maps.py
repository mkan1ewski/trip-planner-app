import os
import httpx
from dotenv import load_dotenv

load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

async def get_route_matrix(origins: list[str], destinations: list[str], travel_mode: str = "DRIVE"):
    """
    Fetches the route matrix from Google Maps Compute Route Matrix API.
    origins and destinations are lists of Google Maps Place IDs.
    """
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable is not set.")

    url = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,condition"
    }

    payload = {
        "origins": [{"waypoint": {"placeId": place_id}} for place_id in origins],
        "destinations": [{"waypoint": {"placeId": place_id}} for place_id in destinations],
        "travelMode": travel_mode,
    }

    if travel_mode == "DRIVE":
        payload["routingPreference"] = "TRAFFIC_AWARE"

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
