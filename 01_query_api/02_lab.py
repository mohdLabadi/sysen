# API name: https://marketstack.com/ 

# Endpoint: http://api.marketstack.com/v1/eod (End-of-Day Data Endpoint)

# Parameters: &sort=DESC &date_from=YYYY-MM-DD &date_to=YYYY-MM-DD &limit=100 &offset=0
# Document: number of records, key fields, data structure


# This query returns the 20 most recent trading days of end-of-day data for Apple (AAPL).
# The market is closed on weekends and holidays, so you get ~20 weekdays, not 20 calendar days.
# The data is returned in JSON, then shown in a DataFrame with date first.

import pandas as pd
import requests
import os
from dotenv import load_dotenv


load_dotenv(".env")

TEST_API_KEY2 = os.getenv("TEST_API_KEY2")

# limit=20 + sort=DESC gives the 20 most recent trading days (no date filter = up to today)
response2 = requests.get(
    "http://api.marketstack.com/v1/eod?access_key=d528295f0499ebe60d13580fb3ce28c5&symbols=AAPL"
    "&limit=20&sort=DESC",
)

# Check that the request succeeded before parsing
print("Status code:", response2.status_code)

# Parse JSON; Marketstack returns records in the "data" key
json_data = response2.json()
records = json_data.get("data", [])

# Convert list of records to a pandas DataFrame for nice tabular display
df = pd.DataFrame(records)

# Shorten date to YY-MM-DD for terminal display (e.g. 24-01-15)
df["date"] = pd.to_datetime(df["date"]).dt.strftime("%y-%m-%d")

# Put date first; API returns exactly 20 rows (most recent trading days)
cols = ["date"] + [c for c in df.columns if c != "date"]
display_df = df[cols]

print("\nEnd-of-Day data (most recent 20 trading days):")
print(display_df.to_string(index=False))
