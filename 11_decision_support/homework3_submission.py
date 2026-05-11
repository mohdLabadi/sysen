# homework3_submission.py
# HOMEWORK 3 submission: AI Report Validation System for Brussels Traffic Reports
# Pairs with HOMEWORK3.md and homework3_submission.md
# Mohammad Labadi (course: dsai)

# This script runs a self-contained experiment:
#   1. Builds a benchmark of expected Brussels vehicle counts per (day_of_week,
#      hour_of_day) from traffic.db (empirical means; no model required).
#   2. Generates traffic-narrative reports using THREE different prompt designs
#      (A=Minimal, B=Structured, C=Reasoning+Role) over N stimulus rows each.
#   3. Validates every report with a CUSTOM five-criterion rubric (mix of
#      deterministic and AI-judged scores) tailored to the traffic use case.
#   4. Runs Bartlett's test, one-way ANOVA, pairwise t-tests with Bonferroni
#      correction, and an OLS regression on the composite score.
#   5. Saves CSVs, a boxplot PNG, and a stats summary text file.
#
# Usage:
#   11_decision_support/.venv/bin/python 11_decision_support/homework3_submission.py
#   11_decision_support/.venv/bin/python 11_decision_support/homework3_submission.py --quick   # smoke test (N=3)

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pingouin as pg
import requests
import statsmodels.formula.api as smf
from dotenv import load_dotenv
from scipy.stats import bartlett

## 0.2 Configuration #################################

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# Ollama Cloud (project default) → fall back to local Ollama if no API key.
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://ollama.com" if OLLAMA_API_KEY else "http://127.0.0.1:11434")
GENERATOR_MODEL = os.getenv("HW3_GENERATOR_MODEL", "gpt-oss:20b" if OLLAMA_API_KEY else "smollm2:1.7b")
VALIDATOR_MODEL = os.getenv("HW3_VALIDATOR_MODEL", "gpt-oss:120b" if OLLAMA_API_KEY else "smollm2:1.7b")

# Paths
DB_PATH = ROOT / "12_end" / "data" / "traffic.db"
OUT_DIR = ROOT / "11_decision_support" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_CSV = OUT_DIR / "homework3_reports.csv"
SCORES_CSV = OUT_DIR / "homework3_scores.csv"
STATS_TXT = OUT_DIR / "homework3_stats.txt"
PLOT_PNG = OUT_DIR / "homework3_boxplot.png"

DAY_NAMES = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
             5: "Friday", 6: "Saturday", 7: "Sunday"}

## 0.3 CLI #################################

parser = argparse.ArgumentParser(description="Homework 3: AI Report Validation Experiment")
parser.add_argument("--quick", action="store_true", help="Smoke test: N=3 reports per prompt")
parser.add_argument("--n", type=int, default=20, help="Reports per prompt (default 20)")
parser.add_argument("--seed", type=int, default=42, help="Random seed for stimulus selection")
args = parser.parse_args()

N_PER_PROMPT = 3 if args.quick else args.n
RNG = np.random.default_rng(args.seed)

print("=" * 72)
print("📋 HOMEWORK 3 | AI Report Validation System (Brussels Traffic)")
print("=" * 72)
print(f"   ☁️  generator model: {GENERATOR_MODEL}")
print(f"   ☁️  validator model: {VALIDATOR_MODEL}")
print(f"   📁 db: {DB_PATH}")
print(f"   📁 out: {OUT_DIR}")
print(f"   🎲 reports per prompt: {N_PER_PROMPT}  (3 prompts → {N_PER_PROMPT * 3} total)")
print()

# 1. BENCHMARK: EMPIRICAL VEHICLE COUNTS ###################################

# Ground truth = empirical mean vehicles per (day_of_week, hour_of_day) for
# Brussels (metro_id 948). Used by the validator to score numerical_grounding.

print("-" * 72)
print("Step 1 — Build empirical benchmark from traffic.db")
print("-" * 72)

with sqlite3.connect(str(DB_PATH)) as conn:
    raw = pd.read_sql(
        "SELECT observed_at, vehicles FROM traffic WHERE metro_id = ? ORDER BY observed_at",
        conn, params=(948,),
    )

