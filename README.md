# PitchIQ — Football Match Prediction Engine

End-to-end ML system for football match outcome prediction. Stacked ensemble
(Logistic Regression + XGBoost + LightGBM) trained on historical match data
with xG, rolling form, and contextual features.

## Quick Start

```bash
# 1. Install dependencies
poetry install

# 2. Copy environment template and fill in your API keys
cp .env.example .env

# 3. Run the full pipeline
make data       # ingest raw match data
make features   # build feature store
make train      # train stacked ensemble
make eval       # generate evaluation reports

# 4. Start serving
make serve-api  # FastAPI on :8000
make serve-ui   # Streamlit on :8501

# Or run everything via Docker
make docker-up
```

## Project Structure

```
PitchIQ/
├── src/
│   ├── api/          # FastAPI backend (all routes under /v1/)
│   ├── dashboard/    # Streamlit frontend
│   ├── ingestion/    # Data source adapters
│   ├── features/     # Feature engineering pipeline
│   ├── training/     # Model training + HPO
│   ├── evaluation/   # Metrics, calibration, SHAP
│   └── domain/       # Canonical league/team definitions
├── configs/          # sources.yaml, model.yaml, features.yaml
├── data/             # Raw + processed data (DVC-tracked)
├── models/           # Trained model artefacts (DVC-tracked)
├── reports/          # Evaluation outputs (generated, not committed)
├── tests/            # Unit + integration tests
├── .env.example      # Environment variable template
├── Makefile          # Pipeline CLI
└── docker-compose.yml
```

## Data Sources

| Source | What it provides | Access |
|--------|-----------------|--------|
| football-data.co.uk | Historical results, betting odds | Free CSV download |
| Understat | Match-level xG | Free scraping via `understatapi` |
| FBref / StatsBomb | Advanced stats (xA, pressures, PPDA) | Free scraping via `soccerdata` |
| API-Football | Live scores, fixtures, injuries | Free tier: 100 req/day (RapidAPI) |

Set `RAPIDAPI_KEY` in `.env` to enable live data.

## API Reference

All endpoints are versioned under `/v1/`. See `/docs` for the full OpenAPI spec.

| Endpoint | Description |
|----------|-------------|
| `GET /v1/leagues` | Supported competitions |
| `GET /v1/live-scores` | Recent/live match scores |
| `GET /v1/league/{id}/table` | League standings |
| `GET /v1/league/{id}/fixtures` | Upcoming/recent fixtures |
| `GET /v1/league/{id}/top-scorers` | Goal scorers |
| `GET /v1/team/{id}` | Team profile |
| `GET /v1/team/{id}/matches` | Recent + upcoming matches |
| `GET /v1/team/{id}/stats/rolling` | Rolling form stats |
| `POST /v1/predict` | ML match prediction |
| `GET /v1/match/{id}/h2h` | Head-to-head history |
| `GET /v1/match/{id}/odds` | Implied betting probabilities |
| `GET /v1/model/performance` | Accuracy, log-loss, F1 |
| `GET /v1/model/calibration` | Calibration curve data |
| `GET /v1/model/feature-importance` | SHAP feature importances |
| `GET /v1/admin/pipeline-status` | Pipeline stage health |
| `GET /v1/admin/model-registry` | Trained model versions |

## Model Architecture

```
Features (27 columns)
    ├── Layer 1: LogisticRegression  ─┐
    ├── Layer 1: XGBoost             ─┼─ OOF probabilities [P(H), P(D), P(A)]
    └── Layer 1: LightGBM            ─┘
                                      │
    Layer 2: LogisticRegression (meta-learner) ── Final probabilities
```

Training uses `TimeSeriesSplit` (n=5). Features use `.shift(1)` before rolling
windows to prevent data leakage. Evaluation against held-out 2023/24 season.

## Engineering Principles

- **No data leakage**: `shift(1)` + `TimeSeriesSplit` only. Future data never touches training.
- **Deterministic API**: No `np.random` in serving endpoints. All non-prediction responses come from reports, feature store, or data snapshots.
- **Reproducible**: Every run is seeded. DVC tracks data + model artefacts.
- **Versioned API**: All routes under `/v1/`. Breaking changes require a new version prefix.
- **Schema-first**: `pandera` validation on every pipeline stage.

## Running Tests

```bash
make test
# or
pytest tests/ -v --tb=short
```

## GitHub Actions

Three workflows are included in `.github/workflows/`:

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `ci.yml` | Every push / PR | Lint (ruff, mypy) + pytest |
| `train.yml` | Manual / weekly schedule / feature changes | Full pipeline: ingest → features → train → eval, with MLflow logging |

### Required GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Required | Description |
|--------|----------|-------------|
| `RAPIDAPI_KEY` | Optional | API-Football key for live data ingestion |
| `MLFLOW_TRACKING_URI` | Optional | Remote MLflow URI (e.g. DagsHub). Defaults to local `mlruns/` |
| `MLFLOW_TRACKING_USERNAME` | Optional | MLflow remote auth username |
| `MLFLOW_TRACKING_PASSWORD` | Optional | MLflow remote auth password |

Without any secrets set, the pipeline runs fully offline using the bundled snapshot data and logs MLflow runs to `mlruns/` as build artefacts.

### Running the train workflow manually

1. Go to **Actions → Train & Evaluate → Run workflow**
2. Set `val_frac` (default `0.2`) and whether to train baselines
3. The workflow uploads the trained model and evaluation reports as build artefacts
4. Key metrics (log loss, F1, accuracy) are printed to the job summary
