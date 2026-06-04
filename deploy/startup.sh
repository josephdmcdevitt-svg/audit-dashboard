#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

mkdir -p data
# Server, client, and theme settings live in .streamlit/config.toml
exec streamlit run app.py \
  --server.port="${PORT:-8501}" \
  --server.address=0.0.0.0
