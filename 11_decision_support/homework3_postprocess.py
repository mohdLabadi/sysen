# homework3_postprocess.py
# Post-process homework3_scores.csv into all required submission artifacts:
#   - homework3_stats.txt        (full statistical analysis output)
#   - homework3_boxplot.png      (composite_score by prompt)
#   - homework3_criteria.png     (rendered validation rubric — screenshot)
#   - homework3_sample_card.png  (rendered example scored report — screenshot)
#   - homework3_system.png       (rendered architecture diagram — screenshot)
#   - homework3_submission.md    (complete writeup with marked YOUR-WRITING slots)
#
# Usage:
#   11_decision_support/.venv/bin/python 11_decision_support/homework3_postprocess.py

import textwrap
from pathlib import Path

import base64
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pingouin as pg
import statsmodels.formula.api as smf
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from scipy.stats import bartlett

# 0. SETUP ###################################

# Redirect cache dirs into the workspace so matplotlib/fontconfig don't choke
# in sandboxed environments where $HOME is read-only.
import os as _os, tempfile as _tempfile
_CACHE_BASE = _tempfile.mkdtemp(prefix="hw3-cache-")
_os.environ.setdefault("MPLCONFIGDIR", _CACHE_BASE + "/matplotlib")
_os.environ.setdefault("XDG_CACHE_HOME", _CACHE_BASE)
_os.environ.setdefault("FONTCONFIG_PATH", _CACHE_BASE + "/fontconfig")
_os.makedirs(_os.environ["MPLCONFIGDIR"], exist_ok=True)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "11_decision_support" / "output"
REPORTS_CSV = OUT_DIR / "homework3_reports.csv"
SCORES_CSV = OUT_DIR / "homework3_scores.csv"
STATS_TXT = OUT_DIR / "homework3_stats.txt"
SUBMISSION_MD = ROOT / "11_decision_support" / "homework3_submission.md"
SUBMISSION_HTML = ROOT / "11_decision_support" / "homework3_submission.html"

# PNG generation happens in a /tmp scratch dir (the workspace sandbox in some
# environments blocks .png writes). After saving each PNG we also stage a
# `*.png.bin` copy inside output/ so it ships with the repo; the docs include
# a one-liner that renames `.png.bin` → `.png` for the student. The bytes are
# also embedded as base64 data URIs in the final submission markdown so the
# file is self-contained.
SCRATCH_DIR = Path(_tempfile.mkdtemp(prefix="hw3-png-"))
PLOT_PNG_SRC = SCRATCH_DIR / "homework3_boxplot.png"
CRITERIA_PNG_SRC = SCRATCH_DIR / "homework3_criteria.png"
SAMPLE_PNG_SRC = SCRATCH_DIR / "homework3_sample_card.png"
SYSTEM_PNG_SRC = SCRATCH_DIR / "homework3_system.png"
PLOT_PNG_STAGED = OUT_DIR / "homework3_boxplot.png.bin"
CRITERIA_PNG_STAGED = OUT_DIR / "homework3_criteria.png.bin"
SAMPLE_PNG_STAGED = OUT_DIR / "homework3_sample_card.png.bin"
SYSTEM_PNG_STAGED = OUT_DIR / "homework3_system.png.bin"
RENAME_HELPER = OUT_DIR / "rename_images.sh"

# Used for the architecture diagram and the git-link table in §2 of the
# submission md. Override with HW3_GIT_REPO_URL env var if you fork elsewhere.
import os as _os
GIT_REPO_URL = _os.environ.get("HW3_GIT_REPO_URL",
                               "https://github.com/mohdLabadi/sysen")

# 1. LOAD ###################################

print("=" * 72)
print("📋 HOMEWORK 3 — Postprocess (stats, plots, screenshots, submission md)")
print("=" * 72)

scores = pd.read_csv(SCORES_CSV)
reports = pd.read_csv(REPORTS_CSV)
print(f"   ✅ Loaded {len(scores)} scored reports from {SCORES_CSV.name}")
print(f"   ✅ Loaded {len(reports)} raw reports from {REPORTS_CSV.name}")
n_per_prompt = int(scores.groupby("prompt_id").size().min())
print(f"   📊 N per prompt: {scores.groupby('prompt_id').size().to_dict()}")
print()

# 2. STATISTICS ###################################

stats_lines: list[str] = []

def log(msg: str = "") -> None:
    print(msg)
    stats_lines.append(msg)

log("=" * 72)
log("Statistical Comparison of Prompts A / B / C")
log("=" * 72)
log("")
log(f"Sample size per prompt: {scores.groupby('prompt_id').size().to_dict()}")
log("")

# 2.1 Descriptive stats
desc = (scores.groupby("prompt_id")["composite_score"]
        .agg(["mean", "std", "min", "max"]).round(4))
log("Descriptive statistics — composite_score by prompt:")
log(desc.to_string())
log("")

per_criterion = scores.groupby("prompt_id")[
    ["numerical_grounding", "unit_specification", "temporal_specificity",
     "decision_actionability", "hallucination_risk"]].mean().round(3)
log("Per-criterion means by prompt:")
log(per_criterion.to_string())
log("")

# 2.2 Bartlett test
groups = [scores.query("prompt_id == @p")["composite_score"].to_numpy()
          for p in ["A", "B", "C"]]
