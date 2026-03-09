import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = os.environ.get("CONGESTION_API_BASE_URL", "http://127.0.0.1:8000")


def fetch_json(path: str, params: Optional[dict] = None) -> dict:
    url = f"{API_BASE_URL}{path}"
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> None:
    st.set_page_config(page_title="City Congestion Tracker", layout="wide")

    # Lightweight custom theming
    st.markdown(
        """
<style>
/* Keep base colors from the active Streamlit theme so text always contrasts.
   Only style specific components and anchors. */

.hero-card {
  background: radial-gradient(circle at top left, #1d4ed8, #020617);
  border-radius: 18px;
  padding: 20px 26px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.9);
  color: #f9fafb;
}

.hero-title {
  font-size: 1.9rem;
  font-weight: 700;
  margin-bottom: 0.3rem;
}

.hero-subtitle {
  font-size: 0.95rem;
  opacity: 0.98;
}

.hero-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.95);
  font-size: 0.75rem;
  color: #f9fafb;
}

.hero-metric {
  font-size: 0.85rem;
}

.severity-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 999px;
  margin-right: 4px;
}

.severity-low   { background-color: #22c55e; }
.severity-med   { background-color: #eab308; }
.severity-high  { background-color: #ef4444; }

.legend-text {
  font-size: 0.80rem;
}

/* Anchor offset so headings are not hidden under Streamlit's top bar */
.section-anchor {
  position: relative;
  top: -80px;   /* adjust if Streamlit header height changes */
  visibility: hidden;
}
</style>
        """,
        unsafe_allow_html=True,
    )

    # Layout: left vertical navigation, right main content
    nav_col, main_col = st.columns([1, 3])

    with nav_col:
        st.markdown("### Navigate")
        st.markdown(
            "- [Hero](#hero)\n"
            "- [Problem](#problem)\n"
            "- [Solution](#solution)\n"
            "- [How it works](#how-it-works)\n"
            "- [Benefits](#benefits)\n"
            "- [Live dashboard](#live-demo)\n"
        )

    with main_col:
        # Hero section
        st.markdown('<div id="hero" class="section-anchor"></div>', unsafe_allow_html=True)
        st.markdown(
            """
<div class="hero-card">
  <div class="hero-pill">
    <span>🚑 City operations · Midterm DL pipeline</span>
  </div>
  <div style="margin-top: 0.4rem;">
    <div class="hero-title">City Congestion Tracker</div>
    <div class="hero-subtitle">
      A live intersection‑level view of city traffic, powered by Supabase, FastAPI, Streamlit, and an Ollama Cloud model
      that speaks like an emergency‑dispatch assistant.
    </div>
  </div>
  <div style="display: flex; flex-wrap: wrap; gap: 1.5rem; margin-top: 1rem;">
    <div class="hero-metric">
      <strong>Intersection</strong> = a road junction with a name, GPS point, and priority (e.g., hospital route).
    </div>
    <div class="hero-metric">
      <strong>Congestion (0–100)</strong> every 5 minutes: 0 = free flow, 40–60 = moderate, 80–100 = severe.
    </div>
    <div class="hero-metric">
      <strong>AI summary</strong> turns numbers into concrete routing advice for emergency vehicles.
    </div>
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )

    # Problem + solution + how-it-works + benefits sections
        st.markdown('<div id="problem" class="section-anchor"></div>', unsafe_allow_html=True)
        st.markdown("## The problem")
        st.write(
            "- Dispatchers can’t see **which intersections are failing right now** in one place.\n"
            "- Routing decisions rely on experience and radio chatter, not real‑time data.\n"
            "- Raw numbers don’t translate into **plain‑language routing advice**."
        )

        st.markdown('<div id="solution" class="section-anchor"></div>', unsafe_allow_html=True)
        st.markdown("## Our solution")
        st.write(
            "- A live intersection‑level dashboard with **5‑minute congestion scores**.\n"
            "- Time‑series views for spotting recurring trouble spots.\n"
            "- An AI assistant that **speaks like a dispatcher**, recommending safer routes."
        )

        st.markdown('<div id="how-it-works" class="section-anchor"></div>', unsafe_allow_html=True)
        st.markdown("## How it works (3 steps)")
        step1, step2, step3 = st.columns(3)
        with step1:
            st.markdown("**1. Store**")
            st.write("Supabase stores congestion readings for each intersection every 5 minutes.")
        with step2:
            st.markdown("**2. Serve & Explore**")
            st.write("FastAPI exposes a REST API, and the dashboard shows live tables, charts, and a city map.")
        with step3:
            st.markdown("**3. Summarize**")
            st.write("Ollama Cloud turns aggregated stats into **plain‑language routing suggestions**.")

        st.markdown(
            "```text\n"
            "Sensors / Synthetic → Supabase DB → FastAPI API → Dashboard → AI Summary\n"
            "```"
        )

        st.markdown('<div id="benefits" class="section-anchor"></div>', unsafe_allow_html=True)
        st.markdown("## Who benefits?")
        b_left, b_right = st.columns(2)
        with b_left:
            st.markdown("**Emergency services**")
            st.write(
                "- See worst intersections instantly.\n"
                "- Avoid gridlocked routes for ambulances and fire trucks.\n"
                "- Get a concise AI summary before making routing calls."
            )
        with b_right:
            st.markdown("**City planners & ops**")
            st.write(
                "- Spot consistently overloaded intersections.\n"
                "- Compare short‑term spikes vs. typical patterns.\n"
                "- Use the API for further analysis or reporting."
            )

        st.markdown('<div id="live-demo" class="section-anchor"></div>', unsafe_allow_html=True)
        st.markdown("## Live congestion dashboard")
        st.write("Use the tabs below to explore live congestion, trends, the city map, and AI insights.")

    with st.sidebar:
        st.header("App settings")
        st.markdown("**API base URL**")
        st.code(API_BASE_URL, language="text")
        st.markdown("1. Start FastAPI.\n2. Start Streamlit.\n3. Use the tabs to explore the pipeline.")

    # Load intersections once
    try:
        intersections = fetch_json("/intersections")
    except Exception as exc:
        st.error(f"Error loading intersections from API: {exc}")
        return

    if not intersections:
        st.warning("No intersections found. Check that your database is populated.")
        return

    intersections_df = pd.DataFrame(intersections)

    tab_now, tab_trends, tab_map, tab_arch = st.tabs(
        ["Live congestion (now)", "Trends & time series", "City map", "Architecture & docs"]
    )

    with tab_now:
        st.subheader("Most congested intersections right now")
        st.markdown(
            "This view shows the intersections with the **highest congestion level** "
            "in the latest 5‑minute time bucket."
        )

        st.markdown(
            """
<span class="legend-text">
  <span class="severity-dot severity-low"></span>0–39 low &nbsp;&nbsp;
  <span class="severity-dot severity-med"></span>40–69 medium &nbsp;&nbsp;
  <span class="severity-dot severity-high"></span>70–100 high
</span>
            """,
            unsafe_allow_html=True,
        )

        limit = st.slider("Number of intersections to show", min_value=5, max_value=20, value=10)

        try:
            top_now = fetch_json("/congestion/top_current", params={"limit": limit})
        except Exception as exc:
            st.error(f"Error loading current congestion: {exc}")
            top_now = []

        if top_now:
            top_df = pd.DataFrame(top_now)

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric(
                    "Max congestion level",
                    f"{top_df['congestion_level'].max():.0f}",
                )
            with col_b:
                st.metric(
                    "Avg congestion (top N)",
                    f"{top_df['congestion_level'].mean():.1f}",
                )
            with col_c:
                st.metric("Intersections shown", f"{len(top_df)}")

            st.dataframe(
                top_df[
                    [
                        "intersection_name",
                        "congestion_level",
                        "speed_kmh",
                        "delay_sec",
                    ]
                ].rename(
                    columns={
                        "intersection_name": "Intersection",
                        "congestion_level": "Congestion (0–100)",
                        "speed_kmh": "Estimated speed (km/h)",
                        "delay_sec": "Estimated delay (sec)",
                    }
                ),
                use_container_width=True,
            )
        else:
            st.info("No congestion readings found for the latest 5‑minute interval.")

    with tab_trends:
        st.subheader("Time series for a single intersection")
        st.markdown(
            "Select an intersection to explore how congestion changes over time, "
            "then optionally generate an **AI summary** for the recent period."
        )

        intersection_name = st.selectbox(
            "Choose intersection",
            options=intersections_df["name"],
        )

        selected_row = intersections_df[intersections_df["name"] == intersection_name].iloc[0]
        intersection_id = selected_row["id"]

        col1, col2 = st.columns(2)
        with col1:
            days_back = st.slider("Days back", min_value=1, max_value=7, value=1)
        with col2:
            now = datetime.now(timezone.utc)
            end = now
            start = now - timedelta(days=days_back)
            st.write(f"Showing last {days_back} day(s)")

        params = {
            "intersection_id": intersection_id,
            "start": start.isoformat(),
            "end": end.isoformat(),
        }

        try:
            series = fetch_json("/congestion/timeseries", params=params)
        except Exception as exc:
            st.error(f"Error loading time series: {exc}")
            series = []

        if series:
            series_df = pd.DataFrame(series)
            series_df["timestamp_utc"] = pd.to_datetime(series_df["timestamp_utc"])
            series_df = series_df.set_index("timestamp_utc").sort_index()

            st.line_chart(series_df[["congestion_level"]])
            st.write("Congestion level over time (higher = more congested).")
        else:
            st.info("No time series data returned for this selection.")

        st.markdown("---")
        st.subheader("AI summary for recent congestion")

        hours = st.slider("Hours to summarize", min_value=1, max_value=24, value=6)

        if st.button("Generate AI summary"):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/ai/summary",
                    json={"hours": hours},
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                st.markdown(f"**Time window:** last {data['hours']} hour(s)")
                st.markdown(f"**Generated at (UTC):** {data['generated_at_utc']}")
                st.markdown("#### AI summary")
                st.write(data["summary"])
            except Exception as exc:
                st.error(f"Error generating AI summary: {exc}")

    with tab_map:
        st.subheader("City map (synthetic layout)")
        st.markdown(
            "This map shows the **synthetic locations** of intersections in the city, "
            "with points sized by current congestion level."
        )

        try:
            snapshot = fetch_json("/congestion/top_current", params={"limit": len(intersections_df)})
        except Exception as exc:
            st.error(f"Error loading snapshot for map: {exc}")
            snapshot = []

        if snapshot:
            snap_df = pd.DataFrame(snapshot)
            merged = intersections_df.merge(
                snap_df[["intersection_id", "congestion_level"]],
                left_on="id",
                right_on="intersection_id",
                how="left",
            )
            merged["congestion_level"] = merged["congestion_level"].fillna(0)
        else:
            merged = intersections_df.copy()
            merged["congestion_level"] = 0

        map_df = merged.rename(columns={"lat": "latitude", "lon": "longitude"})
        st.map(map_df[["latitude", "longitude"]])

        st.write(
            "Points are centered around a synthetic downtown area (lat/lon). "
            "In a real deployment, these would match true intersection coordinates."
        )

        st.dataframe(
            merged[["name", "priority_level", "congestion_level"]].rename(
                columns={
                    "name": "Intersection",
                    "priority_level": "Priority level",
                    "congestion_level": "Current congestion (0–100, synthetic)",
                }
            ),
            use_container_width=True,
        )

    with tab_arch:
        st.subheader("System architecture")
        st.markdown(
            "This dashboard is part of a full midterm pipeline:\n\n"
            "- **Supabase (PostgreSQL)** stores synthetic congestion readings.\n"
            "- **FastAPI** exposes a REST API over the database.\n"
            "- **Streamlit** (this app) calls the API to show tables and charts.\n"
            "- **Ollama Cloud** generates natural‑language summaries from aggregated stats.\n"
        )

        st.markdown(
            "### Data flow\n\n"
            "```text\n"
            "Synthetic generator  →  Supabase  →  FastAPI  →  Streamlit  →  Ollama Cloud\n"
            " (Python script)        (DB)         (/api)       (UI)          (AI model)\n"
            "```\n"
        )

        st.markdown(
            "### How to use\n\n"
            "1. Open the **Live congestion (now)** tab to see the worst intersections.\n"
            "2. Switch to **Trends & time series** to inspect a specific intersection.\n"
            "3. Use **AI summary for recent congestion** to get routing suggestions for dispatch.\n"
        )


if __name__ == "__main__":
    main()

