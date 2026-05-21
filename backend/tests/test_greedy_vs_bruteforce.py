import json
from pathlib import Path
import requests
from dotenv import load_dotenv
import os
load_dotenv()

API_URL = os.getenv("API_BASE_URL") + "/api/calculate"

DATA_DIR = Path("tests/data")


def load_payload(file_path: Path) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_saved_requests():
    print("Testing saved requests...")

    request_files = sorted(DATA_DIR.glob("test_*.json"))

    for file_path in request_files:

        payload = load_payload(file_path)

        response = requests.post(API_URL, json=payload)

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "success"

        print(f"{file_path.name}:", data["route_order"])

if __name__ == "__main__":
    test_saved_requests()