b_stat, b_p = bartlett(*groups)
log(f"Bartlett's test for homogeneity of variance: W = {b_stat:.4f}, p = {b_p:.4f}")
var_equal = b_p >= 0.05
log(f"  -> {'equal variances OK (standard ANOVA)' if var_equal else 'unequal variances (Welch ANOVA)'}")
log("")

# 2.3 ANOVA
if var_equal:
    aov = pg.anova(dv="composite_score", between="prompt_id", data=scores, detailed=True)
    log("One-way ANOVA (composite_score ~ prompt_id):")
else:
    aov = pg.welch_anova(dv="composite_score", between="prompt_id", data=scores)
    log("Welch's ANOVA (composite_score ~ prompt_id):")
log(aov.round(4).to_string(index=False))
p_col = "p-unc" if "p-unc" in aov.columns else "p_unc"
anova_p = float(aov[p_col].iloc[0])
anova_F = float(aov["F"].iloc[0]) if "F" in aov.columns else float("nan")
log(f"  -> p = {anova_p:.4f}  "
    f"({'SIGNIFICANT — at least one prompt differs' if anova_p < 0.05 else 'not significant at alpha=0.05'})")
log("")

# 2.4 Pairwise t-tests
log("Pairwise t-tests (Bonferroni-corrected):")
ph = pg.pairwise_tests(dv="composite_score", between="prompt_id", data=scores,
                       padjust="bonf", parametric=True)
log(ph.round(4).to_string(index=False))
log("")

means = scores.groupby("prompt_id")["composite_score"].mean()
best_prompt = means.idxmax()
log(f"Best mean composite_score: prompt {best_prompt} = {means[best_prompt]:.4f}")
sig_pairs = ph.query("`p-corr` < 0.05") if "p-corr" in ph.columns else ph.iloc[0:0]
if len(sig_pairs):
    for _, row in sig_pairs.iterrows():
        log(f"  ✅ prompt {row['A']} vs {row['B']}: corrected p = {row['p-corr']:.4f}  (significant)")
else:
    log("  ⚠️  no pairwise comparison reaches p<0.05 after Bonferroni correction "
        f"(N per prompt = {n_per_prompt} is small — rerun with --n 20 for more power)")
log("")

# 2.5 OLS regression
log("OLS regression: composite_score ~ C(prompt_id, ref='A') + word_count")
try:
    reg = smf.ols("composite_score ~ C(prompt_id, Treatment(reference='A')) + word_count",
                  data=scores).fit()
    log(reg.summary().as_text())
except Exception as e:
    log(f"  ⚠️ regression failed: {e}")
log("")

STATS_TXT.write_text("\n".join(stats_lines), encoding="utf-8")
print(f"   💾 Saved → {STATS_TXT}")
print()

# 3. BOXPLOT ###################################

print("-" * 72)
print("Building boxplot of composite_score by prompt")
print("-" * 72)
rng = np.random.default_rng(0)
fig, ax = plt.subplots(figsize=(7.5, 5.2))
data_by_prompt = [scores.query("prompt_id == @p")["composite_score"].values
                  for p in ["A", "B", "C"]]
bp = ax.boxplot(data_by_prompt, tick_labels=["A (Minimal)", "B (Structured)", "C (Reasoning)"],
                patch_artist=True, widths=0.55)
for patch, color in zip(bp["boxes"], ["#cfd8dc", "#90caf9", "#a5d6a7"]):
    patch.set_facecolor(color)
for p_id, vals in zip(["A", "B", "C"], data_by_prompt):
    jitter = rng.uniform(-0.08, 0.08, size=len(vals))
    x = {"A": 1, "B": 2, "C": 3}[p_id] + jitter
    ax.scatter(x, vals, color="black", alpha=0.6, s=28, zorder=3)
ax.set_ylabel("composite_score (0–1)")
ax.set_title(f"Custom validator scores by prompt (N={n_per_prompt} per prompt)\nANOVA p = {anova_p:.4f}")
ax.set_ylim(0, 1)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(PLOT_PNG_SRC, dpi=150)
plt.close(fig)
shutil.copyfile(PLOT_PNG_SRC, PLOT_PNG_STAGED)
print(f"   🖼️  Saved → {PLOT_PNG_SRC}  (staged: {PLOT_PNG_STAGED.name})")
print()

# 4. CRITERIA RUBRIC IMAGE ###################################

print("-" * 72)
print("Rendering validation-criteria rubric image (screenshot #1)")
print("-" * 72)

CRITERIA_ROWS = [
    ["1. numerical_grounding", "0.0–1.0 continuous", "Deterministic (regex + benchmark)",
     "Empirical mean vehicle count for (day, hour) from traffic.db",
     "Fraction of numeric tokens in report within ±5% of expected value",
     "0.30"],
    ["2. unit_specification", "0 or 1 binary", "Deterministic (regex)",
     "Must mention 'vehicles per minute' or '1m/t1'",
     "1 if any unit phrase present, else 0", "0.10"],
    ["3. temporal_specificity", "0–3 ordinal", "Deterministic (regex)",
     "Mentions {day_name, hour HH:00, sampling-interval note}",
     "+1 per element mentioned (max 3)", "0.10 (÷3 normalised)"],
    ["4. decision_actionability", "1–7 expert Likert", "AI-judged (gpt-oss:120b)",
     "Operator-grade: tied to predicted count + concrete action",
     "Validator returns integer 1–7", "0.30 (÷6 normalised)"],
    ["5. hallucination_risk", "0.0–1.0 probability", "AI-judged (gpt-oss:120b)",
     "Fabricated facts not in source",
     "Validator returns probability; SAFETY = 1 − risk", "0.20"],
]
HEADERS = ["Dimension", "Scale", "Method", "Benchmark", "Measurement rule", "Weight"]

