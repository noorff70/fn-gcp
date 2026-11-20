FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fruit ./fruit
COPY data/inventory.db ./data/inventory.db

# Settings come from env vars in containers (no .env file inside the image)
ENV DATABASE_URL=data/inventory.db ENVIRONMENT=docker

# Don't run as root
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8080
# Cloud Run (and others) tell the app which port to use via $PORT
CMD exec uvicorn fruit.main:app --host 0.0.0.0 --port ${PORT:-8080}