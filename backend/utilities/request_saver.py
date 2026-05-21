from pathlib import Path
import json
import re

from models import CalculateRouteRequest

def save_request(payload: CalculateRouteRequest, folder_path: str = "tests/data/") -> None:
    folder = Path(folder_path)

    folder.mkdir(parents=True, exist_ok=True)

    existing_indices = []

    pattern = re.compile(r"request_(\d+)\.json")

    for file in folder.iterdir():

        if not file.is_file():
            continue

        match = pattern.match(file.name)

        if match:
            existing_indices.append(int(match.group(1)))

    next_index = max(existing_indices, default=0) + 1

    file_path = folder / f"request_{next_index}.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(payload.dict(), file, indent=2)

    print(f"Saved request to: {file_path}")