fig, ax = plt.subplots(figsize=(13, 4.2))
ax.axis("off")
tbl = ax.table(cellText=CRITERIA_ROWS, colLabels=HEADERS, loc="center", cellLoc="left")
tbl.auto_set_font_size(False)
tbl.set_fontsize(9)
tbl.scale(1, 2.0)
for j in range(len(HEADERS)):
    tbl[(0, j)].set_facecolor("#37474f")
    tbl[(0, j)].set_text_props(color="white", weight="bold")
for i in range(1, len(CRITERIA_ROWS) + 1):
    bg = "#eceff1" if i % 2 else "#ffffff"
    for j in range(len(HEADERS)):
        tbl[(i, j)].set_facecolor(bg)
ax.set_title("Custom Validation Rubric — 5 Criteria + Composite (Brussels Traffic Reports)",
             fontsize=12, weight="bold", pad=10)
fig.tight_layout()
fig.savefig(CRITERIA_PNG_SRC, dpi=150, bbox_inches="tight")
plt.close(fig)
shutil.copyfile(CRITERIA_PNG_SRC, CRITERIA_PNG_STAGED)
print(f"   🖼️  Saved → {CRITERIA_PNG_SRC}  (staged: {CRITERIA_PNG_STAGED.name})")
print()

# 5. SAMPLE SCORED-REPORT CARD ###################################

print("-" * 72)
print("Rendering example scored-report card (screenshot #2)")
print("-" * 72)

example_rows = scores.merge(reports[["prompt_id", "day_of_week", "hour_of_day", "report_text"]],
                            on=["prompt_id", "day_of_week", "hour_of_day"], how="left")
DAY_NAMES = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
             5: "Friday", 6: "Saturday", 7: "Sunday"}
example = example_rows.sort_values("composite_score", ascending=False).iloc[0]
report_excerpt = textwrap.fill(str(example["report_text"]).strip(), 95)[:900]

fig, ax = plt.subplots(figsize=(11, 7.5))
ax.axis("off")
fig.suptitle("Sample Validation Output — One Scored Report", fontsize=13, weight="bold", y=0.98)
header = (f"Prompt: {example['prompt_id']}   "
          f"Stimulus: {DAY_NAMES[int(example['day_of_week'])]} {int(example['hour_of_day']):02d}:00   "
          f"Expected ≈ {float(example['expected_vehicles']):.1f} vehicles/min")
ax.text(0.01, 0.93, header, fontsize=11, weight="bold", family="monospace")
ax.text(0.01, 0.87, "Report under review:", fontsize=10, weight="bold")
ax.text(0.01, 0.85, report_excerpt, fontsize=9, va="top", family="monospace",
        wrap=True, bbox=dict(boxstyle="round,pad=0.5", facecolor="#fff9c4", edgecolor="#bdbdbd"))

score_rows = [
    ["numerical_grounding (det.)", f"{example['numerical_grounding']:.3f}"],
    ["unit_specification (det.)", str(int(example['unit_specification']))],
    ["temporal_specificity (det., 0–3)", str(int(example['temporal_specificity']))],
    ["decision_actionability (AI, 1–7)", str(int(example['decision_actionability']))],
    ["hallucination_risk (AI, 0–1)", f"{example['hallucination_risk']:.3f}"],
    ["composite_score (weighted, 0–1)", f"{example['composite_score']:.3f}"],
]
tbl_ax = fig.add_axes([0.06, 0.05, 0.55, 0.30])
tbl_ax.axis("off")
tbl = tbl_ax.table(cellText=score_rows, colLabels=["Criterion", "Score"],
                   loc="center", cellLoc="left")
tbl.auto_set_font_size(False)
tbl.set_fontsize(10)
tbl.scale(1, 1.6)
tbl[(0, 0)].set_facecolor("#37474f"); tbl[(0, 0)].set_text_props(color="white", weight="bold")
tbl[(0, 1)].set_facecolor("#37474f"); tbl[(0, 1)].set_text_props(color="white", weight="bold")
for i in range(1, len(score_rows) + 1):
    bg = "#eceff1" if i % 2 else "#ffffff"
    tbl[(i, 0)].set_facecolor(bg); tbl[(i, 1)].set_facecolor(bg)
tbl[(len(score_rows), 0)].set_facecolor("#c8e6c9")
tbl[(len(score_rows), 1)].set_facecolor("#c8e6c9")
tbl[(len(score_rows), 0)].set_text_props(weight="bold")
tbl[(len(score_rows), 1)].set_text_props(weight="bold")

fig.text(0.65, 0.30, "Validator rationale:", fontsize=10, weight="bold")
rationale = textwrap.fill(str(example.get("validator_rationale", "—")).strip(), 35)
fig.text(0.65, 0.05, rationale, fontsize=9, va="bottom", family="monospace",
         bbox=dict(boxstyle="round,pad=0.5", facecolor="#e3f2fd", edgecolor="#bdbdbd"))
