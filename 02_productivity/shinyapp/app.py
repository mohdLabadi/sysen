"""
app.py
Interactive Shiny for Python app for querying Marketstack EOD data.
Pairs with 01_query_api/02_lab.py and LAB_cursor_shiny_app.md.

This app lets you:
- enter a stock ticker symbol (e.g., AAPL)
- choose how many recent trading days to request
- decide whether to sort newest-first or oldest-first
- run the query on demand with a button
- view results in an interactive data table

The app is intentionally simple and heavily commented so students can see
how to connect an API query to a Shiny user interface.
"""

# 0. Setup #################################

## 0.1 Load packages ############################

import pandas as pd
from shiny import App, reactive, render, ui

from api_client import query_marketstack_eod


# 1. UI definition #################################

## 1.1 Page layout ############################

# We use a navbar page with a single tab.
# This gives the app a modern, extensible structure: more panels can be
# added later without changing the basic pattern.
app_ui = ui.page_navbar(
    ui.nav_panel(
        "Market Data Explorer",
        ui.layout_sidebar(
            # Sidebar on the left with inputs
            ui.sidebar(
                ui.h4("Query settings"),
                ui.input_text(
                    "symbol",
                    "Stock symbol",
                    value="AAPL",
                    placeholder="e.g., AAPL, MSFT, TSLA",
                ),
                ui.input_numeric(
                    "limit_days",
                    "Number of recent trading days",
                    value=20,
                    min=5,
                    max=60,
                    step=5,
                ),
                ui.input_switch(
                    "sort_desc",
                    "Show most recent days first",
                    value=True,
                ),
                ui.input_action_button(
                    "run_query",
                    "Run API query",
                    class_="btn-primary",
                ),
                ui.p(
                    "Note: Data comes from the Marketstack End-of-Day (EOD) endpoint. "
                    "Trading days exclude weekends and some holidays."
                ),
                bg="#f8f9fa",
            ),
            # Main content area
            ui.card(
                ui.card_header("Simple momentum rating"),
                ui.output_text("rating_text"),
            ),
            ui.card(
                ui.card_header("End-of-Day results"),
                ui.output_text_verbatim("status_text"),
                ui.output_data_frame("results_table"),
            ),
        ),
    ),
    title="Shiny Marketstack EOD Explorer",
)


# 2. Server logic #################################

def server(input, output, session):
    """
    Server function connects UI inputs to the API query and outputs.

    The pattern here uses:
    - a reactive.Value to store the latest DataFrame
    - a reactive.Value to store the latest status / error message
    - an effect that runs only when the user clicks the button
    """

    ## 2.1 Reactive state ############################

    # Store the most recent DataFrame (or None on error)
    latest_df = reactive.Value(None)

    # Store a short status message for the user
    status_message = reactive.Value(
        "Enter a symbol and click 'Run API query' to load data."
    )

    ## 2.2 Query effect ##############################

    @reactive.effect
    @reactive.event(input.run_query)
    def _run_query_effect():
        """
        Run when the user clicks the 'Run API query' button.

        This function:
        - reads UI inputs
        - calls the API helper function
        - updates reactive values for data and status messages
        """
        symbol = input.symbol()
        limit_days = int(input.limit_days() or 20)
        sort_desc = bool(input.sort_desc())

        status_message.set("Contacting Marketstack API...")
        latest_df.set(None)

        df, error = query_marketstack_eod(
            symbol=symbol,
            limit=limit_days,
            sort_desc=sort_desc,
        )

        if error is not None:
            status_message.set(f"❗ {error}")
            latest_df.set(None)
        else:
            n_rows = len(df)
            status_message.set(
                f"✅ Retrieved {n_rows} rows for {symbol.strip().upper()} "
                f"(limit={limit_days})."
            )
            latest_df.set(df)

    ## 2.3 Output renderers ##########################

    @output
    @render.text
    def status_text():
        """
        Show the current status message (info or error).
        """
        return status_message()

    @output
    @render.text
    def rating_text():
        """
        Provide a very simple, educational narrative for an investor
        based on recent price momentum.

        This is NOT investment advice; it is only meant to demonstrate
        how to compute a summary metric from the last X days of data.
        """
        df = latest_df()
        if df is None or "close" not in df.columns:
            return (
                "No rating yet. Run a query to see a simple trend-based suggestion "
                "based on recent closing prices."
            )

        # Sort by date so we can compare the earliest and latest close prices.
        # The date column is in YY-MM-DD format, so string sorting still
        # preserves chronological order.
        df_sorted = df.sort_values("date")

        first_close = df_sorted["close"].iloc[0]
        last_close = df_sorted["close"].iloc[-1]

        if pd.isna(first_close) or pd.isna(last_close) or first_close == 0:
            return "Not enough clean closing price data to compute a rating."

        pct_change = (last_close - first_close) / first_close * 100
        n_days = len(df_sorted)

        # Very simple interpretation rules of thumb.
        if pct_change >= 5:
            tone = (
                "The stock has exhibited positive price momentum over this period, "
                "which may support a moderately bullish view for investors who are "
                "comfortable with short-term trend-following strategies."
            )
        elif pct_change <= -5:
            tone = (
                "The stock has experienced a meaningful drawdown over this period, "
                "which may justify a more cautious stance or a wait-and-see approach "
                "before committing new capital."
            )
        else:
            tone = (
                "The stock’s price has been relatively range-bound over this period, "
                "suggesting limited directional signal and a more neutral short-term outlook."
            )

        return (
            f"Over the last {n_days} trading days, the closing price moved from "
            f"{first_close:.2f} to {last_close:.2f}, a change of {pct_change:.1f}%. "
            f"{tone} This is a simple illustration using recent returns only and "
            f"does not incorporate fundamentals, valuation, or risk preferences."
        )

    @output
    @render.data_frame
    def results_table():
        """
        Render the most recent DataFrame as an interactive table.

        If no data is available yet, we return an empty DataFrame. This keeps
        the output stable and avoids errors when the page first loads.
        """
        df = latest_df()
        if df is None:
            # Return an empty DataFrame with a helpful placeholder column.
            return pd.DataFrame({"info": ["No data loaded yet."]})
        return df


# 3. App object #################################

app = App(app_ui, server)