raw["observed_at"] = pd.to_datetime(raw["observed_at"], utc=True)
raw["day_of_week"] = raw["observed_at"].dt.dayofweek + 1  # 1=Mon ... 7=Sun
raw["hour_of_day"] = raw["observed_at"].dt.hour

benchmark = (raw
             .groupby(["day_of_week", "hour_of_day"], as_index=False)
             .agg(expected_vehicles=("vehicles", "mean"),
                  std_vehicles=("vehicles", "std"),
                  n_obs=("vehicles", "size")))
benchmark["expected_vehicles"] = benchmark["expected_vehicles"].round(1)
benchmark["std_vehicles"] = benchmark["std_vehicles"].fillna(benchmark["expected_vehicles"] * 0.2).round(1)

print(f"   ✅ Loaded {len(raw):,} rows → {len(benchmark)} (day, hour) cells")
print(f"   📊 expected_vehicles range: {benchmark['expected_vehicles'].min():.1f} – {benchmark['expected_vehicles'].max():.1f}")
print()

def lookup_expected(day: int, hour: int) -> float:
    """Return expected vehicle count for a (day, hour). Falls back to overall mean."""
    row = benchmark.query("day_of_week == @day and hour_of_day == @hour")
    if len(row):
        return float(row["expected_vehicles"].iloc[0])
    return float(benchmark["expected_vehicles"].mean())

# 2. STIMULUS ROWS ###################################

# A "stimulus" = one (day, hour) the agent should write a report about. We
# sample N distinct combinations uniformly at random for reproducibility.

all_combos = [(d, h) for d in range(1, 8) for h in range(24)]
chosen_idx = RNG.choice(len(all_combos), size=N_PER_PROMPT, replace=False)
stimuli = [all_combos[i] for i in chosen_idx]

print("-" * 72)
print(f"Step 2 — Sample {N_PER_PROMPT} stimulus (day, hour) pairs")
print("-" * 72)
for d, h in stimuli[:5]:
    print(f"   🕒 {DAY_NAMES[d]:9s} {h:02d}:00  → expected ≈ {lookup_expected(d, h):.1f} vehicles/min")
if N_PER_PROMPT > 5:
    print(f"   ... and {N_PER_PROMPT - 5} more")
print()

# 3. PROMPT VARIANTS ###################################

# Each prompt receives the same source facts (predicted vehicle count + unit)
# but differs in HOW it instructs the model to write the report. The validator
# never sees the prompt — it only sees the report and the ground-truth value.

def stimulus_facts(day: int, hour: int) -> dict[str, Any]:
    return {
        "day_name": DAY_NAMES[day],
        "day_of_week": day,
        "hour_of_day": hour,
        "expected_vehicles": round(lookup_expected(day, hour), 1),
        "unit": "vehicles per minute (1m/t1 sampling interval)",
    }

def prompt_a_minimal(facts: dict) -> str:
    return (
        f"Write a short report about Brussels vehicle traffic for "
        f"{facts['day_name']} at {facts['hour_of_day']:02d}:00. "
        f"Predicted count: {facts['expected_vehicles']} vehicles per minute."
    )

def prompt_b_structured(facts: dict) -> str:
    return (
        "You are a traffic analyst. Write a 3-section report using EXACTLY these "
        "section headers on their own line: SUMMARY, NUMBERS, RECOMMENDATION.\n\n"
        "Rules:\n"
        f"- The day is {facts['day_name']} (day_of_week={facts['day_of_week']}).\n"
        f"- The hour is {facts['hour_of_day']:02d}:00.\n"
        f"- The predicted vehicle count is {facts['expected_vehicles']} {facts['unit']}.\n"
        "- Mention the predicted count exactly once with the unit.\n"
        "- Keep the whole report under 120 words.\n"
        "- Do NOT invent additional statistics."
    )

