# api_main.py
# FastAPI REST API for City Congestion Tracker
# Pairs with MIDTERM_DL_challenge materials
# DSAI Midterm – Supabase → API → Dashboard → AI

import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .env_utils import load_env_from_dotenv


def get_supabase_config() -> dict:
    """Read Supabase URL and key from environment variables."""
    load_env_from_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError(
            "Missing Supabase configuration. "
            "Set SUPABASE_URL and SUPABASE_SERVICE_KEY (or SUPABASE_ANON_KEY)."
        )

    return {"url": url.rstrip("/"), "key": key}


app = FastAPI(title="City Congestion Tracker API")


class Intersection(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    priority_level: str


class CongestionPoint(BaseModel):
    intersection_id: str
    intersection_name: str
    timestamp_utc: datetime
    congestion_level: int
    speed_kmh: Optional[float] = None
    delay_sec: Optional[float] = None


class AISummaryRequest(BaseModel):
    hours: int = 6


class AISummaryResponse(BaseModel):
    hours: int
    generated_at_utc: datetime
    summary: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/intersections", response_model=List[Intersection])
def list_intersections(priority_level: Optional[str] = Query(default=None)) -> List[Intersection]:
    """Return all intersections, optionally filtered by priority level."""
    cfg = get_supabase_config()
    endpoint = f"{cfg['url']}/rest/v1/intersections"

    params = {"select": "id,name,lat,lon,priority_level", "order": "name.asc"}
    if priority_level:
        params["priority_level"] = f"eq.{priority_level}"

    headers = {"apikey": cfg["key"], "Authorization": f"Bearer {cfg['key']}"}

    response = requests.get(endpoint, params=params, headers=headers, timeout=30)
    if not response.ok:
        raise HTTPException(status_code=500, detail="Error fetching intersections from Supabase")

    return response.json()


@app.get("/congestion/top_current", response_model=List[CongestionPoint])
def top_current(limit: int = Query(default=10, ge=1, le=100)) -> List[CongestionPoint]:
    """Return the most congested intersections for the latest available 5-minute interval."""
    cfg = get_supabase_config()
    headers = {"apikey": cfg["key"], "Authorization": f"Bearer {cfg['key']}"}

    # First, find the most recent timestamp_utc available in the readings.
    latest_endpoint = f"{cfg['url']}/rest/v1/congestion_readings"
    latest_params = {
        "select": "timestamp_utc",
        "order": "timestamp_utc.desc",
        "limit": 1,
    }
    latest_resp = requests.get(latest_endpoint, params=latest_params, headers=headers, timeout=30)
    if not latest_resp.ok:
        raise HTTPException(status_code=500, detail="Error fetching latest timestamp from Supabase")

    latest_rows = latest_resp.json()
    if not latest_rows:
        return []

    snapped_iso = latest_rows[0]["timestamp_utc"]

    # Now fetch readings for that latest interval.
    endpoint = latest_endpoint
    params = {
        "select": "intersection_id,timestamp_utc,congestion_level,speed_kmh,delay_sec",
        "timestamp_utc": f"eq.{snapped_iso}",
        "order": "congestion_level.desc",
        "limit": limit,
    }

    response = requests.get(endpoint, params=params, headers=headers, timeout=30)
    if not response.ok:
        raise HTTPException(status_code=500, detail="Error fetching congestion readings from Supabase")

    readings = response.json()
    if not readings:
        return []

    # Fetch intersection names for these ids
    intersection_ids = {row["intersection_id"] for row in readings}
    id_list = ",".join(intersection_ids)

    intersections_endpoint = f"{cfg['url']}/rest/v1/intersections"
    intersections_params = {
        "select": "id,name",
        "id": f"in.({id_list})",
    }

    intersections_resp = requests.get(
        intersections_endpoint,
        params=intersections_params,
        headers=headers,
        timeout=30,
    )
    if not intersections_resp.ok:
        raise HTTPException(status_code=500, detail="Error fetching intersections for congestion results")

    intersections_by_id = {row["id"]: row["name"] for row in intersections_resp.json()}

    results: List[CongestionPoint] = []
    for row in readings:
        intersection_id = row["intersection_id"]
        name = intersections_by_id.get(intersection_id, "Unknown")
        results.append(
            CongestionPoint(
                intersection_id=intersection_id,
                intersection_name=name,
                timestamp_utc=datetime.fromisoformat(row["timestamp_utc"]),
                congestion_level=row["congestion_level"],
                speed_kmh=row.get("speed_kmh"),
                delay_sec=row.get("delay_sec"),
            )
        )

    return results


@app.get("/congestion/timeseries", response_model=List[CongestionPoint])
def congestion_timeseries(
    intersection_id: str,
    start: datetime,
    end: datetime,
) -> List[CongestionPoint]:
    """Return 5-minute congestion readings for one intersection in a time window."""
    cfg = get_supabase_config()
    endpoint = f"{cfg['url']}/rest/v1/congestion_readings"

    params = {
        "select": "intersection_id,timestamp_utc,congestion_level,speed_kmh,delay_sec",
        "intersection_id": f"eq.{intersection_id}",
        "timestamp_utc": f"gte.{start.isoformat()}",
        "timestamp_utc": f"lte.{end.isoformat()}",
        "order": "timestamp_utc.asc",
    }

    headers = {"apikey": cfg["key"], "Authorization": f"Bearer {cfg['key']}"}

    response = requests.get(endpoint, params=params, headers=headers, timeout=30)
    if not response.ok:
        raise HTTPException(status_code=500, detail="Error fetching timeseries from Supabase")

    readings = response.json()

    # Fetch intersection name once
    intersections_endpoint = f"{cfg['url']}/rest/v1/intersections"
    intersections_params = {
        "select": "id,name",
        "id": f"eq.{intersection_id}",
    }
    intersections_resp = requests.get(
        intersections_endpoint,
        params=intersections_params,
        headers=headers,
        timeout=30,
    )
    if not intersections_resp.ok:
        raise HTTPException(status_code=500, detail="Error fetching intersection name")

    intersection_name = (
        intersections_resp.json()[0]["name"] if intersections_resp.json() else "Unknown"
    )

    results: List[CongestionPoint] = []
    for row in readings:
        results.append(
            CongestionPoint(
                intersection_id=intersection_id,
                intersection_name=intersection_name,
                timestamp_utc=datetime.fromisoformat(row["timestamp_utc"]),
                congestion_level=row["congestion_level"],
                speed_kmh=row.get("speed_kmh"),
                delay_sec=row.get("delay_sec"),
            )
        )

    return results


# Simple summary endpoint stub (we can expand this later for AI integration)
@app.get("/congestion/summary")
def congestion_summary(
    hours: int = Query(default=24, ge=1, le=168),
) -> dict:
    """Return a high-level summary for the last N hours (placeholder for AI)."""
    cfg = get_supabase_config()
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=hours)

    endpoint = f"{cfg['url']}/rest/v1/congestion_readings"
    params = {
        "select": "congestion_level",
        "timestamp_utc": f"gte.{start.isoformat()}",
    }
    headers = {"apikey": cfg["key"], "Authorization": f"Bearer {cfg['key']}"}

    response = requests.get(endpoint, params=params, headers=headers, timeout=30)
    if not response.ok:
        raise HTTPException(status_code=500, detail="Error fetching summary data")

    rows = response.json()
    if not rows:
        return {"hours": hours, "count": 0, "avg_congestion": None}

    levels = [row["congestion_level"] for row in rows]
    avg_level = sum(levels) / len(levels)

    return {"hours": hours, "count": len(levels), "avg_congestion": avg_level}


