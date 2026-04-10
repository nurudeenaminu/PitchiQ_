# PitchIQ

PitchIQ is an end-to-end football match prediction project that combines data ingestion,
feature engineering, model training, evaluation, and serving.

It includes:

- A machine learning pipeline for match outcome prediction.
- A FastAPI backend for predictions and football data endpoints.
- A Streamlit dashboard for visualization and interaction.
- Reproducible configuration-driven workflows.

## Table of Contents

- [PitchIQ](#pitchiq)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Features](#features)
  - [Tech Stack](#tech-stack)
  - [Project Structure](#project-structure)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Environment Variables](#environment-variables)
  - [Usage](#usage)
  - [API](#api)
  - [Testing and Quality](#testing-and-quality)
  - [Docker](#docker)
  - [CI/CD](#cicd)
  - [Troubleshooting](#troubleshooting)

## Overview

The project predicts football match outcomes using engineered historical and contextual
features. The workflow is designed to reduce leakage risk with time-aware validation
and reproducible training/evaluation stages.

## Features

- Data ingestion from multiple football data sources.
- Feature engineering for rolling form and context features.
- Ensemble-based training workflow.
- Evaluation outputs and reporting.
- Versioned API routes under `/v1`.
- Dashboard for model and data inspection.

## Tech Stack

- Python 3.11
- FastAPI, Uvicorn
- Streamlit, Plotly
- Pandas, NumPy, DuckDB
- scikit-learn, XGBoost, LightGBM, Optuna, SHAP
- MLflow for experiment tracking
- Pytest, Ruff, MyPy for quality checks

## Project Structure

```text
.
|-- configs/
|-- data/
|-- docs/
|-- models/
|-- reports/
|-- src/
|   |-- api/
|   |-- dashboard/
|   |-- domain/
|   |-- evaluation/
|   |-- features/
|   |-- ingestion/
|   `-- training/
|-- tests/
|-- docker-compose.yml
|-- Dockerfile
|-- Makefile
`-- pyproject.toml
```

## Prerequisites

- Python 3.11+
- Poetry
- Make (optional, for shortcut commands)
- Docker and Docker Compose (optional)

## Setup

```bash
# Clone and enter project directory
git clone <your-repo-url>
cd PitchIQ_

# Install dependencies
poetry install --no-root

# Optional: install git hooks
pre-commit install
```

If you want the full training and evaluation stack, install the optional ML extra:

```bash
poetry install --no-root --extras ml
```

## Environment Variables

Copy `.env.example` to `.env` and set values as needed.

Common variables:

- `RAPIDAPI_KEY`: API-Football key for live/extended endpoints.
- `MLFLOW_TRACKING_URI`: remote or local MLflow tracking endpoint.
- `MLFLOW_TRACKING_USERNAME`: MLflow username if required.
- `MLFLOW_TRACKING_PASSWORD`: MLflow password/token if required.

## Usage

Run the pipeline stages:

```bash
make data
make features
make train
make eval
```

Run all stages:

```bash
make all
```

Serve backend API:

```bash
make serve-api
```

Serve dashboard:

```bash
make serve-ui
```

## API

Start the API and open:

- `http://localhost:8000/docs` for interactive OpenAPI docs.

Routes are versioned under `/v1`.

## Testing and Quality

Run tests:

```bash
make test
```

Run lint/type checks:

```bash
make lint
```

## Docker

Start containers:

```bash
make docker-up
```

Stop containers:

```bash
make docker-down
```

## CI/CD

GitHub Actions workflows are included for continuous integration and training-related
automation. Configure repository secrets if your workflow uses external services.

## Troubleshooting

- If API startup fails, verify `.env` values and dependency installation.
- If tests fail, run `poetry install` again to ensure all dev dependencies are present.
- If `make` is unavailable on Windows, use the Python module commands directly from `src/`.
