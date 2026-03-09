https://congestion-tracker-hyx4z.ondigitalocean.app/

# City Congestion Tracker – Midterm Pipeline

This folder contains everything for your **midterm DL challenge pipeline**:

- Supabase PostgreSQL **database**
- FastAPI **REST API**
- Streamlit **dashboard**
- Ollama Cloud **AI model**

If you open only this README and follow it **top to bottom**, you can reproduce the full system and the midterm demo.

---

## 1. What this tool does

- Tracks congestion at synthetic city intersections every 5 minutes.
- Stores readings in a Supabase database.
- Serves the data through a FastAPI REST API.
- Shows a dashboard in Streamlit with:
  - Live congestion table
  - Time‑series plots
  - City map
  - AI summary of recent congestion
- Uses Ollama Cloud to turn numbers into **plain‑language routing advice** for emergency services and planners.

---

## 2. One‑time setup

Run everything from this folder.

```bash
cd 05_hackathon/congestionTracker
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your real keys:

```env
SUPABASE_URL="https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_SERVICE_KEY="YOUR_SERVICE_ROLE_KEY"

OLLAMA_CLOUD_API_KEY="YOUR_OLLAMA_CLOUD_API_KEY"
OLLAMA_CLOUD_MODEL="gpt-oss:120b"
```

Do **not** commit the real `.env` file.

### 2.1 Supabase schema

1. Open Supabase → SQL editor.
2. Paste and run the contents of `db/supabase_schema.sql`.

This creates the two tables used in the pipeline:

- `intersections`
- `congestion_readings`

See `CODEBOOK_congestion_tracker.md` for full column documentation.

### 2.2 Generate & load synthetic data (test datasets)

From this folder:

```bash
python backend/generate_synthetic_congestion.py   # writes data/intersections.csv + data/congestion_readings_raw.csv
python backend/load_congestion_readings.py        # loads data into Supabase
```

These two runs are your **main test datasets**:

1. `intersections.csv` – list of synthetic intersections with GPS and priority level.
2. `congestion_readings_raw.csv` – 5‑minute congestion readings for several days.

After running the loader, check in Supabase:

- `intersections` has about 20 rows.
- `congestion_readings` has many time‑series rows.

---

## 3. Run the full pipeline locally

### 3.1 Start the API (FastAPI)

```bash
uvicorn backend.api_main:app --reload
```

- API base URL: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`

This API:

- Reads from the Supabase database.
- Serves intersections and congestion readings.
- Exposes an `/ai/summary` endpoint that calls Ollama Cloud.

### 3.2 Start the dashboard (Streamlit)

Open a second terminal:

```bash
cd 05_hackathon/congestionTracker
export CONGESTION_API_BASE_URL="http://127.0.0.1:8000"
streamlit run frontend/dashboard_app.py
```

- Dashboard: `http://localhost:8501`

The dashboard calls the API only; it does **not** talk to Supabase directly.

You should see:

- Landing page explaining the problem and solution.
- Tabs:
  - **Live congestion (now)**
  - **Trends & time series**
  - **City map**
  - **Architecture & docs**
- An **AI summary** button in the trends tab.

---

## 4. How to demo (2–3 concrete test executions)

You can use these steps directly in your midterm demo.

### 4.1 Live congestion (now)

1. Go to the **Live congestion (now)** tab.
2. Set “Number of intersections to show” to **10**.
3. Explain:
   - The **max congestion level**.
   - The **average congestion** for the top 10.
   - What the table columns mean:
     - Intersection
     - Congestion (0–100)
     - Estimated speed (km/h)
     - Estimated delay (sec)

This is one clear **test execution** of the tool.

### 4.2 Trends & time series

1. Open **Trends & time series**.
2. Pick any intersection.
3. Set “Days back” to **3**.
4. Show the line chart and point out:
   - Morning and evening peaks.
   - How this helps schedule signal changes or plan patrol routes.

This is a second **test execution** using the time‑series pipeline.