def prompt_c_reasoning(facts: dict) -> str:
    return (
        "ROLE: Senior Brussels mobility planner briefing the city operations desk.\n\n"
        "TASK: Produce a decision-grade traffic note for one specific hour.\n\n"
        "REASONING STEPS (think silently, then write the final note):\n"
        "  1. Restate day-of-week and hour explicitly.\n"
        "  2. Restate the predicted vehicle count and its unit.\n"
        "  3. Compare informally to typical commuter peaks (07:00-09:00, 17:00-19:00).\n"
        "  4. Recommend ONE concrete action (signal timing, lane reallocation, "
        "messaging) tied to the predicted count.\n\n"
        "GROUNDED FACTS YOU MUST USE VERBATIM:\n"
        f"  - day: {facts['day_name']} (day_of_week={facts['day_of_week']})\n"
        f"  - hour: {facts['hour_of_day']:02d}:00\n"
        f"  - predicted vehicles: {facts['expected_vehicles']} {facts['unit']}\n\n"
        "HARD RULES:\n"
        "  - Never invent numbers not given above.\n"
        "  - State the unit at least once.\n"
        "  - Total length: 80-150 words. No bullet points in the final note."
    )

PROMPT_BUILDERS = {"A": prompt_a_minimal, "B": prompt_b_structured, "C": prompt_c_reasoning}

# 4. OLLAMA CLIENT ###################################

REQ_TIMEOUT_S = int(os.getenv("HW3_HTTP_TIMEOUT", "60"))
REQ_RETRIES = int(os.getenv("HW3_HTTP_RETRIES", "1"))

def ollama_chat(prompt: str, model: str, temperature: float = 0.7,
                json_mode: bool = False, retries: int = REQ_RETRIES) -> str:
    """Single-turn Ollama /api/chat call. Returns assistant text.

    Bounded wall-clock per call: (retries + 1) * REQ_TIMEOUT_S seconds. Override
    with env vars HW3_HTTP_TIMEOUT and HW3_HTTP_RETRIES if needed.
    """
    url = f"{OLLAMA_HOST.rstrip('/')}/api/chat"
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
    body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": temperature},
    }
    if json_mode:
        body["format"] = "json"

    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, headers=headers, json=body, timeout=REQ_TIMEOUT_S)
            r.raise_for_status()
            return r.json()["message"]["content"]
        except Exception as e:
            last_err = e
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"Ollama request failed after {retries + 1} attempts: {last_err}")

# 5. GENERATE REPORTS ###################################

print("-" * 72)
print("Step 3 — Generate reports for all (prompt × stimulus) combinations")
print("-" * 72)

report_rows: list[dict[str, Any]] = []
total = len(stimuli) * len(PROMPT_BUILDERS)
i = 0
run_start = time.monotonic()
for prompt_id, builder in PROMPT_BUILDERS.items():
    for day, hour in stimuli:
        i += 1
        facts = stimulus_facts(day, hour)
        prompt_text = builder(facts)
        call_start = time.monotonic()
        try:
            report_text = ollama_chat(prompt_text, model=GENERATOR_MODEL, temperature=0.7)
        except Exception as e:
            report_text = f"[generator_error: {e}]"
        call_s = time.monotonic() - call_start
        report_rows.append({
            "prompt_id": prompt_id,
            "day_of_week": day,
            "hour_of_day": hour,
            "expected_vehicles": facts["expected_vehicles"],
            "report_text": report_text,
        })
        # Incremental save — if the run is cut, partial progress is preserved.
        pd.DataFrame(report_rows).assign(
            word_count=lambda d: d["report_text"].str.split().str.len()
        ).to_csv(REPORTS_CSV, index=False)
        preview = report_text.replace("\n", " ")[:80]
        elapsed = time.monotonic() - run_start
        print(f"   ✏️  [{i:3d}/{total}] {prompt_id} · {DAY_NAMES[day][:3]} {hour:02d}:00 "
              f"({call_s:5.1f}s · elapsed {elapsed:6.1f}s) → {preview}...")

reports_df = pd.DataFrame(report_rows)
reports_df["word_count"] = reports_df["report_text"].str.split().str.len()
reports_df.to_csv(REPORTS_CSV, index=False)
print(f"   💾 saved {len(reports_df)} reports → {REPORTS_CSV}")
print()

# 6. VALIDATOR ###################################

# Custom 5-criterion rubric (NOT the LAB's six 1-5 Likert scales):
#   1. numerical_grounding  (0-1 continuous, deterministic)
#   2. unit_specification   (0/1 binary, deterministic)
#   3. temporal_specificity (0-3 ordinal, deterministic)
#   4. decision_actionability (1-7 Likert, AI-judged)
#   5. hallucination_risk   (0-1 probability, AI-judged)
# composite = weighted sum on a 0-1 scale.

