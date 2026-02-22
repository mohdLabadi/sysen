# HW1 AI-Powered Reporter App

This folder contains a complete app for `03_query_ai/HOMEWORK1.md` that combines:

- API integration from `01_query_api/LAB_your_good_api_query.md`
- Shiny app interface from `02_productivity/LAB_cursor_shiny_app.md`
- AI reporting from `03_query_ai/LAB_ai_reporter.md`

## What this app does

The app queries Marketstack end-of-day stock data, shows results in a Shiny UI, computes quick summary metrics, and generates an AI-written report (OpenAI or Ollama Cloud). It also supports a local fallback summary when AI keys are not configured.

## Project files

- `app.py`: Main Shiny for Python application (UI + server logic)
- `api_client.py`: Marketstack query and data summarization helpers
- `ai_reporter.py`: Prompt construction and AI API calls
- `requirements.txt`: Python dependencies

## 1) Setup

From repo root:

```bash
cd 04_deployment/hw1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Configure API keys

Create or update a `.env` file in the **repository root** (`/Users/mohammadlabadi/coding/dsai/.env`):

```bash
# Required for stock data query
TEST_API_KEY2=your_marketstack_key_here

# Optional AI providers (set one or both)
OPENAI_API_KEY=your_openai_key_here
OLLAMA_API_KEY=your_ollama_cloud_key_here

# Optional model overrides
OPENAI_MODEL=gpt-4o-mini
OLLAMA_MODEL=gpt-oss:20b-cloud
```

Notes:
- The app accepts `MARKETSTACK_API_KEY` if `TEST_API_KEY2` is not set.
- If no AI key is set, choose `Local summary only` inside the app.

## 3) Run the app

```bash
cd 04_deployment/hw1
source .venv/bin/activate
shiny run --reload app.py
```

Open the local URL printed in terminal (usually `http://127.0.0.1:8000`).

## 4) Use the app

1. Enter a ticker symbol (`AAPL`, `MSFT`, etc.) and trading-day limit.
2. Click **1) Run API Query** to load data.
3. Review query status, data snapshot, and table output.
4. Select AI provider (`Local`, `OpenAI`, or `Ollama Cloud`).
5. Select report style and click **2) Generate Report**.

## Data column summary

Common columns returned by Marketstack EOD data:

| Column Name | Type | Description |
|---|---|---|
| `date` | date string | Trading date for the record |
| `symbol` | string | Stock ticker symbol |
| `open` | numeric | Opening price |
| `high` | numeric | Highest price during the day |
| `low` | numeric | Lowest price during the day |
| `close` | numeric | Closing price |
| `volume` | numeric | Total traded volume |
| `exchange` | string/object | Exchange metadata (if provided by API) |

## Error handling included

- Missing API key
- Network/request failures
- Invalid or empty API responses
- Unsupported AI provider selections
- Missing AI provider keys (falls back to local summary)

## Homework 1 completion checklist

Use this app folder as your code deliverable, then complete the four required submission components in your `.docx`:

- [ ] **Writing Component (25 pts)**: 3+ paragraphs in your own words (not AI-generated).
- [ ] **Git Repository Links (25 pts)**: include links to:
  - `04_deployment/hw1/app.py`
  - `04_deployment/hw1/api_client.py`
  - `04_deployment/hw1/ai_reporter.py`
  - `04_deployment/hw1/README.md`
- [ ] **Screenshots/Outputs (25 pts)**: at least 3-4 images:
  - app UI with controls
  - successful data query table
  - AI-generated report
  - one error-handling example
- [ ] **Documentation (25 pts)**: this README provides:
  - data-column summary table
  - technical setup details
  - run/use instructions