### 4.3 AI summary of recent congestion

1. In the same tab, scroll to **AI summary for recent congestion**.
2. Set “Hours to summarize” to **6**.
3. Click **Generate AI summary**.
4. Read 1–2 sentences aloud that show:
   - Which intersections are most concerning.
   - A concrete routing suggestion for emergency services.

This is a third **test execution** that uses the AI part of the pipeline.

If you need precise definitions of all variables for your write‑up, see the codebook file.

---

## 5. System architecture (how all parts connect)

This project follows the required midterm pipeline:

1. **Database – Supabase (PostgreSQL)**
   - Tables: `intersections`, `congestion_readings`
   - Created with `db/supabase_schema.sql`
   - Populated by `backend/generate_synthetic_congestion.py` and `backend/load_congestion_readings.py`

2. **REST API – FastAPI (`backend/api_main.py`)**
   - Talks to Supabase using the REST interface.
   - Key endpoints:
     - `GET /intersections`
     - `GET /congestion/top_current`
     - `GET /congestion/timeseries`
     - `POST /ai/summary` (calls Ollama Cloud)

3. **Dashboard – Streamlit (`frontend/dashboard_app.py`)**
   - Calls the API at `CONGESTION_API_BASE_URL`.
   - Shows:
     - Live congestion table
     - Time‑series charts per intersection
     - City‑level map
     - AI summary section

4. **AI model – Ollama Cloud**
   - Configured with `OLLAMA_CLOUD_API_KEY` and `OLLAMA_CLOUD_MODEL`.
   - Input: aggregated congestion stats from the database.
   - Output: short, concrete text summary for dispatchers.

High‑level data flow:

```text
Synthetic generator  →  Supabase  →  FastAPI API  →  Streamlit dashboard  →  Ollama Cloud
 (Python scripts)       (database)    (/api routes)   (UI tabs)               (AI summary)
```

---

## 6. Deployment (Docker + DigitalOcean)

### 6.1 Local Docker test

From this folder:

```bash
docker build -t city-congestion-tracker .
docker run --env-file .env -p 8000:8000 -p 8501:8501 city-congestion-tracker
```

Then open:

- `http://localhost:8000/docs` (API)
- `http://localhost:8501` (dashboard)

### 6.2 DigitalOcean App Platform

1. Push this folder to a **public GitHub repo**.
2. Create a new DigitalOcean App from that repo.
3. Set the app’s working directory to `05_hackathon/congestionTracker`.
4. Add environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `OLLAMA_CLOUD_API_KEY`
   - `OLLAMA_CLOUD_MODEL` (optional, default `gpt-oss:120b`)
5. Expose:
   - Port **8501** publicly for the dashboard.
   - Port **8000** if you also want public API docs.

Deployed dashboard URL for grading (Streamlit):

- `https://congestion-tracker-hyx4z.ondigitalocean.app/`

---

## 7. Files in this folder (quick map)

- `README.md` – this file; start here.
- `docs/CODEBOOK_congestion_tracker.md` – explains all data files, tables, and variables.
- `db/supabase_schema.sql` – creates the Supabase tables and indexes.
- `backend/generate_synthetic_congestion.py` – writes `data/intersections.csv` and `data/congestion_readings_raw.csv`.
- `backend/load_congestion_readings.py` – loads the synthetic data into Supabase.
- `backend/api_main.py` – FastAPI REST API over the Supabase database and AI summary.
- `frontend/dashboard_app.py` – Streamlit dashboard that calls the API.
- `requirements.txt` – Python dependencies for the whole pipeline.
- `Dockerfile` – container image for API + dashboard.
- `.env.example` – template for required environment variables.
- `start.sh` – helper script used for container startup.

With this README, a grader can:

1. Understand the system at a glance.
2. Reproduce the database, API, dashboard, and AI pipeline.
3. Run at least 2–3 clear test executions.
4. Reach the deployed app from the link at the top.