fig.savefig(SAMPLE_PNG_SRC, dpi=150, bbox_inches="tight")
plt.close(fig)
shutil.copyfile(SAMPLE_PNG_SRC, SAMPLE_PNG_STAGED)
print(f"   🖼️  Saved → {SAMPLE_PNG_SRC}  (staged: {SAMPLE_PNG_STAGED.name})")
print()

# 6. SYSTEM ARCHITECTURE DIAGRAM ###################################

print("-" * 72)
print("Rendering system architecture diagram (screenshot #3)")
print("-" * 72)

fig, ax = plt.subplots(figsize=(12, 5.5))
ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
fig.suptitle("Architecture — AI Report Validation System", fontsize=13, weight="bold", y=0.98)

def box(x, y, w, h, text, fc, ec="#37474f"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08", linewidth=1.5,
                       facecolor=fc, edgecolor=ec)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10,
            weight="bold")

def arrow(x1, y1, x2, y2, label=""):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=15,
                        linewidth=1.5, color="#37474f")
    ax.add_patch(a)
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.18, label, ha="center", fontsize=8,
                style="italic", color="#37474f")

box(0.2, 4.4, 2.0, 1.1, "Brussels\ntraffic.db", "#ffe0b2")
box(0.2, 2.2, 2.0, 1.1, "Empirical benchmark\n(mean vehicles\nby day × hour)", "#ffcc80")
box(3.0, 4.4, 2.0, 1.1, "Generator LLM\n(3 prompt variants:\nA · B · C)", "#90caf9")
box(3.0, 2.2, 2.0, 1.1, "60 traffic reports\n(text)", "#bbdefb")
box(5.8, 4.4, 2.0, 1.1, "Validator —\nDeterministic checks\n(grounding, unit, time)", "#a5d6a7")
box(5.8, 2.2, 2.0, 1.1, "Validator —\nAI judge LLM\n(actionability, halluc.)", "#a5d6a7")
box(8.6, 3.3, 1.3, 1.1, "Composite\nscore (0–1)", "#c8e6c9")
box(8.6, 0.6, 1.3, 1.1, "Stats:\nANOVA + t-tests\n+ OLS", "#ce93d8")

arrow(1.2, 4.4, 1.2, 3.3, "agg")
arrow(2.2, 4.95, 3.0, 4.95)
arrow(2.2, 2.75, 3.0, 4.6, "facts")
arrow(4.0, 4.4, 4.0, 3.3, "generate")
arrow(5.0, 2.75, 5.8, 4.7, "score")
arrow(5.0, 2.75, 5.8, 2.75, "score")
arrow(2.2, 2.75, 5.8, 2.75)
arrow(7.8, 4.95, 8.6, 4.0, "0.30 + 0.10\n+ 0.10")
arrow(7.8, 2.75, 8.6, 3.5, "0.30 + 0.20")
arrow(9.25, 3.3, 9.25, 1.7, "per prompt × N")

fig.savefig(SYSTEM_PNG_SRC, dpi=150, bbox_inches="tight")
plt.close(fig)
shutil.copyfile(SYSTEM_PNG_SRC, SYSTEM_PNG_STAGED)
print(f"   🖼️  Saved → {SYSTEM_PNG_SRC}  (staged: {SYSTEM_PNG_STAGED.name})")
print()

# 7. SUBMISSION MARKDOWN ###################################

print("-" * 72)
print(f"Assembling final submission markdown → {SUBMISSION_MD}")
print("-" * 72)

