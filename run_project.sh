#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mode="${1:-app}"
case "$mode" in app|notebook|prepare) ;; *) echo 'Usage: bash run_project.sh [app|notebook|prepare]'; exit 2 ;; esac
if [ ! -d .venv ]; then "${PYTHON:-python3}" -m venv .venv; fi
.venv/bin/python -m pip install -r requirements.txt
case "$mode" in
  prepare) shift; exec .venv/bin/python src/utils/download_dataset.py "$@" ;;
  notebook) .venv/bin/python -m pip install -r requirements-notebooks.txt; exec .venv/bin/jupyter notebook notebooks/image_retrival.ipynb ;;
  app) exec .venv/bin/streamlit run src/streamlit-app.py ;;
esac