NUMBER_RE = re.compile(r"\b\d{1,4}(?:[.,]\d+)?\b")
UNIT_PATTERNS = [
    r"vehicles?\s+per\s+minute", r"per[- ]?minute", r"vehicles?/min",
    r"1m\s*/?\s*t1", r"per\s+minute\s+interval",
]
UNIT_RE = re.compile("|".join(UNIT_PATTERNS), re.IGNORECASE)

def numerical_grounding(text: str, expected: float, tol: float = 0.05) -> float:
    """
    Fraction of numeric tokens in `text` that fall within ±tol of `expected`.
    Returns 0 if no numbers, 1 if all numbers are grounded. Bounded [0, 1].
    """
    nums: list[float] = []
    for m in NUMBER_RE.findall(text):
        try:
            nums.append(float(m.replace(",", ".")))
        except ValueError:
            continue
    if not nums:
        return 0.0
    grounded = sum(1 for n in nums if abs(n - expected) <= tol * max(abs(expected), 1.0))
    return grounded / len(nums)

def unit_specification(text: str) -> int:
    return int(bool(UNIT_RE.search(text)))

def temporal_specificity(text: str, day_name: str, hour: int) -> int:
    score = 0
    if re.search(rf"\b{day_name}\b", text, re.IGNORECASE):
        score += 1
    hour_patterns = [rf"\b{hour:02d}:00\b", rf"\b{hour}:00\b", rf"\b{hour}\s*(?:am|pm|AM|PM)\b",
                     rf"\b{hour}\s*o'?clock\b"]
    if any(re.search(p, text) for p in hour_patterns):
        score += 1
    if re.search(r"per\s+minute|1m|t1\s+interval|sampling\s+interval", text, re.IGNORECASE):
        score += 1
    return score

VALIDATOR_PROMPT = """You are a strict, neutral validator of short traffic reports.

You will see ONE report. Score it on TWO criteria and return JSON ONLY.

1) decision_actionability (integer 1-7):
   1 = no actionable guidance for a traffic operator
   4 = generic advice
   7 = a specific, concrete action tied to the predicted vehicle count

2) hallucination_risk (number 0.0-1.0):
   0.0 = every claim is plausibly grounded in the source facts
   1.0 = clearly fabricated facts (numbers/places/policies not in source)

SOURCE FACTS:
- day: {day_name} (day_of_week={day_of_week})
- hour: {hour_of_day:02d}:00
- predicted vehicle count: {expected_vehicles} vehicles per minute

REPORT:
\"\"\"
{report}
\"\"\"

Return EXACTLY this JSON schema (no prose, no code fences):
{{"decision_actionability": <1-7>, "hallucination_risk": <0.0-1.0>, "rationale": "<<=30 words>"}}
"""

def parse_validator_json(raw: str) -> dict[str, Any]:
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    payload = m.group(0) if m else raw
    try:
        d = json.loads(payload)
    except json.JSONDecodeError:
        return {"decision_actionability": 4, "hallucination_risk": 0.5,
                "rationale": "parse_error", "_parse_error": True}
    return {
        "decision_actionability": int(np.clip(d.get("decision_actionability", 4), 1, 7)),
        "hallucination_risk": float(np.clip(d.get("hallucination_risk", 0.5), 0.0, 1.0)),
        "rationale": str(d.get("rationale", ""))[:200],
        "_parse_error": False,
    }

# Composite weights — chosen to balance domain-critical (grounding, units) with
# subjective quality (actionability) and risk (hallucination penalty).
WEIGHTS = {"numerical_grounding": 0.30, "unit_specification": 0.10,
           "temporal_specificity_norm": 0.10,
           "decision_actionability_norm": 0.30, "hallucination_safety": 0.20}

def composite(row: pd.Series) -> float:
    return float(
        WEIGHTS["numerical_grounding"] * row["numerical_grounding"]
        + WEIGHTS["unit_specification"] * row["unit_specification"]
        + WEIGHTS["temporal_specificity_norm"] * (row["temporal_specificity"] / 3.0)
        + WEIGHTS["decision_actionability_norm"] * ((row["decision_actionability"] - 1) / 6.0)
        + WEIGHTS["hallucination_safety"] * (1.0 - row["hallucination_risk"])
    )

