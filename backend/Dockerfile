FROM python:3.11-slim

# System deps + LibreOffice for headless conversion
RUN apt-get update && apt-get install -y --no-install-recommends     libreoffice-calc libreoffice-writer libreoffice-common     fonts-dejavu fonts-liberation     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir .

COPY app /app/app
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY scripts /app/scripts

ENV PYTHONUNBUFFERED=1

CMD ["bash", "/app/scripts/start.sh"]
