import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utilities.algorithms.greedy import calculate_route_order as greedy_route_order
from utilities.algorithms.brute import calculate_optimal_route_bruteforce
from models import CalculateRouteRequest
from services.google_maps import get_route_matrix
from utilities.matrix_parser import get_route_graph

app = FastAPI()

origins = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/calculate")
async def calculate_route(payload: CalculateRouteRequest):
    """
    Receives trip data, queries Google Routes API for distance matrices across multiple travel modes, and returns the results.
    """
    all_place_ids = [point.location_id for point in payload.trip_points]

    try:
        graph = await get_route_graph(origins=all_place_ids, destinations=all_place_ids, travel_mode=payload.travel_mode)
        # result = greedy_route_order(
        result = calculate_optimal_route_bruteforce(
            graph=graph,
            trip_points=payload.trip_points,
            start_location_id=payload.trip_start_location_id,
            trip_start_time=payload.trip_start_time,
            trip_end_time=payload.trip_end_time
        )
        return {
            "status": "success",
            "route_order": result
        }
    except Exception as e:
        print(f"Error calculating route: {e}")
        return {"status": "error", "message": str(e)}
