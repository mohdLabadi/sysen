import csv
import json
import os
from typing import Dict, List

import requests

from env_utils import load_env_from_dotenv


# load_congestion_readings.py
# Load synthetic congestion readings into Supabase
# Pairs with generate_synthetic_congestion.py
# DSAI Midterm – City Congestion Tracker
#
# This script:
# - Fetches intersections from Supabase
# - Aligns them with intersection_index from congestion_readings_raw.csv
# - Bulk inserts rows into the congestion_readings table


def get_supabase_config() -> Dict[str, str]:
    """Read Supabase URL and key from environment variables."""
    load_env_from_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError(
            "Missing Supabase configuration. "
            "Set SUPABASE_URL and SUPABASE_SERVICE_KEY (or SUPABASE_ANON_KEY) in your environment."
        )

    return {"url": url.rstrip("/"), "key": key}


def fetch_intersections(cfg: Dict[str, str]) -> List[Dict[str, str]]:
    """Fetch all intersections from Supabase, ordered by name."""
    endpoint = f"{cfg['url']}/rest/v1/intersections"
    params = {
        "select": "id,name,lat,lon,priority_level,created_at",
        "order": "name.asc",
    }
    headers = {
        "apikey": cfg["key"],
        "Authorization": f"Bearer {cfg['key']}",
    }

    response = requests.get(endpoint, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def read_congestion_raw(path: str) -> List[Dict[str, str]]:
    """Read raw congestion readings from CSV."""
    rows: List[Dict[str, str]] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def bulk_insert_readings(cfg: Dict[str, str], readings: List[Dict[str, object]]) -> None:
    """Insert readings into Supabase in batches."""
    endpoint = f"{cfg['url']}/rest/v1/congestion_readings"
    headers = {
        "apikey": cfg["key"],
        "Authorization": f"Bearer {cfg['key']}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    batch_size = 500
    total = len(readings)

    for start in range(0, total, batch_size):
        batch = readings[start : start + batch_size]
        print(f"Inserting rows {start + 1} to {min(start + batch_size, total)} of {total}...")
        response = requests.post(endpoint, headers=headers, data=json.dumps(batch), timeout=60)
        if not response.ok:
            print("Error during insert:")
            print(response.status_code, response.text)
            response.raise_for_status()

    print("Finished inserting congestion_readings.")


def main() -> None:
    cfg = get_supabase_config()

    print("Fetching intersections from Supabase...")
    intersections = fetch_intersections(cfg)

    if not intersections:
        raise RuntimeError("No intersections found in Supabase. Import intersections.csv first.")

    # Map intersection_index (0..N-1) to Supabase ids using name ordering
    # generate_synthetic_congestion.py also created intersections in order: Intersection 1, 2, ...
    intersections_sorted = sorted(intersections, key=lambda x: x["name"])
    index_to_id = {index: row["id"] for index, row in enumerate(intersections_sorted)}

    print("Reading local congestion_readings_raw.csv...")
    raw_rows = read_congestion_raw("congestion_readings_raw.csv")

    prepared: List[Dict[str, object]] = []
    for raw in raw_rows:
        intersection_index = int(raw["intersection_index"])
        intersection_id = index_to_id.get(intersection_index)
        if not intersection_id:
            raise RuntimeError(f"No intersection_id found for intersection_index={intersection_index}")

        prepared.append(
            {
                "intersection_id": intersection_id,
                "timestamp_utc": raw["timestamp_utc"],
                "congestion_level": int(raw["congestion_level"]),
                "speed_kmh": float(raw["speed_kmh"]),
                "delay_sec": float(raw["delay_sec"]),
                "source": raw.get("source", "synthetic"),
            }
        )

    print(f"Prepared {len(prepared)} congestion readings for insert.")
    bulk_insert_readings(cfg, prepared)


if __name__ == "__main__":
    main()

