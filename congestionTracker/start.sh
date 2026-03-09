#!/usr/bin/env bash

set -e

export CONGESTION_API_BASE_URL="${CONGESTION_API_BASE_URL:-http://127.0.0.1:8000}"

# Start FastAPI in the background
uvicorn api_main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit (this will keep the container running)
streamlit run dashboard_app.py --server.port 8501 --server.address 0.0.0.0

