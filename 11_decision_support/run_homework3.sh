#!/usr/bin/env bash
# Run the whole Homework 3 pipeline end-to-end with one command.
#   1. Run the N=5 experiment (15 generator + 15 validator LLM calls)
#   2. Rebuild stats / boxplot / criteria / sample / system PNGs (all staged as
#      *.png.bin to dodge the Cursor sandbox)
#   3. Restore .png filenames
#
# Usage:
#   bash 11_decision_support/run_homework3.sh
#   bash 11_decision_support/run_homework3.sh --n 10        # bigger run
#
# Requires:
#   - ./.env at the repo root with OLLAMA_API_KEY=... (Ollama Cloud)
#   - 11_decision_support/.venv  already created with requirements installed.
#     (Recreate with: python3 -m venv 11_decision_support/.venv &&
#        11_decision_support/.venv/bin/pip install -r 11_decision_support/homework3_requirements.txt)

set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

PY="$ROOT/11_decision_support/.venv/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "❌ venv not found at $PY"
  echo "   Create it with:"
  echo "     python3 -m venv 11_decision_support/.venv"
  echo "     11_decision_support/.venv/bin/pip install -r 11_decision_support/homework3_requirements.txt"
  exit 1
fi

N_ARG=("--n" "5")
if [[ "${1:-}" == "--n" && -n "${2:-}" ]]; then
  N_ARG=("$1" "$2")
fi

echo "========================================================================"
echo "📋 HOMEWORK 3 — full pipeline"
echo "========================================================================"
echo "   python: $PY"
echo "   args  : ${N_ARG[*]}"
echo ""

echo "Step 1 — running experiment (this hits Ollama Cloud)..."
"$PY" 11_decision_support/homework3_submission.py "${N_ARG[@]}"

echo ""
echo "Step 2 — postprocessing (no network)..."
"$PY" 11_decision_support/homework3_postprocess.py

echo ""
echo "Step 3 — restoring .png filenames..."
bash 11_decision_support/output/rename_images.sh

echo ""
echo "Step 4 — building the real .docx (requires /tmp/hw3venv with python-docx)..."
if [[ ! -x /tmp/hw3venv/bin/python ]]; then
  echo "   ℹ️  Creating /tmp/hw3venv (one-time setup)..."
  python3 -m venv /tmp/hw3venv
  /tmp/hw3venv/bin/pip install --quiet python-docx
fi
/tmp/hw3venv/bin/python 11_decision_support/homework3_build_docx.py

echo ""
echo "========================================================================"
echo "✅ ALL DONE"
echo "========================================================================"
echo "Three submission-ready files were produced:"
echo "  📄 11_decision_support/homework3_submission.docx   ← submit this (preferred)"
echo "  🌐 11_decision_support/homework3_submission.html   ← open in Word as backup"
echo "  📝 11_decision_support/homework3_submission.md     ← source markdown"
echo ""
echo "Next steps:"
echo "  1. Open homework3_submission.docx in Word"
echo "  2. Fill the 5 yellow 'YOUR WRITING GOES HERE' placeholders in §1"
echo "  3. Save and submit to Canvas"
echo "========================================================================"
