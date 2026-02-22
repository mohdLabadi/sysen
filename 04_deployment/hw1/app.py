"""
app.py
Homework 1 complete AI-powered reporter app (Shiny for Python).

This app combines:
1) Public API query (Marketstack EOD stock data)
2) Interactive web UI
3) AI-generated report summaries (OpenAI or Ollama Cloud)
"""

import pandas as pd
from shiny import App, reactive, render, ui

from ai_reporter import generate_ai_report
from api_client import query_marketstack_eod, summarize_market_data


# 1. UI #############################################

app_ui = ui.page_navbar(
    ui.nav_panel(
        "AI Reporter",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Query Controls"),
                ui.input_text("symbol", "Stock Symbol", value="AAPL", placeholder="e.g., AAPL, MSFT"),
                ui.input_numeric("limit_days", "Trading days", value=20, min=10, max=60, step=5),
                ui.input_switch("sort_desc", "Newest first", value=True),
                ui.input_action_button("run_query", "1) Run API Query", class_="btn-primary"),
                ui.hr(),
                ui.h4("AI Report Controls"),
                ui.input_select(
                    "provider",
                    "AI provider",
                    {
                        "none": "Local summary only (no AI key needed)",
                        "openai": "OpenAI",
                        "ollama_cloud": "Ollama Cloud",
                    },
                    selected="none",
                ),
                ui.input_select(
                    "style",
                    "Report style",
                    {
                        "brief_bullets": "Brief bullets",
                        "analyst_note": "Analyst paragraph",
                        "risk_focus": "Risk-focused bullets",
                    },
                    selected="brief_bullets",
                ),
                ui.input_action_button("run_report", "2) Generate Report", class_="btn-success"),
                ui.p(
                    "Tip: Start with local summary to verify your query. "
                    "Then switch to OpenAI or Ollama Cloud after setting API keys."
                ),
                bg="#f8f9fa",
            ),
            ui.card(
                ui.card_header("Query Status"),
                ui.output_text_verbatim("status_text"),
            ),
            ui.card(
                ui.card_header("Data Snapshot"),
                ui.output_text_verbatim("metrics_text"),
            ),
            ui.card(
                ui.card_header("End-of-Day Data"),
                ui.output_data_frame("results_table"),
            ),
            ui.card(
                ui.card_header("AI Reporter Output"),
                ui.output_text_verbatim("report_text"),
            ),
        ),
    ),
    title="HW1 AI-Powered Reporter",
)


# 2. Server #########################################

def server(input, output, session):
    """Connect UI events to API querying and AI report generation."""
    latest_data = reactive.Value(None)
    status_message = reactive.Value("Click 'Run API Query' to load data.")
    report_message = reactive.Value("Generate a report after loading data.")
    latest_summary = reactive.Value({})

    @reactive.effect
    @reactive.event(input.run_query)
    def _run_query():
        """Run API query when the user clicks the query button."""
        status_message.set("Contacting Marketstack...")
        report_message.set("Generate a report after loading data.")
        latest_data.set(None)
        latest_summary.set({})

        data, error = query_marketstack_eod(
            symbol=input.symbol(),
            limit=int(input.limit_days() or 20),
            sort_desc=bool(input.sort_desc()),
        )

        if error is not None:
            status_message.set(f"Error: {error}")
            return

        summary = summarize_market_data(data)
        latest_data.set(data)
        latest_summary.set(summary)
        status_message.set(f"Success: Retrieved {len(data)} rows for {input.symbol().strip().upper()}.")

    @reactive.effect
    @reactive.event(input.run_report)
    def _run_report():
        """Generate AI report from the latest query summary."""
        summary = latest_summary()
        if not summary:
            report_message.set("No data summary available. Run API query first.")
            return

        report, report_error = generate_ai_report(
            summary=summary,
            provider=input.provider(),
            style=input.style(),
        )
        if report_error:
            report_message.set(f"{report_error}\n\n{report}")
        else:
            report_message.set(report)

    @output
    @render.text
    def status_text():
        return status_message()

    @output
    @render.text
    def metrics_text():
        """Show a compact deterministic summary of the queried data."""
        summary = latest_summary()
        if not summary:
            return "No summary yet. Run an API query."

        direction = "up" if summary["pct_change"] >= 0 else "down"
        return (
            f"Rows: {summary['rows']}\n"
            f"Close range: {summary['min_close']:.2f} to {summary['max_close']:.2f}\n"
            f"Average close: {summary['mean_close']:.2f}\n"
            f"Period change: {summary['pct_change']:.2f}% ({direction})"
        )

    @output
    @render.data_frame
    def results_table():
        data = latest_data()
        if data is None:
            return pd.DataFrame({"info": ["No data loaded yet."]})
        return data

    @output
    @render.text
    def report_text():
        return report_message()


app = App(app_ui, server)
