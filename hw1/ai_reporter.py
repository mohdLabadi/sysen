"""
ai_reporter.py
AI reporting helpers for Homework 1.

Supports:
- OpenAI Responses API
- Ollama Cloud chat API
"""

import json
import os
from typing import Dict, Optional, Tuple

import requests
from dotenv import load_dotenv


load_dotenv()


def _report_instructions(style: str) -> str:
    """Return style-specific instructions for the model."""
    instructions = {
        "brief_bullets": (
            "Return exactly 4 concise bullet points: trend, volatility, notable range, and risk note."
        ),
        "analyst_note": (
            "Write one short analyst-style paragraph (4-6 sentences) with a neutral tone."
        ),
        "risk_focus": (
            "Write 5 bullet points focused on downside risk, uncertainty, and what to monitor next."
        ),
    }
    return instructions.get(style, instructions["brief_bullets"])


def _build_prompt(summary: Dict[str, float], style: str) -> str:
    """Build a compact reporting prompt from summary metrics."""
    serialized_summary = json.dumps(summary, indent=2)
    return (
        "You are a financial data reporting assistant for a classroom project.\n"
        "You are not providing investment advice. Use only the provided metrics.\n\n"
        f"Metrics:\n{serialized_summary}\n\n"
        f"Instruction: {_report_instructions(style)}\n"
        "Keep wording clear for non-experts."
    )


def _fallback_report(summary: Dict[str, float]) -> str:
    """Return a deterministic non-AI summary if no model key is available."""
    if not summary:
        return "No summary is available yet. Run an API query first."

    trend = "upward" if summary.get("pct_change", 0) > 0 else "downward"
    return (
        f"Local summary only (AI disabled): Over {summary.get('rows', 0)} rows, close prices show an "
        f"{trend} move of {summary.get('pct_change', 0):.2f}%. "
        f"Range: {summary.get('min_close', 0):.2f} to {summary.get('max_close', 0):.2f}. "
        f"Average close: {summary.get('mean_close', 0):.2f}."
    )


def _generate_openai_report(prompt: str) -> Tuple[Optional[str], Optional[str]]:
    """Call OpenAI Responses API and return (report, error)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "OPENAI_API_KEY is missing from your environment."

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    url = "https://api.openai.com/v1/responses"
    body = {"model": model, "input": prompt}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as exc:
        return None, f"OpenAI request failed: {exc}"
    except ValueError:
        return None, "OpenAI returned invalid JSON."

    try:
        content = payload["output"][0]["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None, "OpenAI response format was unexpected."
    return content, None


def _generate_ollama_cloud_report(prompt: str) -> Tuple[Optional[str], Optional[str]]:
    """Call Ollama Cloud chat API and return (report, error)."""
    api_key = os.getenv("OLLAMA_API_KEY")
    if not api_key:
        return None, "OLLAMA_API_KEY is missing from your environment."

    model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b-cloud")
    url = "https://ollama.com/api/chat"
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as exc:
        return None, f"Ollama Cloud request failed: {exc}"
    except ValueError:
        return None, "Ollama Cloud returned invalid JSON."

    try:
        content = payload["message"]["content"]
    except (KeyError, TypeError):
        return None, "Ollama Cloud response format was unexpected."
    return content, None


def generate_ai_report(
    summary: Dict[str, float],
    provider: str,
    style: str,
) -> Tuple[str, Optional[str]]:
    """
    Generate a report from summary metrics.

    Returns:
      (report_text, error_message)
    """
    if not summary:
        return "No summary is available yet. Run an API query first.", None

    if provider == "none":
        return _fallback_report(summary), None

    prompt = _build_prompt(summary, style)
    if provider == "openai":
        report, error = _generate_openai_report(prompt)
    elif provider == "ollama_cloud":
        report, error = _generate_ollama_cloud_report(prompt)
    else:
        return _fallback_report(summary), f"Unknown provider '{provider}'. Used local summary instead."

    if error is not None:
        return _fallback_report(summary), f"{error} Local summary shown instead."

    return report or _fallback_report(summary), None
