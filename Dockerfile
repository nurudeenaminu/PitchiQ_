FROM python:3.11-slim as builder

WORKDIR /app
COPY pyproject.toml .
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --only=main --no-dev

FROM python:3.11-slim as api

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# Copy all required source modules (API depends on domain, features, config)
COPY src/ ./src/
COPY models/ ./models/
COPY configs/ ./configs/
COPY data/features/ ./data/features/

EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim as dashboard

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# Copy all required source modules (dashboard depends on domain, services)
COPY src/ ./src/
COPY configs/ ./configs/
COPY reports/ ./reports/

EXPOSE 8501
CMD ["streamlit", "run", "src/dashboard/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]