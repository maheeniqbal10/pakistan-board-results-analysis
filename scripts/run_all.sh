#!/usr/bin/env bash
# Rebuild everything, in order. Stops at the first failure.
#
#   bash scripts/run_all.sh             offline: committed CSVs -> tidy table -> figures -> tests
#   bash scripts/run_all.sh --download  first download the FBISE PDFs (~95 MB, network
#                                       needed) and re-extract data/raw/*.csv from them
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "${1:-}" == "--download" ]]; then
    echo "== 1. collect: download PDFs, verify checksums, extract aggregate tables"
    python -m src.collect
else
    echo "== 1. collect: skipped (using committed data/raw/*.csv; pass --download to refresh)"
fi

echo "== 2. clean: validate and build data/processed/results_tidy.csv"
python -m src.clean

echo "== 3. figures and summary tables"
python -m scripts.make_figures

echo "== 4. lint and tests"
ruff check .
pytest -q

echo "Done. Open notebooks/analysis.ipynb for the narrative."
