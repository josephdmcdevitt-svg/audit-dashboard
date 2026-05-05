#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

mkdir -p data
exec streamlit run app.py \
  --server.port="${PORT:-8501}" \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableXsrfProtection=true \
  --browser.gatherUsageStats=false \
  --client.toolbarMode=minimal \
  --client.showSidebarNavigation=false \
  --theme.base=light \
  --theme.primaryColor="#1a2332" \
  --theme.backgroundColor="#f6f2e9" \
  --theme.secondaryBackgroundColor="#efe9dc" \
  --theme.textColor="#1a2332" \
  --theme.font=serif
