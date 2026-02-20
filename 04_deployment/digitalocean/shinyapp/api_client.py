"""
api_client.py
Helper functions for querying the Marketstack EOD API.
Pairs with 01_query_api/02_lab.py
Tim Fraser (course materials), adapted for Shiny app use.

This module wraps the Marketstack End-of-Day (EOD) endpoint in a small,
well-documented function that:
- builds a URL from user inputs
- handles HTTP and JSON errors gracefully
- returns a pandas DataFrame that is easy to display in the Shiny app
"""

# 0. Setup #################################

## 0.1 Load packages ############################

import os
from typing import Optional, Tuple

import pandas as pd
import requests
from dotenv import load_dotenv


## 0.2 Load environment variables ################

# Load variables from a .env file if it exists.
# We call load_dotenv() with no path so that python-dotenv will:
# - check the current working directory, and
# - walk up parent directories to find the first .env it can.
# This lets you keep a single .env at the project root and still
# run the Shiny app from 02_productivity/shinyapp.
# In Docker/App Platform, use env vars set in the dashboard.
load_dotenv()


def get_marketstack_api_key() -> Optional[str]:
    """
    Get the Marketstack API key from environment variables.

    We first look for TEST_API_KEY2 to stay consistent with 02_lab.py.
    If that is not set, we fall back to MARKETSTACK_API_KEY.

    Returns
    -------
    Optional[str]
        The API key string, or None if not found.
    """
    # Prefer TEST_API_KEY2 for consistency with 02_lab.py,
    # but fall back to MARKETSTACK_API_KEY if needed.
    api_key = os.getenv("TEST_API_KEY2") or os.getenv("MARKETSTACK_API_KEY")
    return api_key


def build_marketstack_url(
    symbol: str,
    limit: int = 20,
    sort_desc: bool = True,
) -> str:
    """
    Build the Marketstack EOD URL for a single symbol.

    Parameters
    ----------
    symbol : str
        Stock ticker symbol (e.g., "AAPL").
    limit : int
        Number of records to request (trading days, not calendar days).
    sort_desc : bool
        If True, request most recent days first (DESC); otherwise ASC.

    Returns
    -------
    str
        Fully parameterized URL (without the access_key).
    """
    base_url = "http://api.marketstack.com/v1/eod"
    sort = "DESC" if sort_desc else "ASC"
    # You can add additional parameters here later (date_from, date_to, etc.)
    url = f"{base_url}?symbols={symbol}&limit={limit}&sort={sort}"
    return url


def query_marketstack_eod(
    symbol: str,
    limit: int = 20,
    sort_desc: bool = True,
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Query the Marketstack EOD endpoint and return a cleaned DataFrame.

    This function is designed to be called from the Shiny server logic.
    It always returns a tuple:
    - df: a pandas DataFrame if successful, otherwise None
    - error: an error message string if something went wrong, otherwise None

    Parameters
    ----------
    symbol : str
        Stock ticker symbol (e.g., "AAPL").
    limit : int
        Number of records to request (trading days, not calendar days).
    sort_desc : bool
        If True, request most recent days first (DESC); otherwise ASC.

    Returns
    -------
    Tuple[Optional[pd.DataFrame], Optional[str]]
        (df, error_message)
    """
    symbol = symbol.strip().upper()
    if not symbol:
        return None, "Please enter a stock symbol (for example: AAPL)."

    api_key = get_marketstack_api_key()
    if not api_key:
        return None, (
            "Missing API key. Set TEST_API_KEY2 or MARKETSTACK_API_KEY in your .env file "
            "before running the app."
        )

    url = build_marketstack_url(symbol=symbol, limit=limit, sort_desc=sort_desc)
    url_with_key = f"{url}&access_key={api_key}"

    try:
        response = requests.get(url_with_key, timeout=10)
    except requests.exceptions.RequestException as exc:
        return None, f"Network error while contacting Marketstack: {exc}"

    if response.status_code != 200:
        return None, (
            f"API returned status code {response.status_code}. "
            "Double-check your API key, request parameters, or try again later."
        )

    try:
        json_data = response.json()
    except ValueError:
        return None, "The API returned a response that could not be parsed as JSON."

    # Marketstack returns records in the "data" key
    records = json_data.get("data", [])
    if not records:
        return None, "The API returned no data for this symbol. Try a different ticker or date range."

    df = pd.DataFrame(records)

    # Shorten the date to YY-MM-DD for a cleaner display, similar to 02_lab.py
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%y-%m-%d")
        cols = ["date"] + [c for c in df.columns if c != "date"]
        df = df[cols]

    return df, None
