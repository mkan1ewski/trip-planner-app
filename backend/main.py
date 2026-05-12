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
    Receives trip data, queries Google Routes API for the distance matrix, and returns the results.
    """
    all_place_ids = [point.location_id for point in payload.trip_points]
    origins = all_place_ids
    destinations = all_place_ids

    try:
        matrix_data = await get_route_matrix(origins=origins, destinations=destinations)
        return {
            "status": "success",
            "message": "Got matrix data from Google",
            "matrix": matrix_data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
