import csv
import math
import random
from datetime import datetime, timedelta, timezone

# Config
NUM_INTERSECTIONS = 20
DAYS = 7
INTERVAL_MINUTES = 5

# Simple city bounding box (fake coords)
BASE_LAT = 40.0
BASE_LON = -74.0

def generate_intersections():
    intersections = []
    for i in range(NUM_INTERSECTIONS):
        name = f"Intersection {i+1}"
        lat = BASE_LAT + random.uniform(-0.05, 0.05)
        lon = BASE_LON + random.uniform(-0.05, 0.05)
        priority_level = random.choice(["normal", "hospital_route", "school_zone"])
        intersections.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "priority_level": priority_level,
        })
    return intersections

def congestion_pattern(dt: datetime, intersection_index: int) -> int:
    # Base diurnal pattern: morning + evening peaks
    hour = dt.hour + dt.minute / 60
    morning_peak = math.exp(-((hour - 8) ** 2) / 8)
    evening_peak = math.exp(-((hour - 17) ** 2) / 8)
    base = 20 + 50 * (morning_peak + evening_peak)

    # Weekday vs weekend
    if dt.weekday() >= 5:  # weekend
        base *= 0.7

    # Slight per-intersection variation
    base *= 0.8 + 0.4 * (intersection_index / max(1, NUM_INTERSECTIONS - 1))

    # Random noise & occasional spikes
    noise = random.uniform(-10, 10)
    spike = 0
    if random.random() < 0.02:
        spike = random.uniform(20, 40)

    level = max(0, min(100, int(base + noise + spike)))
    return level

def main():
    random.seed(42)

    intersections = generate_intersections()

    # Write intersections CSV
    with open("intersections.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["name", "lat", "lon", "priority_level"],
        )
        writer.writeheader()
        for row in intersections:
            writer.writerow(row)

    # Generate time series
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=DAYS)
    readings = []

    current = start
    while current <= now:
        # snap to 5-minute intervals
        minute = (current.minute // INTERVAL_MINUTES) * INTERVAL_MINUTES
        current_snapped = current.replace(minute=minute, second=0, microsecond=0)

        for idx, _ in enumerate(intersections):
            level = congestion_pattern(current_snapped, idx)
            # Simple mapping from congestion to speed/delay
            speed_kmh = max(5.0, 60.0 * (1 - level / 120.0))
            delay_sec = max(0.0, level * 1.5)

            readings.append({
                "intersection_index": idx,  # we will map to ids later
                "timestamp_utc": current_snapped.isoformat(),
                "congestion_level": level,
                "speed_kmh": round(speed_kmh, 1),
                "delay_sec": round(delay_sec, 1),
                "source": "synthetic",
            })

        current += timedelta(minutes=INTERVAL_MINUTES)

    with open("congestion_readings_raw.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "intersection_index",
                "timestamp_utc",
                "congestion_level",
                "speed_kmh",
                "delay_sec",
                "source",
            ],
        )
        writer.writeheader()
        for row in readings:
            writer.writerow(row)

    print("Wrote intersections.csv and congestion_readings_raw.csv")

if __name__ == "__main__":
    main()