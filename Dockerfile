FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/data \
 && useradd --create-home --shell /bin/bash ledger \
 && chown -R ledger:ledger /app
USER ledger

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableXsrfProtection=true", \
     "--browser.gatherUsageStats=false", \
     "--client.toolbarMode=minimal", \
     "--client.showSidebarNavigation=false", \
     "--theme.base=light", \
     "--theme.primaryColor=#1a2332", \
     "--theme.backgroundColor=#f6f2e9", \
     "--theme.secondaryBackgroundColor=#efe9dc", \
     "--theme.textColor=#1a2332", \
     "--theme.font=serif"]