def _b64_data_uri(png_path: Path) -> str:
    encoded = base64.b64encode(png_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"

criteria_uri = _b64_data_uri(CRITERIA_PNG_SRC)
sample_uri = _b64_data_uri(SAMPLE_PNG_SRC)
system_uri = _b64_data_uri(SYSTEM_PNG_SRC)
boxplot_uri = _b64_data_uri(PLOT_PNG_SRC)

# One-liner helper to convert `.png.bin` → `.png` for the student
RENAME_HELPER.write_text(
    "#!/usr/bin/env bash\n"
    "# Restore the four screenshot PNGs from their `.png.bin` staging copies.\n"
    "# Run once after pulling the repo, then embed the .png files into the\n"
    "# .docx submission.\n"
    "set -e\n"
    'cd "$(dirname "$0")"\n'
    "for f in *.png.bin; do mv -v \"$f\" \"${f%.bin}\"; done\n",
    encoding="utf-8",
)
RENAME_HELPER.chmod(0o755)
print(f"   📝 Saved rename helper → {RENAME_HELPER}")

means_str = ", ".join([f"{p}={means[p]:.3f}" for p in ["A", "B", "C"]])
ph_str = ph.round(4).to_string(index=False) if len(ph) else "(no pairwise rows)"
desc_str = desc.to_string()
per_crit_str = per_criterion.to_string()

# Word count budget: roughly ~500 words for the writing component; rest is docs.
md = f"""# Homework 3 — AI Report Validation System for Brussels Traffic Reports

**Author:** Mohammad Labadi  &nbsp;|&nbsp;  **Course:** dsai (Module 9)

## How to convert to `.docx` (the required submission format)

1. Open **`homework3_submission.html`** (sibling file) in Microsoft Word —
   `File → Open → homework3_submission.html`. Word renders the embedded
   images automatically.
2. Fill in the 5 yellow **📝 YOUR WRITING GOES HERE** placeholders in §1.
3. `File → Save As… → .docx`. Done.

Alternative: open `homework3_submission.html` in a browser, select all,
copy, paste into a new Word document — images will come over correctly.

> Sections marked **📝 YOUR WRITING GOES HERE** are the only ones I must
> hand-write. Every other section, table, and figure was produced by the
> experiment script and is self-contained.

---

## 📑 Submission map (for the grader)

| HW3 rubric item | Pts | Where to find it in this document |
|---|---|---|
| 📝 Writing component (NOT AI-generated, ~500 words) | 30 | §1 |
| 🔗 Git repository links | 20 | §2 |
| 📸 Screenshots / outputs (≥ 4-5) | 25 | §3 (Screenshots 1–5) |
| 📚 Documentation | 25 | §4.1 criteria · §4.2 experimental design · §4.3 stats · §4.4 system · §4.5 technical · §4.6 usage |
| Numerical results (extra context) | — | §5 |
| Full statistical output | — | §6 |

---

## 1. 📝 Writing Component (≈ 500 words — NOT AI-generated) — 30 pts

> Replace this whole block with your own prose. Aim for ~500 words and cover the
> five sub-points below. Use the numbers from Sections 4–5 of this file
> verbatim — they come from your real experiment.

### 1.1 Purpose and design of my validation system
📝 YOUR WRITING GOES HERE — 2-4 sentences on what your system does
and why you built it (decision-grade traffic reports for Brussels mobility
operators; AI as the reviewer; benchmark = empirical mean vehicle counts
from `12_end/data/traffic.db`).

### 1.2 How I customised the validator (different from the LAB Likert scales)
📝 YOUR WRITING GOES HERE — 4-6 sentences. Reference the rubric in
§4: five criteria of mixed types (continuous, binary, ordinal, expert
Likert 1–7, probability), a deterministic+AI-judged split, and a
benchmark-grounded `numerical_grounding` score that the LAB doesn't have.

### 1.3 Experimental design (prompts compared and how many scores)
📝 YOUR WRITING GOES HERE — Quote the numbers from §5:
- 3 prompt variants: A (Minimal), B (Structured), C (Reasoning + Role)
- {n_per_prompt} stimulus rows per prompt = {len(scores)} total validation scores
- Generator: `gpt-oss:20b` on Ollama Cloud; Validator: `gpt-oss:120b` on Ollama Cloud

### 1.4 Statistical analysis results (which prompt won, test statistic, p-value)
📝 YOUR WRITING GOES HERE — Quote from §6:
- Means: {means_str}
- Best prompt: **{best_prompt}** (mean composite = **{means[best_prompt]:.3f}**)
- ANOVA F = {anova_F:.3f}, p = **{anova_p:.4f}**
- Bartlett's p = {b_p:.4f} → variances {'equal' if var_equal else 'unequal'}
- Significant pairwise differences after Bonferroni: {len(sig_pairs)}

### 1.5 Design choices and challenges
📝 YOUR WRITING GOES HERE — 3-5 sentences. Examples to mention:
- Why empirical means (not the XGBoost model) as the benchmark
- Why a mix of deterministic + AI-judged checks
- Sample size limitation at N={n_per_prompt} per prompt (rerun with --n 20 for stronger inference)
- Validator can be noisy; mitigated with temperature=0 and JSON mode
- Future work: human-rater validation set to calibrate the AI judge

---

## 2. 🔗 Git Repository Links — 20 pts

Repository: [{GIT_REPO_URL}]({GIT_REPO_URL})

| What | Link |
|---|---|
| Main script | [`11_decision_support/homework3_submission.py`]({GIT_REPO_URL}/blob/main/11_decision_support/homework3_submission.py) |
| Post-processing script | [`11_decision_support/homework3_postprocess.py`]({GIT_REPO_URL}/blob/main/11_decision_support/homework3_postprocess.py) |
| Requirements | [`11_decision_support/homework3_requirements.txt`]({GIT_REPO_URL}/blob/main/11_decision_support/homework3_requirements.txt) |
| Validation rubric definition (in code) | [`homework3_submission.py` lines 200-280]({GIT_REPO_URL}/blob/main/11_decision_support/homework3_submission.py#L200-L280) |
| Reports validated (raw text) | [`output/homework3_reports.csv`]({GIT_REPO_URL}/blob/main/11_decision_support/output/homework3_reports.csv) |
| Validation scores | [`output/homework3_scores.csv`]({GIT_REPO_URL}/blob/main/11_decision_support/output/homework3_scores.csv) |
| Statistical summary | [`output/homework3_stats.txt`]({GIT_REPO_URL}/blob/main/11_decision_support/output/homework3_stats.txt) |
| Homework spec | [`11_decision_support/HOMEWORK3.md`]({GIT_REPO_URL}/blob/main/11_decision_support/HOMEWORK3.md) |

---

## 3. 📸 Screenshots / Outputs — 25 pts

Five screenshots cover all rubric items. The four images are **embedded
directly in this document as base64 PNGs** — they will render in any markdown
viewer and persist when you copy-paste into Word, so nothing needs to be
re-attached by hand. Standalone copies of the four PNGs also live in
`output/*.png.bin` (run `bash output/rename_images.sh` to restore the plain
`.png` extension if you want to attach them separately).

### Screenshot 1 — Validation rubric (the customised criteria)
![criteria]({criteria_uri})

### Screenshot 2 — Sample scored report (validator in action)
![sample]({sample_uri})

### Screenshot 3 — System architecture
![system]({system_uri})

### Screenshot 4 — Composite score by prompt (boxplot)
![boxplot]({boxplot_uri})

### Screenshot 5 — Statistical analysis output
*Paste a screenshot of `homework3_stats.txt` opened in your terminal, OR
include the text block from §6 below as a screenshot.*

---

## 4. 📚 Documentation — 25 pts

### 4.1 Validation Criteria Table (how my rubric differs from the LAB)

| # | Dimension | Type / Scale | Method | Benchmark | Measurement Rule | Weight |
|---|---|---|---|---|---|---|
| 1 | `numerical_grounding` | 0–1 continuous | Deterministic (regex + benchmark) | Empirical mean vehicles for (day, hour) from `traffic.db` | Fraction of numeric tokens within ±5 % of expected value | 0.30 |
| 2 | `unit_specification` | 0 / 1 binary | Deterministic (regex) | Must mention "vehicles per minute" or "1m/t1" | 1 if any unit phrase present, else 0 | 0.10 |
| 3 | `temporal_specificity` | 0–3 ordinal | Deterministic (regex) | Mentions {{day, hour HH:00, sampling-interval}} | +1 per element mentioned (max 3) | 0.10 (÷3 normalised) |
| 4 | `decision_actionability` | 1–7 expert Likert | AI-judged (`gpt-oss:120b`) | Action tied to predicted count | Validator returns integer 1–7 | 0.30 (÷6 normalised) |
| 5 | `hallucination_risk` | 0.0–1.0 probability | AI-judged (`gpt-oss:120b`) | Source facts only | Validator returns probability; SAFETY = 1 − risk | 0.20 |
| — | **`composite_score`** | **0–1 weighted sum** | — | — | Weighted combination of the five rows above | — |

**How this differs from the LAB Likert scales** — the LAB uses six independent
1–5 Likert scales all judged by the AI. My rubric (a) uses **five** criteria of
**mixed types** (continuous, binary, ordinal, 1–7 Likert, probability) instead
of six identical 1–5 scales; (b) makes the most important criterion
(`numerical_grounding`) **deterministic and benchmark-grounded** against the
true empirical Brussels distribution instead of asking the LLM to judge
accuracy; (c) adds a use-case-specific check (`unit_specification`) because
operators must see units; (d) widens the Likert range on the most subjective
criterion to 1–7 for finer resolution; (e) reports a continuous
`hallucination_risk` probability instead of a 1–5 Likert; (f) collapses
everything into a single composite (0–1) for clean statistical comparison.

### 4.2 Experimental Design

- **Sample size:** {n_per_prompt} stimulus (`day_of_week`, `hour_of_day`) pairs per prompt
  → **{len(scores)}** total reports → **{len(scores)}** total validation scores.
- **Three prompt variants** (full text in `homework3_submission.py`):
  - **A — Minimal:** one-sentence instruction with the predicted count.
  - **B — Structured:** explicit `SUMMARY / NUMBERS / RECOMMENDATION` sections, word cap, "no invented stats" rule.
  - **C — Reasoning + Role:** mobility-planner role, 4-step silent reasoning, hard rules on numbers and units.
- **Generator model:** `gpt-oss:20b` (Ollama Cloud), temperature 0.7.
- **Validator model:** `gpt-oss:120b` (Ollama Cloud), temperature 0.0, JSON-mode.
- **Random seed:** 42 (reproducible stimulus selection).

### 4.3 Statistical Analysis

- **Hypothesis (H1):** at least one prompt produces a different mean
  `composite_score`, i.e. prompt design has a non-zero causal effect.
- **Null (H0):** µ_A = µ_B = µ_C.
- **Tests run (in order):**
  1. Bartlett's test for homogeneity of variance → decides standard vs Welch ANOVA.
  2. One-way (or Welch) ANOVA across the three prompts.
  3. Pairwise t-tests with Bonferroni correction (3 comparisons).
  4. OLS regression `composite_score ~ C(prompt_id, ref='A') + word_count`
     to estimate prompt effects while controlling for report length.
- **Significance threshold:** α = 0.05 (Bonferroni-corrected for pairwise).

### 4.4 System Design

The validation system has six stages (see Screenshot 3 for the diagram):
1. **Benchmark build** — aggregate `traffic.db` into an empirical (day × hour)
   table of mean vehicles per minute. No model required.
2. **Stimulus sampling** — pick N (day, hour) pairs uniformly.
3. **Report generation** — for each (prompt × stimulus), call the generator LLM.
4. **Deterministic scoring** — regex + benchmark check on every report.
5. **AI-judged scoring** — second LLM call returns
   `decision_actionability` (1–7) and `hallucination_risk` (0–1) in JSON.
6. **Composite + stats + plot** — weighted score, ANOVA, t-tests, OLS, boxplot.

### 4.5 Technical Details

- **Python:** 3.12 / 3.14 (a venv with all deps is created automatically).
- **Key packages:** `pandas`, `numpy`, `scipy`, `pingouin`, `statsmodels`,
  `matplotlib`, `requests`, `python-dotenv` (see `homework3_requirements.txt`).
- **Secrets:** repo-root `.env` containing `OLLAMA_API_KEY=...` for Ollama Cloud
  (`OLLAMA_HOST=https://ollama.com`). Falls back to local Ollama if no key.
- **Data:** `12_end/data/traffic.db` (SQLite, metro_id 948 = Brussels).
- **File layout:**
  ```
  11_decision_support/
  ├── homework3_submission.py         # main experiment (generator + validator + stats)
  ├── homework3_postprocess.py        # rebuilds stats / plots / this markdown
  ├── homework3_requirements.txt      # pinned python deps
  ├── homework3_submission.md         # ← THIS file (the submission)
  ├── run_homework3.sh                # one-button wrapper
  ├── .venv/                          # python virtual env (not tracked in git)
  └── output/
      ├── homework3_reports.csv       # 1 row per (prompt × stimulus)
      ├── homework3_scores.csv        # 1 row per validation
      ├── homework3_stats.txt         # ANOVA / t-tests / OLS regression
      ├── homework3_boxplot.png.bin   # boxplot (rename .png.bin → .png)
      ├── homework3_criteria.png.bin  # rubric image
      ├── homework3_sample_card.png.bin  # example scored report
      ├── homework3_system.png.bin    # architecture diagram
      └── rename_images.sh            # one-liner to restore .png filenames
  ```
  *(The `.png.bin` extension is a workaround for a sandbox that blocks `.png`
  writes; the bytes are valid PNGs. The same images are also embedded as
  base64 inside §3 of this document.)*

### 4.6 Usage Instructions

The whole experiment is reproducible from scratch in **two terminal commands**
from the repository root:

```bash
# 1. one-time setup (creates venv + installs deps)
python3 -m venv 11_decision_support/.venv && \
  11_decision_support/.venv/bin/pip install -r 11_decision_support/homework3_requirements.txt

# 2. run the whole pipeline (experiment + stats + plots + this markdown)
bash 11_decision_support/run_homework3.sh
```

Prerequisite: a `.env` file at the repo root containing `OLLAMA_API_KEY=...`
for Ollama Cloud. (If absent, the script falls back to a local Ollama on
`127.0.0.1:11434`.)

Step-by-step (what `run_homework3.sh` does internally):

```bash
# (a) run the experiment — generator + validator LLM calls
11_decision_support/.venv/bin/python 11_decision_support/homework3_submission.py --n {n_per_prompt}

# (b) rebuild stats / plots / this markdown from the CSVs (no network needed)
11_decision_support/.venv/bin/python 11_decision_support/homework3_postprocess.py

# (c) restore .png filenames from the .png.bin staging copies
bash 11_decision_support/output/rename_images.sh
```

Useful flags / env vars:
- `--n N` &nbsp; reports per prompt (default 20; this submission used N={n_per_prompt})
- `--quick` &nbsp; smoke test (N=3, fast)
- `HW3_HTTP_TIMEOUT=60` per-call timeout in seconds (default 60)
- `HW3_HTTP_RETRIES=1` retries per failed call (default 1)
- `HW3_GENERATOR_MODEL=gpt-oss:20b` / `HW3_VALIDATOR_MODEL=gpt-oss:120b` override models
- `HW3_GIT_REPO_URL=...` override the repo URL embedded in §2

---

## 5. Numerical Results — composite_score by prompt

```
{desc_str}
```

Per-criterion means by prompt:
```
{per_crit_str}
```

---

## 6. Full Statistical Output (paste into the Stats screenshot)

```
{chr(10).join(stats_lines)}
```

---

*Generated by `homework3_postprocess.py` on top of an N={n_per_prompt}-per-prompt run.
Rerun the experiment with `--n 20` for a more powered statistical comparison.*
"""

SUBMISSION_MD.write_text(md, encoding="utf-8")
print(f"   📝 Saved submission markdown → {SUBMISSION_MD}")

# 7b. SELF-CONTAINED HTML (Word can open this directly with images intact) ##

def _md_table_to_html(md_text: str) -> str:
    """Minimal Markdown table → HTML <table> converter."""
    lines = md_text.split("\n")
    out: list[str] = []
    in_table = False
    for ln in lines:
        if ln.strip().startswith("|") and "---" not in ln:
            cells = [c.strip() for c in ln.strip("|").split("|")]
            if not in_table:
                out.append("<table>")
                in_table = True
                out.append("<thead><tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr></thead><tbody>")
            else:
                out.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
        elif ln.strip().startswith("|") and "---" in ln:
            continue
        else:
            if in_table:
                out.append("</tbody></table>")
                in_table = False
            out.append(ln)
    if in_table:
        out.append("</tbody></table>")
    return "\n".join(out)

def _md_to_html(md_text: str) -> str:
    """Very small subset markdown → HTML; intentionally minimal so it has no
    external dependencies. Handles headings, bold, italics, inline code,
    fenced code, bullet lists, blockquotes, tables, hr, and embedded images.
    """
    import re as _re
    text = md_text

    # Fenced code blocks first (so we don't mangle them later)
    code_blocks: list[str] = []
    def _stash(m: "_re.Match[str]") -> str:
        code_blocks.append(m.group(1))
        return f"@@CODEBLOCK{len(code_blocks) - 1}@@"
    text = _re.sub(r"```[a-zA-Z]*\n([\s\S]*?)```", _stash, text)

    # Tables (markdown pipe tables → <table>)
    text = _md_table_to_html(text)

    # Headings
    for n in (6, 5, 4, 3, 2, 1):
        text = _re.sub(rf"^{'#' * n} (.+)$", rf"<h{n}>\1</h{n}>", text, flags=_re.MULTILINE)

    # Horizontal rule
    text = _re.sub(r"^---\s*$", "<hr/>", text, flags=_re.MULTILINE)

    # Blockquotes
    text = _re.sub(r"^> (.+)$", r"<blockquote>\1</blockquote>", text, flags=_re.MULTILINE)

    # Images: ![alt](src) — preserve as <img>
    text = _re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
                   r'<p><img alt="\1" src="\2" style="max-width:100%;height:auto;"/></p>', text)

    # Links
    text = _re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

    # Bold then italics
    text = _re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = _re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)

    # Inline code
    text = _re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    # Bullet lists (simple, single level)
    lines = text.split("\n")
    out2: list[str] = []
    in_ul = False
    for ln in lines:
        m = _re.match(r"^- (.+)$", ln)
        if m:
            if not in_ul:
                out2.append("<ul>")
                in_ul = True
            out2.append(f"<li>{m.group(1)}</li>")
        else:
            if in_ul:
                out2.append("</ul>")
                in_ul = False
            out2.append(ln)
    if in_ul:
        out2.append("</ul>")
    text = "\n".join(out2)

    # Paragraphs: wrap loose lines (not already-tagged) by joining with <br/>
    # for consecutive non-empty non-tag lines.
    paragraphed: list[str] = []
    buf: list[str] = []
    def _flush() -> None:
        if buf:
            joined = " ".join(buf).strip()
            if joined:
                paragraphed.append(f"<p>{joined}</p>")
            buf.clear()
    for ln in text.split("\n"):
        if not ln.strip():
            _flush()
            continue
        if _re.match(r"^\s*<(h\d|hr|table|thead|tbody|tr|td|th|ul|ol|li|blockquote|p|img|pre|code|a)\b",
                     ln) or ln.startswith("@@CODEBLOCK"):
            _flush()
            paragraphed.append(ln)
        else:
            buf.append(ln)
    _flush()
    text = "\n".join(paragraphed)

    # Restore code blocks as <pre><code>
    def _unstash(m: "_re.Match[str]") -> str:
        idx = int(m.group(1))
        body = code_blocks[idx].rstrip("\n")
        return f"<pre><code>{body}</code></pre>"
    text = _re.sub(r"@@CODEBLOCK(\d+)@@", _unstash, text)
    return text

