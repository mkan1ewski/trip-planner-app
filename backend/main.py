import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import CalculateRouteRequest
from services.google_maps import get_route_matrix

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

@app.post("/api/calculate")
async def calculate_route(payload: CalculateRouteRequest):
    """
    Receives trip data, queries Google Routes API for distance matrices across multiple travel modes, and returns the results.
    """
    all_place_ids = [point.location_id for point in payload.trip_points]

    try:
        tasks = [
            get_route_matrix(origins=all_place_ids, destinations=all_place_ids, travel_mode=mode)
            for mode in payload.travel_modes
        ]
        results = await asyncio.gather(*tasks)

        matrices = {mode: matrix for mode, matrix in zip(payload.travel_modes, results)}

        return {
            "status": "success",
            "message": f"Got matrix data for modes: {', '.join(payload.travel_modes)}",
            "matrices": matrices
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
