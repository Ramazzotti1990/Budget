FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# wkhtmltopdf is not available in python:3.12-slim package sources; omitted intentionally.
# If PDF generation is needed in future, install from an official .deb release instead.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY sistema_presupuestos/requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY sistema_presupuestos /app

ENV FLASK_APP=wsgi:app \
    APP_ENV=dev

EXPOSE 8000

CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8000", "wsgi:app"]