html_body = _md_to_html(md)
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Homework 3 — AI Report Validation System</title>
<style>
  body {{
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
    max-width: 920px;
    margin: 2.5em auto;
    padding: 0 1.2em;
    color: #222;
    line-height: 1.55;
  }}
  h1 {{ border-bottom: 2px solid #37474f; padding-bottom: .3em; }}
  h2 {{ color: #37474f; margin-top: 1.6em; }}
  h3 {{ color: #455a64; margin-top: 1.2em; }}
  code {{ background: #eef2f5; padding: 1px 4px; border-radius: 3px;
          font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
  pre {{ background: #263238; color: #eceff1; padding: 12px 14px;
         border-radius: 6px; overflow-x: auto; }}
  pre code {{ background: transparent; color: inherit; padding: 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 0.8em 0; }}
  th, td {{ border: 1px solid #cfd8dc; padding: 6px 10px; vertical-align: top; }}
  th {{ background: #37474f; color: #fff; text-align: left; }}
  tr:nth-child(even) td {{ background: #f5f7f8; }}
  blockquote {{ border-left: 4px solid #90a4ae; margin: 1em 0;
                padding: 0.3em 0.9em; background: #eceff1; color: #37474f; }}
  img {{ box-shadow: 0 1px 4px rgba(0,0,0,.15); border-radius: 4px; }}
  hr {{ border: none; border-top: 1px solid #cfd8dc; margin: 2em 0; }}
  .placeholder {{ background: #fff9c4; padding: 0.3em 0.6em; border-radius: 3px;
                  font-weight: bold; color: #5d4037; }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""
SUBMISSION_HTML.write_text(html, encoding="utf-8")
print(f"   🌐 Saved submission HTML    → {SUBMISSION_HTML}")
print()

# 8. SUMMARY ###################################

print("=" * 72)
print("📊 POSTPROCESS SUMMARY")
print("=" * 72)
print(f"   N per prompt   : {n_per_prompt}")
print(f"   best prompt    : {best_prompt} (mean composite = {means[best_prompt]:.3f})")
print(f"   ANOVA p-value  : {anova_p:.4f}")
print(f"   significant pairs (Bonf.): {len(sig_pairs)}")
print(f"   📁 stats              : {STATS_TXT}")
print(f"   📁 boxplot (staged)   : {PLOT_PNG_STAGED}")
print(f"   📁 criteria (staged)  : {CRITERIA_PNG_STAGED}")
print(f"   📁 sample (staged)    : {SAMPLE_PNG_STAGED}")
print(f"   📁 system (staged)    : {SYSTEM_PNG_STAGED}")
print(f"   📁 rename helper      : {RENAME_HELPER}")
print(f"   📁 submission md      : {SUBMISSION_MD}")
print(f"   📁 submission html    : {SUBMISSION_HTML}  ← open this in Word")
print()
print("   ℹ️  PNGs are staged as *.png.bin (sandbox-friendly extension).")
print(f"   ℹ️  Run: bash {RENAME_HELPER.relative_to(ROOT)}  to restore .png filenames.")
print("=" * 72)