def get_ollama_config() -> dict:
    """Read Ollama Cloud configuration from environment variables."""
    load_env_from_dotenv()
    api_key = os.environ.get("OLLAMA_CLOUD_API_KEY")
    model = os.environ.get("OLLAMA_CLOUD_MODEL", "gpt-oss:120b")

    if not api_key:
        raise RuntimeError("Missing OLLAMA_CLOUD_API_KEY in environment or .env file.")

    # Cloud API host is fixed; see https://docs.ollama.com/cloud
    host = "https://ollama.com"
    return {"host": host.rstrip("/"), "api_key": api_key, "model": model}


@app.post("/ai/summary", response_model=AISummaryResponse)
def ai_summary(body: AISummaryRequest) -> AISummaryResponse:
    """Generate a narrative congestion summary using Ollama Cloud."""
    cfg = get_supabase_config()
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=body.hours)

    # Aggregate congestion by intersection for the window
    endpoint = f"{cfg['url']}/rest/v1/congestion_readings"
    params = {
        "select": "intersection_id,congestion_level",
        "timestamp_utc": f"gte.{start.isoformat()}",
    }
    headers = {"apikey": cfg["key"], "Authorization": f"Bearer {cfg['key']}"}

    response = requests.get(endpoint, params=params, headers=headers, timeout=30)
    if not response.ok:
        raise HTTPException(status_code=500, detail="Error fetching data for AI summary")

    rows = response.json()
    if not rows:
        return AISummaryResponse(
            hours=body.hours,
            generated_at_utc=now,
            summary="No congestion readings available for the requested time window.",
        )

    # Compute simple stats per intersection
    stats: dict = {}
    for row in rows:
        iid = row["intersection_id"]
        level = row["congestion_level"]
        info = stats.setdefault(iid, {"count": 0, "sum": 0, "max": 0})
        info["count"] += 1
        info["sum"] += level
        info["max"] = max(info["max"], level)

    intersection_ids = list(stats.keys())
    id_list = ",".join(intersection_ids)

    intersections_endpoint = f"{cfg['url']}/rest/v1/intersections"
    intersections_params = {
        "select": "id,name,priority_level",
        "id": f"in.({id_list})",
    }
    intersections_resp = requests.get(
        intersections_endpoint,
        params=intersections_params,
        headers=headers,
        timeout=30,
    )
    if not intersections_resp.ok:
        raise HTTPException(status_code=500, detail="Error fetching intersections for AI summary")

    intersections_by_id = {row["id"]: row for row in intersections_resp.json()}

    # Build compact summary payload for the model
    summary_items = []
    for iid, info in stats.items():
        intersection = intersections_by_id.get(iid)
        if not intersection:
            continue
        avg = info["sum"] / info["count"]
        summary_items.append(
            {
                "id": iid,
                "name": intersection["name"],
                "priority_level": intersection["priority_level"],
                "avg_congestion": avg,
                "max_congestion": info["max"],
            }
        )

    ollama_cfg = get_ollama_config()

    system_prompt = (
        "You are an assistant for a city emergency services dispatcher. "
        "You receive summarized congestion statistics for intersections over a given time window. "
        "Write a short, concrete summary (3–6 sentences) describing: "
        "(1) which intersections are currently of greatest concern, "
        "(2) how severe congestion is overall, and "
        "(3) 2–3 routing recommendations or warnings for emergency vehicles."
    )

    user_content = {
        "time_window_hours": body.hours,
        "generated_at_utc": now.isoformat(),
        "intersections": summary_items,
    }

    payload = {
        "model": ollama_cfg["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Given the following congestion summary data (in JSON), "
                    "write the requested narrative:\n\n"
                    f"{user_content}"
                ),
            },
        ],
        "stream": False,
    }

    ai_headers = {
        "Authorization": ollama_cfg["api_key"],
        "Content-Type": "application/json",
    }

    ai_url = f"{ollama_cfg['host']}/api/chat"
    ai_resp = requests.post(ai_url, headers=ai_headers, json=payload, timeout=60)
    if not ai_resp.ok:
        raise HTTPException(status_code=500, detail="Error calling Ollama Cloud API")

    ai_json = ai_resp.json()
    # Cloud chat format: { message: { role, content }, ... }
    try:
        summary_text = ai_json["message"]["content"].strip()
    except Exception:
        summary_text = "AI response format was unexpected. Please check the server logs."

    return AISummaryResponse(
        hours=body.hours,
        generated_at_utc=now,
        summary=summary_text,
    )