# 7. SCORE ALL REPORTS ###################################

print("-" * 72)
print("Step 4 — Score every report (deterministic checks + AI judge)")
print("-" * 72)

score_rows: list[dict[str, Any]] = []
val_start = time.monotonic()
for i, r in reports_df.iterrows():
    facts = stimulus_facts(int(r["day_of_week"]), int(r["hour_of_day"]))
    text = r["report_text"]

    ng = numerical_grounding(text, facts["expected_vehicles"])
    us = unit_specification(text)
    ts = temporal_specificity(text, facts["day_name"], facts["hour_of_day"])

    judge_prompt = VALIDATOR_PROMPT.format(
        day_name=facts["day_name"], day_of_week=facts["day_of_week"],
        hour_of_day=facts["hour_of_day"], expected_vehicles=facts["expected_vehicles"],
        report=text,
    )
    try:
        judge_raw = ollama_chat(judge_prompt, model=VALIDATOR_MODEL,
                                temperature=0.0, json_mode=True)
        judge = parse_validator_json(judge_raw)
    except Exception as e:
        judge = {"decision_actionability": 4, "hallucination_risk": 0.5,
                 "rationale": f"validator_error: {e}", "_parse_error": True}

    row = {
        "prompt_id": r["prompt_id"],
        "day_of_week": int(r["day_of_week"]),
        "hour_of_day": int(r["hour_of_day"]),
        "expected_vehicles": float(r["expected_vehicles"]),
        "word_count": int(r["word_count"]),
        "numerical_grounding": ng,
        "unit_specification": us,
        "temporal_specificity": ts,
        "decision_actionability": judge["decision_actionability"],
        "hallucination_risk": judge["hallucination_risk"],
        "validator_rationale": judge["rationale"],
    }
    row["composite_score"] = composite(pd.Series(row))
    score_rows.append(row)
    # Incremental save — cut runs keep partial scores.
    pd.DataFrame(score_rows).to_csv(SCORES_CSV, index=False)
    elapsed = time.monotonic() - val_start
    print(f"   🔧 [{i + 1:3d}/{total}] {r['prompt_id']} "
          f"(elapsed {elapsed:6.1f}s) → "
          f"ng={ng:.2f} us={us} ts={ts} act={judge['decision_actionability']} "
          f"hr={judge['hallucination_risk']:.2f} → composite={row['composite_score']:.3f}")

scores_df = pd.DataFrame(score_rows)
scores_df.to_csv(SCORES_CSV, index=False)
print(f"   💾 saved {len(scores_df)} score rows → {SCORES_CSV}")
print()

# 8. STATISTICAL ANALYSIS ###################################

print("-" * 72)
print("Step 5 — Statistical comparison of prompts A / B / C")
print("-" * 72)

stats_lines: list[str] = []

def log(msg: str) -> None:
    print(msg)
    stats_lines.append(msg)

log(f"📊 N per prompt: {scores_df.groupby('prompt_id').size().to_dict()}")
log("")

# 8.1 Descriptive stats per prompt
desc = (scores_df.groupby("prompt_id")["composite_score"]
        .agg(["mean", "std", "min", "max"]).round(3))
log("📈 composite_score by prompt:")
log(desc.to_string())
log("")

# 8.2 Bartlett's test for equal variances
groups = [scores_df.query("prompt_id == @p")["composite_score"].to_numpy()
          for p in ["A", "B", "C"]]
b_stat, b_p = bartlett(*groups)
log(f"🔍 Bartlett's test (homogeneity of variance): W={b_stat:.4f}, p={b_p:.4f}")
var_equal = b_p >= 0.05
log(f"   → {'equal variances assumed (standard ANOVA)' if var_equal else 'unequal variances (Welch ANOVA)'}")
log("")

# 8.3 ANOVA across all 3 prompts
if var_equal:
    aov = pg.anova(dv="composite_score", between="prompt_id", data=scores_df, detailed=True)
    log("📋 One-way ANOVA (composite_score ~ prompt_id):")
