# Shiny Marketstack EOD Explorer

## Overview

This app is a small Shiny for Python application that queries the Marketstack End-of-Day (EOD) API and displays recent stock price data in an interactive table. It builds directly on the API work from `01_query_api/02_lab.py` and shows how to turn a script into a user-friendly web interface.

Users can choose a stock symbol, number of recent trading days, and sorting order, then click a button to run the query and view the results. Above the table, the app also presents a short, finance-style narrative that interprets recent price momentum (over the requested window) in investor terms.

## Installation and Requirements

- Python 3.9 or later
- A Marketstack API key stored in a `.env` file in the project root (same level as `01_query_api`):
  - `TEST_API_KEY2` (preferred for consistency with `02_lab.py`), or
  - `MARKETSTACK_API_KEY`

Install the app's dependencies into your environment:

```bash
cd 02_productivity/shinyapp
pip install -r requirements.txt
```

## API Configuration

Create a `.env` file in the project root (where your other labs live), if you do not already have one, and add your API key:

```bash
TEST_API_KEY2=your_marketstack_key_here
```

You can also use `MARKETSTACK_API_KEY` instead if you prefer.

## How to Run the App

From the project root (the same directory that contains `02_productivity`), run:

```bash
cd 02_productivity/shinyapp
shiny run --reload app.py
```

Then open the URL printed in the terminal (usually `http://127.0.0.1:8000`) in a browser.

## Usage Instructions

1. Enter a stock symbol in the sidebar, for example `AAPL`.
2. Choose how many recent trading days to request (between 5 and 60).
3. Decide whether to show the most recent days first.
4. Click **Run API query**.
5. Read the **momentum narrative** card at the top, which:
   - Summarizes the percent change in closing price over the requested period.
   - Uses basic financial language (e.g., positive momentum, drawdown, range-bound) to describe a short-term stance.
   - Emphasizes that this is a simple illustration, not full investment advice.
6. Explore the interactive table of EOD data below the narrative.

If the API key is missing, the symbol is invalid, or the API returns an error, the app will display a clear error message instead of failing silently.

## Screenshots

Include screenshots in this folder (or a nearby `docs` folder) to document the app’s behavior. At minimum, capture:

- The main UI before any query is run.
- A successful query showing both the momentum narrative and EOD results in the table.
- An example of error handling (for example, missing API key or invalid symbol).

Reference these screenshots from your course submission as needed.

