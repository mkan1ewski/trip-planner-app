from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utilities.algorithms.greedy import calculate_route_order as greedy_route_order
from utilities.algorithms.brute import calculate_route_order as  bruteforce_route_order
from utilities.request_saver import save_request
from models import CalculateRouteRequest
from utilities.matrix_parser import get_route_graph

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/calculateBruteforce")
async def calculate_routeBruteforce(payload: CalculateRouteRequest):
    return await calculate_route(payload, algorithm="bruteforce")

@app.post("/api/calculate")
async def calculate_routeGreedy(payload: CalculateRouteRequest):
    return await calculate_route(payload, algorithm="greedy")

async def calculate_route(payload: CalculateRouteRequest, algorithm: str = "greedy") -> dict:
    """
    Receives trip data, queries Google Routes API for distance matrices across multiple travel modes, and returns the results.
    """
    # Uncomment to save incoming requests for testing purposes
    # save_request(payload)
    all_place_ids = [point.location_id for point in payload.trip_points]

    try:
        graph = await get_route_graph(origins=all_place_ids, destinations=all_place_ids, travel_mode=payload.travel_mode)
        if algorithm == "greedy":
            result = greedy_route_order(
                graph=graph,
                trip_points=payload.trip_points,
                start_location_id=payload.trip_start_location_id,
                trip_start_time=payload.trip_start_time,
                trip_end_time=payload.trip_end_time
            )
        else:
            result = bruteforce_route_order(
                graph=graph,
                trip_points=payload.trip_points,
                start_location_id=payload.trip_start_location_id,
                trip_start_time=payload.trip_start_time,
                trip_end_time=payload.trip_end_time
            )
        return {
            "status": "success",
            "route_segments": result["route_segments"],
            "visited_location_ids": result["visited_location_ids"],
            "total_duration_seconds": result["total_duration_seconds"],
        }
    except Exception as e:
        print(f"Error calculating route: {e}")
        return {"status": "error", "message": str(e)}