else:
    aov = pg.welch_anova(dv="composite_score", between="prompt_id", data=scores_df)
    log("📋 Welch ANOVA (composite_score ~ prompt_id):")
log(aov.round(4).to_string(index=False))
p_col = "p-unc" if "p-unc" in aov.columns else "p_unc"
anova_p = float(aov[p_col].iloc[0])
log(f"   → ANOVA p-value = {anova_p:.4f}  "
    f"({'SIGNIFICANT — at least one prompt differs' if anova_p < 0.05 else 'not significant'})")
log("")

# 8.4 Pairwise t-tests with Bonferroni correction
log("📋 Pairwise t-tests (Bonferroni-corrected):")
ph = pg.pairwise_tests(dv="composite_score", between="prompt_id", data=scores_df,
                       padjust="bonf", parametric=True)
log(ph.round(4).to_string(index=False))
log("")

# Identify the best prompt and a head-to-head winner
means = scores_df.groupby("prompt_id")["composite_score"].mean()
best_prompt = means.idxmax()
log(f"🏆 Best mean composite_score: prompt {best_prompt} = {means[best_prompt]:.3f}")
sig_pairs = ph.query("`p-corr` < 0.05") if "p-corr" in ph.columns else ph.iloc[0:0]
if len(sig_pairs):
    for _, row in sig_pairs.iterrows():
        log(f"   ✅ prompt {row['A']} vs {row['B']}: corrected p={row['p-corr']:.4f} (significant)")
else:
    log("   ⚠️  no pairwise comparison reaches p<0.05 after Bonferroni correction")
log("")

# 8.5 OLS regression — composite_score ~ prompt + word_count
log("📋 OLS regression (composite_score ~ C(prompt_id) + word_count):")
reg = smf.ols("composite_score ~ C(prompt_id, Treatment(reference='A')) + word_count",
              data=scores_df).fit()
log(reg.summary().as_text())
log("")

STATS_TXT.write_text("\n".join(stats_lines), encoding="utf-8")
print(f"   💾 saved stats summary → {STATS_TXT}")
print()

# 9. PLOT ###################################

print("-" * 72)
print("Step 6 — Boxplot of composite_score by prompt")
print("-" * 72)

fig, ax = plt.subplots(figsize=(7, 5))
data_by_prompt = [scores_df.query("prompt_id == @p")["composite_score"].values
                  for p in ["A", "B", "C"]]
bp = ax.boxplot(data_by_prompt, labels=["A (Minimal)", "B (Structured)", "C (Reasoning)"],
                patch_artist=True, widths=0.55)
for patch, color in zip(bp["boxes"], ["#cfd8dc", "#90caf9", "#a5d6a7"]):
    patch.set_facecolor(color)
for p_id, vals in zip(["A", "B", "C"], data_by_prompt):
    jitter = RNG.uniform(-0.08, 0.08, size=len(vals))
    x = {"A": 1, "B": 2, "C": 3}[p_id] + jitter
    ax.scatter(x, vals, color="black", alpha=0.5, s=20, zorder=3)
ax.set_ylabel("composite_score (0-1)")
ax.set_title(f"Custom validator scores by prompt (N={N_PER_PROMPT} per prompt)\nANOVA p = {anova_p:.4f}")
ax.set_ylim(0, 1)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(PLOT_PNG, dpi=150)
plt.close(fig)
print(f"   🖼️  saved → {PLOT_PNG}")
print()

# 10. FINAL SUMMARY ###################################

print("=" * 72)
print("📊 SUMMARY")
print("=" * 72)
print(f"   reports validated: {len(scores_df)}")
print(f"   best prompt (mean composite_score): {best_prompt} = {means[best_prompt]:.3f}")
print(f"   ANOVA p-value: {anova_p:.4f}")
print(f"   significant pairwise differences (Bonferroni): {len(sig_pairs)}")
print(f"   📁 reports CSV : {REPORTS_CSV}")
print(f"   📁 scores CSV  : {SCORES_CSV}")
print(f"   📁 stats summary: {STATS_TXT}")
print(f"   📁 boxplot PNG : {PLOT_PNG}")
print("=" * 72)
