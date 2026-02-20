# Documentation: [`02_lab.py`](02_lab.py)

Script for the [LAB: Develop a Meaningful API Query](LAB_your_good_api_query.md). Fetches **End-of-Day (EOD)** stock data from Marketstack and displays the most recent trading days in a table.

---

## Overview

`02_lab.py` requests the **20 most recent trading days** of end-of-day data for **Apple (AAPL)** from the Marketstack API. It parses the JSON response, loads records into a **pandas DataFrame**, formats the date column for display, and prints the table to the terminal. Markets are closed on weekends and holidays, so 20 rows correspond to about 20 **weekdays**, not 20 calendar days.

---

## API Endpoint and Parameters

| Item | Value |
|------|--------|
| **API** | [Marketstack](https://marketstack.com/) |
| **Endpoint** | `http://api.marketstack.com/v1/eod` (End-of-Day Data) |
| **Method** | GET (query parameters in URL) |

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `access_key` | Yes | Your API key (use from `.env` in production) |
| `symbols` | Yes | Ticker symbol(s), e.g. `AAPL` (comma-separated for multiple) |
| `limit` | No | Max records to return (default varies; script uses `20`) |
| `sort` | No | `ASC` or `DESC`; script uses `DESC` for most recent first |
| `date_from` | No | Start date `YYYY-MM-DD` |
| `date_to` | No | End date `YYYY-MM-DD` |
| `offset` | No | Pagination offset (e.g. `0`) |

**Example query (script logic):**  
`limit=20` and `sort=DESC` with no date range returns the 20 most recent trading days up to today.

---

## Data Structure

### Response shape

- The API returns **JSON**. Records live under the top-level key **`"data"`** (array of objects).
- Each element is one trading day for the requested symbol(s).

### Key fields (per record)

| Field | Type | Description |
|-------|------|-------------|
| `date` | string | Trading date (YYYY-MM-DD) |
| `open` | number | Opening price |
| `high` | number | High price |
| `low` | number | Low price |
| `close` | number | Closing price |
| `volume` | number | Trading volume |
| `symbol` | string | Ticker (e.g. AAPL) |
| `exchange` | string | Exchange code |
| `adj_open` | number | Adjusted open |
| `adj_high` | number | Adjusted high |
| `adj_low` | number | Adjusted low |
| `adj_close` | number | Adjusted close |
| `adj_volume` | number | Adjusted volume |

**Record count:** The script requests 20 rows; the number of rows printed equals the length of `response.json()["data"]` (up to 20).

---

## Flow (Mermaid)

```mermaid
flowchart LR
    A[Load .env] --> B[GET /v1/eod]
    B --> C[JSON response]
    C --> D[Parse .json]
    D --> E[Extract "data"]
    E --> F[DataFrame]
    F --> G[Format date]
    G --> H[Print table]
```

---

## Usage

### Prerequisites

- Python 3 with: `requests`, `pandas`, `python-dotenv`
- Install: `pip install requests pandas python-dotenv`

### Setup

1. Add a **Marketstack API key** to a `.env` file in the same directory (or parent) as the script, e.g.:
   ```bash
   TEST_API_KEY2=your_marketstack_access_key
   ```
2. In the script, use this key in the request URL as the `access_key` query parameter (the script loads `.env`; replace any hardcoded key with `TEST_API_KEY2` if you prefer to keep the key only in `.env`).

### Run

From the repo root:

```bash
python 01_query_api/02_lab.py
```

Or from `01_query_api/`:

```bash
python 02_lab.py
```

### Expected output

- A line: `Status code: 200`
- A table with columns including **date** (YY-MM-DD), **open**, **high**, **low**, **close**, **volume**, and other EOD fields for the 20 most recent trading days of AAPL.

---

← 🏠 [Back to Top](#documentation-02_labpy)
