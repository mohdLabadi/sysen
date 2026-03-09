"""
api_client.py
Marketstack End-of-Day (EOD) query helpers for Homework 1.

This module handles:
- loading the Marketstack API key from environment variables
- querying the EOD endpoint with robust error handling
- returning cleaned data for app display and AI reporting
"""

import os
from typing import Dict, Optional, Tuple

import pandas as pd
import requests
from dotenv import load_dotenv


# Load .env values once at import time.
load_dotenv()


def get_marketstack_api_key() -> Optional[str]:
    """Return a Marketstack key from common environment variable names."""
    return os.getenv("TEST_API_KEY2") or os.getenv("MARKETSTACK_API_KEY")


def build_marketstack_url(symbol: str, limit: int, sort_desc: bool) -> str:
    """Build the Marketstack EOD URL (without the API key)."""
    base_url = "http://api.marketstack.com/v1/eod"
    sort = "DESC" if sort_desc else "ASC"
    return f"{base_url}?symbols={symbol}&limit={limit}&sort={sort}"


def query_marketstack_eod(
    symbol: str,
    limit: int = 20,
    sort_desc: bool = True,
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Query Marketstack and return (dataframe, error_message).

    On success:
      - dataframe is non-empty
      - error_message is None
    On failure:
      - dataframe is None
      - error_message contains a user-friendly string
    """
    cleaned_symbol = symbol.strip().upper()
    if not cleaned_symbol:
        return None, "Please enter a stock symbol (example: AAPL)."

    api_key = get_marketstack_api_key()
    if not api_key:
        return None, (
            "Missing Marketstack API key. Add TEST_API_KEY2 or MARKETSTACK_API_KEY "
            "to your .env file."
        )

    safe_limit = max(10, min(int(limit), 60))
    url = build_marketstack_url(cleaned_symbol, safe_limit, sort_desc)
    url_with_key = f"{url}&access_key={api_key}"

    try:
        response = requests.get(url_with_key, timeout=15)
    except requests.exceptions.RequestException as exc:
        return None, f"Network error while contacting Marketstack: {exc}"

    if response.status_code != 200:
        return None, (
            f"Marketstack returned status {response.status_code}. "
            "Check your API key, ticker symbol, or try again shortly."
        )

    try:
        payload = response.json()
    except ValueError:
        return None, "API response was not valid JSON."

    records = payload.get("data", [])
    if not records:
        return None, (
            "No records returned for this symbol. Try a different ticker or widen your query."
        )

    data = pd.DataFrame(records)
    if "date" in data.columns:
        data["date"] = pd.to_datetime(data["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        ordered_cols = ["date"] + [col for col in data.columns if col != "date"]
        data = data[ordered_cols]

    return data, None


def summarize_market_data(data: pd.DataFrame) -> Dict[str, float]:
    """
    Compute compact metrics used by the app and AI prompt.

    Returns a dictionary that is safe for rendering in text output.
    """
    if data.empty or "close" not in data.columns:
        return {}

    numeric_close = pd.to_numeric(data["close"], errors="coerce").dropna()
    if numeric_close.empty:
        return {}

    # Sort by date ascending to compare earliest vs latest close.
    sorted_data = data.sort_values("date")
    sorted_close = pd.to_numeric(sorted_data["close"], errors="coerce").dropna()
    if sorted_close.empty:
        return {}

    first_close = float(sorted_close.iloc[0])
    last_close = float(sorted_close.iloc[-1])
    pct_change = ((last_close - first_close) / first_close * 100.0) if first_close else 0.0

    return {
        "rows": int(len(data)),
        "first_close": round(first_close, 4),
        "last_close": round(last_close, 4),
        "min_close": round(float(numeric_close.min()), 4),
        "max_close": round(float(numeric_close.max()), 4),
        "mean_close": round(float(numeric_close.mean()), 4),
        "pct_change": round(float(pct_change), 4),
    }
