# City Congestion Tracker – Midterm DL Challenge

An end-to-end congestion tracking system for a city transportation authority.  
The pipeline is:

**Supabase (PostgreSQL) → FastAPI REST API → Streamlit dashboard → Ollama Cloud AI.**

---

## 1. Use case

- **User**: Emergency services / dispatchers and transportation operators.
- **Goal**: See where congestion is building by intersection and time, and get **plain‑language routing guidance**.
- **Data**: Synthetic congestion readings every 5 minutes for ~20 intersections over the last 7 days.

Example questions the tool answers:

- Which intersections are currently most congested?
- How did congestion evolve at a specific intersection over the last few days?
- Is congestion in the last N hours better, worse, or similar to typical patterns?
- What routes should emergency vehicles avoid or prefer right now?

---

## 2. Architecture overview

High‑level pipeline:

```text
Synthetic generator (Python)
        │
        ▼
Supabase PostgreSQL ──▶ FastAPI REST API ──▶ Streamlit dashboard ──▶ Ollama Cloud (gpt-oss:120b)
        ▲                      ▲                       │
        └──── load script ─────┘                       └── user interacts in browser
```

- **Supabase**
  - `intersections`: metadata (name, lat/lon, priority level such as hospital route).
  - `congestion_readings`: 5‑minute congestion levels per intersection, with simple speed/delay estimates.
- **FastAPI (`api_main.py`)**
  - `GET /intersections`
  - `GET /congestion/top_current`
  - `GET /congestion/timeseries`
  - `GET /congestion/summary`
  - `POST /ai/summary` → aggregates recent congestion, calls **Ollama Cloud** for a short narrative.
- **Streamlit dashboard (`dashboard_app.py`)**
  - Live “top congested intersections now” table.
  - Per‑intersection time series plot.
  - “Generate AI summary” panel with narrative recommendations.

---

## 3. Project layout (key files)

- `generate_synthetic_congestion.py` – creates:
  - `intersections.csv`
  - `congestion_readings_raw.csv`
- `load_congestion_readings.py` – loads the synthetic readings into Supabase.
- `api_main.py` – FastAPI application exposing the REST API and AI summary.
- `dashboard_app.py` – Streamlit dashboard UI.
- `env_utils.py` – loads `.env` for Supabase and Ollama settings.
- `.env.example` – template for environment variables.
- `requirements.txt` – Python dependencies for this project.
- `Dockerfile` / `start.sh` – container entrypoint for DigitalOcean deployment.

---

## 4. Environment configuration

Create a `.env` file in the `congestionTracker` folder (next to `api_main.py`) by copying `.env.example`:

```bash
cp .env.example .env
```

Then edit `.env` with your real values:

```env
SUPABASE_URL="https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_SERVICE_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY"

OLLAMA_CLOUD_API_KEY="YOUR_OLLAMA_CLOUD_API_KEY"
OLLAMA_CLOUD_MODEL="gpt-oss:120b"
```

> **Note**: Do **not** commit the real `.env` file. Only commit `.env.example`.

---

## 5. Local setup and running

From the `05_hackathon/congestionTracker` directory:

```bash
pip install -r requirements.txt
```

### 5.1 Populate Supabase with synthetic data (one‑time)

1. Run the generator:

```bash
python generate_synthetic_congestion.py
```

2. Import `intersections.csv` into the `intersections` table using the Supabase UI.
3. Run the loader to send all readings into `congestion_readings`:

```bash
python load_congestion_readings.py
```

Verify in Supabase that both tables contain data.

### 5.2 Start the API

```bash
uvicorn api_main:app --reload
```

- API docs: `http://127.0.0.1:8000/docs`

### 5.3 Start the Streamlit dashboard

In a second terminal:

```bash
export CONGESTION_API_BASE_URL="http://127.0.0.1:8000"
streamlit run dashboard_app.py
```

- Dashboard: typically at `http://localhost:8501`

---

## 6. Example test scenarios

These can be used in your midterm report as “test executions”.

- **Scenario 1 – Live operations**
  - Open the dashboard live tab.
  - Set “Number of intersections to show” to 10.
  - Observe the list of worst intersections (by congestion level) and confirm they match `GET /congestion/top_current`.

- **Scenario 2 – Intersection time series**
  - Select an intersection in the “Trends & time series” tab.
  - Set “Days back” to 3.
  - Confirm that the line chart shows morning and evening peaks as generated in the synthetic data.

- **Scenario 3 – AI summary**
  - In the same tab, set “Hours to summarize” to 6.
  - Click **Generate AI summary**.
  - Confirm the text clearly:
    - Names top congested intersections.
    - Comments on overall severity.
    - Provides 2–3 routing recommendations.

---

## 7. DigitalOcean deployment (Docker)

This project is containerized so it can be deployed to **DigitalOcean App Platform** or a **Droplet**.

### 7.1 Build and run locally with Docker

From `05_hackathon/congestionTracker`:

```bash
docker build -t city-congestion-tracker .

docker run --env-file .env -p 8000:8000 -p 8501:8501 city-congestion-tracker
```

Then:

- API docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:8501`

### 7.2 Deploy to DigitalOcean App Platform

1. Push your code to a public GitHub repository (include `Dockerfile`, `requirements.txt`, `.env.example`).
2. In DigitalOcean:
   - Create a **new App** from the GitHub repo.
   - Select the `05_hackathon/congestionTracker` directory as the App’s root if prompted.
   - The App will detect the Dockerfile automatically.
3. Configure environment variables in the DO App settings:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `OLLAMA_CLOUD_API_KEY`
   - `OLLAMA_CLOUD_MODEL` (optional override, default `gpt-oss:120b`)
4. Expose ports:
   - **Service port 8000** (FastAPI) – for the API.
   - **Service port 8501** (Streamlit) – for the dashboard used in the browser.

You can either:

- Create **two services** (one for the API endpoint, one for the dashboard), or
- Expose only the dashboard externally and keep the API internal if DO networking is configured that way.

> For grading, it is sufficient to provide a **public dashboard URL** and a brief note in the README that the dashboard internally calls the FastAPI service.

---

## 8. Reproducibility notes

- All synthetic data is generated from a fixed random seed in `generate_synthetic_congestion.py`.
- Supabase schema is created via the SQL commands described in `MIDTERM_DL_challenge.md`.
- The entire pipeline can be reproduced by:
  1. Creating a new Supabase project.
  2. Running the SQL schema.
  3. Running the generator and loader.
  4. Running `uvicorn` and `streamlit` as shown above.

