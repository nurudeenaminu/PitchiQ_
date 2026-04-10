import { useState } from "react";

const phases = [
  {
    id: "P0", label: "P0 — Environment & Repo Bootstrap", color: "#00e5ff", duration: "Day 1–2",
    objective: "Establish reproducible, dependency-locked environment and project scaffold.",
    stack: ["Python 3.11+", "Poetry / pip-tools", "Git + pre-commit hooks", "DVC (Data Version Control)", "Makefile"],
    steps: [
      { title: "Initialise repository", detail: "Create a mono-repo with /data, /src, /notebooks, /models, /reports, /tests. Commit a .gitignore that excludes raw data, model binaries, and .env files. Tag v0.0.1." },
      { title: "Lock dependency graph", detail: "Define two dependency groups in pyproject.toml: core (pandas, numpy, scikit-learn, xgboost, lightgbm, torch, shap, optuna) and dev (pytest, black, ruff, mypy, jupyter). Pin all transitive deps with `poetry lock`. This is your reproducibility contract." },
      { title: "Set up DVC remote", detail: "Initialise DVC (`dvc init`). Configure a local or cloud remote (Google Drive or S3 bucket) as the data registry. All raw CSVs, processed parquets, and model artifacts will be versioned via DVC — never committed to Git." },
      { title: "Pre-commit pipeline", detail: "Configure hooks: ruff (linter), black (formatter), mypy (static types), and nbstripout (strips notebook outputs before commit). Run `pre-commit install`. This enforces code hygiene from day one." },
      { title: "Makefile targets", detail: "Define: `make data` (runs ingestion), `make features` (runs FE pipeline), `make train` (trains all models), `make eval` (generates evaluation report), `make all`. This is your project's CLI and CI entrypoint." }
    ]
  },
  {
    id: "P1", label: "P1 — Data Ingestion & Storage", color: "#ff6d00", duration: "Day 3–5",
    objective: "Build a deterministic, idempotent data pipeline that produces versioned, schema-validated datasets.",
    stack: ["football-data.co.uk (CSV)", "FBref / StatsBomb (scraping)", "Understat API", "API-Football (free tier)", "pandas", "pandera (schema validation)", "DuckDB"],
    steps: [
      { title: "Define data contract first", detail: "Before writing a single scraper, define a pandera DataFrameSchema for your raw ingestion layer. Columns: match_id, date, season, home_team, away_team, home_goals, away_goals, xg_home, xg_away, referee, matchweek. This schema is your ground truth — all sources must conform to it." },
      { title: "Source adapters (one per source)", detail: "Write a separate adapter class per source (FootballDataAdapter, FBrefAdapter, UnderstatAdapter). Each exposes a single `.fetch(season, league) -> pd.DataFrame` interface and maps raw columns to the canonical schema. Isolate scraping logic; never mix it with feature engineering." },
      { title: "Deduplication and merge strategy", detail: "Use match_id (constructed as `{date}_{home}_{away}_{league}`) as a surrogate key. When joining xG from Understat with results from football-data.co.uk, use a fuzzy name matcher (rapidfuzz) to handle team name inconsistencies. Log all unmatched rows." },
      { title: "Persist to DuckDB", detail: "Store the canonical match table in `data/processed/matches.duckdb`. DuckDB supports columnar storage and SQL queries without a server — ideal for fast feature queries at training time. Track the .duckdb file with DVC." },
      { title: "Validate and log", detail: "After every ingestion run, execute pandera validation. On schema failure, raise a `DataIngestionError` and halt the pipeline. Log row counts, null rates, and date ranges to `reports/ingestion_log.json`." }
    ]
  },
  {
    id: "P2", label: "P2 — Feature Engineering", color: "#76ff03", duration: "Day 6–9",
    objective: "Transform raw match data into ML-ready, leakage-free feature vectors.",
    stack: ["pandas", "numpy", "scikit-learn Pipelines", "Custom rolling window transforms", "Feature Store (parquet partitions)"],
    steps: [
      { title: "Temporal split discipline — enforce from the start", detail: "Sort all data by date. Never compute rolling features using future matches. Use `.shift(1)` before `.rolling(N)` to ensure only past matches inform each row. This is the most common source of data leakage in sports ML — treat it as a hard invariant." },
      { title: "Form features (rolling window)", detail: "Compute separately for home and away: rolling_wins_5, rolling_goals_scored_5, rolling_goals_conceded_5, rolling_xg_for_5, rolling_xg_against_5, rolling_points_5. Use windows of 5 and 10 games. Compute venue-specific form (home-only, away-only) as separate columns." },
      { title: "Head-to-head (H2H) aggregates", detail: "For each match, look back at all prior meetings between the two teams. Compute: h2h_home_win_rate, h2h_avg_goals, h2h_last_result (one-hot). Limit to last 5 meetings if history is sparse (<3 games)." },
      { title: "Contextual features", detail: "rest_days_home/away (fatigue signal), matchweek (seasonality), is_derby (pre-encoded rivalries), league_position_diff (rank delta at time of match), promoted_team_flag (newly promoted sides behave differently)." },
      { title: "Feature store as versioned parquet", detail: "Write to `data/features/features_v{N}.parquet`, partitioned by season. Version N increments when the feature schema changes. This decouples feature engineering from model training." },
      { title: "Correlation & VIF analysis", detail: "Compute Pearson correlation matrix and Variance Inflation Factor (VIF) for all numeric features. Drop features with VIF > 10. Log the feature manifest (name, dtype, VIF, null rate) to `reports/feature_report.csv`." }
    ]
  },
  {
    id: "P3", label: "P3 — Model Training & Tuning", color: "#e040fb", duration: "Day 10–15",
    objective: "Train a stacked ensemble with rigorous time-series cross-validation and hyperparameter optimisation.",
    stack: ["scikit-learn (Logistic Regression, stacking meta-learner)", "XGBoost", "LightGBM", "PyTorch (MLP)", "Optuna (HPO)", "TimeSeriesSplit (CV)", "MLflow"],
    steps: [
      { title: "Cross-validation: TimeSeriesSplit, not KFold", detail: "Use sklearn's TimeSeriesSplit with n_splits=5. Each fold trains on all past seasons and validates on the next chronological block. Never shuffle. Record OOF predictions for every model — these become the meta-learner's training data." },
      { title: "Layer 1 — Base learners", detail: "Train three base models: (1) LogisticRegression with L2 regularisation. (2) XGBClassifier — primary workhorse, handles missing values natively. (3) LGBMClassifier — faster, comparable to XGB, serves as a diversity source. Each outputs class probabilities [P(H), P(D), P(A)] — 9 features total for Layer 2." },
      { title: "Hyperparameter optimisation with Optuna", detail: "Define an Optuna study per base model. Optimise log-loss on OOF predictions. XGB search space: max_depth [3-8], learning_rate [0.01-0.3], subsample [0.6-1.0], colsample_bytree [0.5-1.0], n_estimators [100-1000]. Use MedianPruner. Run 100 trials per model." },
      { title: "Layer 2 — Meta-learner", detail: "Train a LogisticRegression (C=0.1, max_iter=1000) on the 9-dimensional OOF probability vectors from Layer 1. Keep it simple — a complex meta-learner risks overfitting to the base model errors." },
      { title: "Optional Layer 3 — MLP", detail: "If dataset has >10k matches, add a PyTorch MLP (3 hidden layers: [128, 64, 32], ReLU, Dropout 0.3, BatchNorm, softmax output). Use Adam, lr=1e-3, early stopping on val log-loss with patience=10." },
      { title: "Experiment tracking with MLflow", detail: "Log every run: params, metrics (log-loss, F1, ROC-AUC per class), artefacts (feature importance plot, calibration curve). Tag runs with model name, feature version, and date." }
    ]
  },
  {
    id: "P4", label: "P4 — Evaluation & Interpretability", color: "#ffd740", duration: "Day 16–18",
    objective: "Validate model quality, diagnose failure modes, and generate explainability artefacts.",
    stack: ["scikit-learn metrics", "SHAP", "matplotlib / seaborn", "reliability-diagram (calibration)", "MLflow"],
    steps: [
      { title: "Primary metric: Log Loss", detail: "Log-loss penalises confident wrong predictions. Target: beat the betting odds implied probability baseline (convert odds to probabilities, compute their log-loss as your ceiling). A model that beats closing odds is genuinely valuable." },
      { title: "Secondary metrics suite", detail: "Macro F1-score (balanced across W/D/L), ROC-AUC per class (one-vs-rest), Brier Score per class, Confusion matrix. Inspect draw prediction specifically — draws are systematically underpredicted by most models. Stratify all metrics by league, season, and home/away." },
      { title: "Calibration analysis", detail: "Plot reliability diagrams per class. A model's predicted P(home win)=0.6 should correspond to 60% empirical win rate in that bin. Use sklearn's `calibration_curve`. If poorly calibrated, apply Platt Scaling or Isotonic Regression post-hoc." },
      { title: "SHAP global and local explanations", detail: "Compute SHAP values on the test set for XGBoost. Generate: (1) Summary beeswarm plot — global feature importance. (2) Dependence plot for rolling_xg_for_5. (3) Waterfall plot for 3 representative match predictions." },
      { title: "Failure mode analysis", detail: "Filter predictions where model was most wrong (high log-loss per match). Look for systematic patterns: upsets involving promoted sides, post-international break matches, under 3 days rest. Document as known model limitations." }
    ]
  },
  {
    id: "P5", label: "P5 — Serving & Demo Interface", color: "#ff4081", duration: "Day 19–21",
    objective: "Package the model into a reproducible, demo-ready prediction interface.",
    stack: ["FastAPI (prediction endpoint)", "Streamlit (demo UI)", "joblib / ONNX (model serialisation)", "Docker", "GitHub Actions (CI)"],
    steps: [
      { title: "Model serialisation", detail: "Serialise the full stacking pipeline (preprocessor + base models + meta-learner) with joblib. Save to `models/ensemble_v{N}.pkl`. Track with DVC. Never load a model without verifying its DVC hash." },
      { title: "FastAPI inference endpoint", detail: "Expose POST /predict accepting: home_team, away_team, matchweek, league, date. Handler fetches latest rolling stats from DuckDB, constructs feature vector, runs inference, returns {home_win: float, draw: float, away_win: float, confidence: str}. Add input validation via Pydantic models." },
      { title: "Streamlit demo dashboard", detail: "Single-page Streamlit app: team selector dropdowns, predicted probabilities as horizontal bar chart, top 5 SHAP features driving the prediction, recent form table for both teams. Keep it fast (under 2s response)." },
      { title: "Containerise with Docker", detail: "Multi-stage Dockerfile: builder stage installs deps, runtime stage copies only what is needed. Expose port 8501 (Streamlit). Use docker-compose to run both FastAPI and Streamlit together with `docker compose up`." },
      { title: "GitHub Actions CI pipeline", detail: "On every push to main: run pytest (unit tests for feature functions and schema validation), run ruff + mypy, build Docker image. Prevents regressions and signals professional engineering practice." }
    ]
  }
];

const stackLayers = [
  { layer: "Data Ingestion", tools: ["football-data.co.uk", "FBref / StatsBomb", "Understat", "API-Football"], color: "#00e5ff" },
  { layer: "Storage", tools: ["DuckDB", "Parquet (Feature Store)", "DVC (versioning)"], color: "#ff6d00" },
  { layer: "Feature Engineering", tools: ["pandas", "numpy", "scikit-learn Pipelines", "pandera"], color: "#76ff03" },
  { layer: "Model Training", tools: ["XGBoost", "LightGBM", "scikit-learn", "PyTorch", "Optuna"], color: "#e040fb" },
  { layer: "Evaluation", tools: ["SHAP", "sklearn metrics", "MLflow", "matplotlib"], color: "#ffd740" },
  { layer: "Serving / Demo", tools: ["FastAPI", "Streamlit", "Docker", "GitHub Actions"], color: "#ff4081" },
];

const dataSources = [
  {
    name: "football-data.co.uk",
    tag: "FREE · No auth",
    color: "#00e5ff",
    type: "Direct CSV Download",
    what: "Historical match results, half-time scores, shots, fouls, cards, and 20+ betting odds columns from major European leagues (EPL, La Liga, Serie A, Bundesliga, Ligue 1) going back to 1993.",
    howTo: [
      "Visit football-data.co.uk/data.php — no signup required.",
      "Navigate to the league and season you need (e.g. Premier League 2023/24).",
      "Download the .csv file directly. File naming pattern: E0.csv (EPL), SP1.csv (La Liga), I1.csv (Serie A), D1.csv (Bundesliga), F1.csv (Ligue 1).",
      "Automate with Python requests: pd.read_csv('https://www.football-data.co.uk/mmz4281/2324/E0.csv'). Replace '2324' with the season code.",
      "Key columns to extract: Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR, HS, AS, HST, AST, B365H, B365D, B365A (Bet365 odds)."
    ],
    caveats: "Team names are inconsistent across seasons (e.g. 'Man United' vs 'Manchester United'). Use rapidfuzz for normalisation. Odds columns have many nulls for older seasons.",
    code: `import pandas as pd

def fetch_football_data(season: str, league: str = "E0") -> pd.DataFrame:
    # season format: "2324" for 2023/24
    url = f"https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
    df = pd.read_csv(url, encoding="latin-1")
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    return df`
  },
  {
    name: "Understat",
    tag: "FREE · No auth · Scraping",
    color: "#ff6d00",
    type: "JSON scraping via understatapi",
    what: "Match-level and shot-level xG (expected goals) data for EPL, La Liga, Bundesliga, Serie A, Ligue 1, and RFPL from 2014/15 onwards. Best free source for xG.",
    howTo: [
      "Install the Python wrapper: pip install understatapi",
      "No API key or login needed — the library scrapes Understat's embedded JSON.",
      "Use UnderstatClient to fetch league fixtures and xG per match.",
      "Data includes: xG home, xG away, deep passes, PPDA (pressing intensity), and shot-by-shot detail.",
      "Rate-limit your requests — add time.sleep(1) between calls to avoid being blocked."
    ],
    caveats: "Scraping-based — Understat can change its page structure. Pin the understatapi version. Coverage starts 2014/15 only. No cup competitions.",
    code: `import asyncio
from understatapi import UnderstatClient

async def fetch_understat_xg(league: str, season: str):
    # league: "EPL", "La liga", "Bundesliga", "Serie A", "Ligue 1"
    async with UnderstatClient() as client:
        matches = await client.league(league=league).get_match_data(season=season)
    return matches  # list of match dicts with xG fields`
  },
  {
    name: "FBref / StatsBomb",
    tag: "FREE · No auth · Scraping",
    color: "#76ff03",
    type: "Web scraping via soccerdata / mplsoccer",
    what: "Advanced stats: progressive passes, pressures, shot-creating actions, xA (expected assists), defensive actions, and full squad-level aggregates. Most comprehensive free advanced stats source.",
    howTo: [
      "Install soccerdata: pip install soccerdata. This wraps FBref scraping cleanly.",
      "No API key needed. FBref is powered by StatsBomb open data.",
      "Use soccerdata.FBref(leagues='ENG-Premier League', seasons='2023-2024') to initialise.",
      "Call .read_schedule() for fixtures, .read_team_match_stats() for per-match team stats.",
      "FBref enforces a rate limit — soccerdata handles caching automatically in ~/.cache/soccerdata/",
      "Alternatively, use the StatsBomb open-data GitHub repo for free detailed shot data: github.com/statsbomb/open-data"
    ],
    caveats: "FBref scraping is slow (1-2s per page). Run ingestion overnight for large backfills. Cache aggressively. Column names contain HTML artefacts — clean with str.strip().",
    code: `import soccerdata as sd

def fetch_fbref_stats(league: str = "ENG-Premier League", season: str = "2023-2024"):
    fbref = sd.FBref(leagues=league, seasons=season)
    schedule = fbref.read_schedule()
    team_stats = fbref.read_team_match_stats(stat_type="standard")
    return schedule, team_stats`
  },
  {
    name: "API-Football",
    tag: "FREE TIER · API key required",
    color: "#e040fb",
    type: "REST API (RapidAPI)",
    what: "Live scores, fixtures, standings, player stats, injuries, and head-to-head data. Free tier gives 100 requests/day covering most historical and live data needs.",
    howTo: [
      "Go to rapidapi.com and search 'API-Football' (by api-sports.io).",
      "Click Subscribe and select the Basic (free) plan — 100 req/day.",
      "Copy your RapidAPI key from the dashboard.",
      "Store it in your .env file as RAPIDAPI_KEY=your_key_here. Never hardcode it.",
      "Load it in Python with python-dotenv: from dotenv import load_dotenv; load_dotenv()",
      "Base URL: https://api-football-v1.p.rapidapi.com/v3/ — Key endpoints: /fixtures, /standings, /teams/statistics, /injuries"
    ],
    caveats: "100 req/day is tight for large backscrapes — use football-data.co.uk for historical bulk data and API-Football only for recent fixtures and live data. Cache all responses to disk.",
    code: `import os, requests
from dotenv import load_dotenv

load_dotenv()

def fetch_fixtures(league_id: int, season: int):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    params = {"league": league_id, "season": season}
    r = requests.get(url, headers=headers, params=params)
    return r.json()["response"]`
  }
];

const contextFiles = [
  {
    name: ".env.example",
    icon: "🔐",
    color: "#ff4081",
    description: "Environment variable template. Copy to .env and fill values. Never commit .env to Git.",
    content: `# ── API Keys ──────────────────────────────────────
RAPIDAPI_KEY=your_rapidapi_key_here
MLFLOW_TRACKING_URI=http://localhost:5000

# ── DVC Remote (choose one) ───────────────────────
DVC_REMOTE_URL=gdrive://your_gdrive_folder_id
# DVC_REMOTE_URL=s3://your-bucket/dvc-store

# ── Database ──────────────────────────────────────
DUCKDB_PATH=data/processed/matches.duckdb

# ── Project ───────────────────────────────────────
PROJECT_NAME=pitchiq
ENVIRONMENT=development   # development | staging | production
LOG_LEVEL=INFO`
  },
  {
    name: "pyproject.toml",
    icon: "📦",
    color: "#00e5ff",
    description: "Single source of truth for dependencies, linting config, and tool settings.",
    content: `[tool.poetry]
name = "pitchiq"
version = "0.1.0"
description = "Football match outcome prediction engine"
python = "^3.11"

[tool.poetry.dependencies]
pandas = "^2.2"
numpy = "^1.26"
scikit-learn = "^1.4"
xgboost = "^2.0"
lightgbm = "^4.3"
torch = "^2.2"
shap = "^0.44"
optuna = "^3.5"
duckdb = "^0.10"
pandera = "^0.18"
understatapi = "^0.10"
soccerdata = "^1.5"
rapidfuzz = "^3.6"
python-dotenv = "^1.0"
mlflow = "^2.10"
fastapi = "^0.110"
streamlit = "^1.32"
uvicorn = "^0.28"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
black = "^24.0"
ruff = "^0.3"
mypy = "^1.8"
nbstripout = "^0.7"
pre-commit = "^3.6"

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N"]

[tool.mypy]
python_version = "3.11"
strict = true`
  },
  {
    name: "configs/sources.yaml",
    icon: "⚙️",
    color: "#76ff03",
    description: "Declarative data source config. Add leagues/seasons here without touching code.",
    content: `# Data source configuration for PitchIQ ingestion pipeline

sources:
  football_data:
    enabled: true
    base_url: "https://www.football-data.co.uk/mmz4281"
    leagues:
      EPL:        { code: "E0",  seasons: ["2122","2223","2324"] }
      LaLiga:     { code: "SP1", seasons: ["2122","2223","2324"] }
      SerieA:     { code: "I1",  seasons: ["2122","2223","2324"] }
      Bundesliga: { code: "D1",  seasons: ["2122","2223","2324"] }
      Ligue1:     { code: "F1",  seasons: ["2122","2223","2324"] }

  understat:
    enabled: true
    leagues: ["EPL", "La liga", "Bundesliga", "Serie A", "Ligue 1"]
    seasons: ["2021", "2022", "2023"]  # Understat uses start year

  fbref:
    enabled: true
    leagues: ["ENG-Premier League", "ESP-La Liga"]
    seasons: ["2022-2023", "2023-2024"]
    cache_dir: "~/.cache/soccerdata"

  api_football:
    enabled: true
    leagues:
      EPL:        { id: 39,  season: 2023 }
      LaLiga:     { id: 140, season: 2023 }
      Bundesliga: { id: 78,  season: 2023 }
    use_for: ["live_fixtures", "injuries", "h2h"]`
  },
  {
    name: "configs/model.yaml",
    icon: "🧠",
    color: "#e040fb",
    description: "Model hyperparameter defaults. Optuna overwrites these at tuning time.",
    content: `# Model training configuration for PitchIQ

training:
  target: "FTR"               # Full Time Result: H / D / A
  test_season: "2023-2024"    # Hold-out — never touch during training
  cv_splits: 5                # TimeSeriesSplit n_splits
  random_seed: 42
  feature_version: "v1"

models:
  logistic_regression:
    C: 0.1
    max_iter: 1000
    class_weight: "balanced"
    solver: "lbfgs"
    multi_class: "multinomial"

  xgboost:
    n_estimators: 500
    max_depth: 5
    learning_rate: 0.05
    subsample: 0.8
    colsample_bytree: 0.7
    eval_metric: "mlogloss"
    early_stopping_rounds: 50

  lightgbm:
    n_estimators: 500
    max_depth: 6
    learning_rate: 0.05
    num_leaves: 63
    subsample: 0.8
    colsample_bytree: 0.7
    metric: "multi_logloss"

  meta_learner:
    type: "logistic_regression"
    C: 0.05
    max_iter: 1000

optuna:
  n_trials: 100
  direction: "minimize"
  pruner: "MedianPruner"
  storage: "sqlite:///models/optuna.db"`
  },
  {
    name: "configs/features.yaml",
    icon: "🔧",
    color: "#ffd740",
    description: "Feature engineering config. Control window sizes, active features, and VIF thresholds.",
    content: `# Feature engineering configuration
version: "v1"

rolling_windows:
  short: 5
  long: 10
  venue_split: true   # Compute home-only and away-only form separately

features:
  form:
    - rolling_wins_{w}
    - rolling_goals_scored_{w}
    - rolling_goals_conceded_{w}
    - rolling_xg_for_{w}        # Requires Understat
    - rolling_xg_against_{w}
    - rolling_points_{w}
    - rolling_clean_sheets_{w}

  head_to_head:
    - h2h_home_win_rate
    - h2h_avg_goals
    - h2h_last_result           # one-hot encoded
    max_meetings: 5

  contextual:
    - rest_days_home
    - rest_days_away
    - matchweek
    - league_position_diff
    - is_home
    - is_derby
    - promoted_team_home
    - promoted_team_away

quality:
  vif_threshold: 10
  min_null_rate_drop: 0.4
  corr_threshold: 0.95`
  },
  {
    name: "Makefile",
    icon: "⚡",
    color: "#ff6d00",
    description: "Project CLI. All pipeline stages are driven through make targets.",
    content: `.PHONY: install data features train eval serve test lint all

install:
	poetry install
	pre-commit install
	dvc pull

data:
	python src/ingestion/run_ingestion.py

features:
	python src/features/build_features.py

train:
	python src/training/train.py

eval:
	python src/evaluation/evaluate.py

serve-api:
	uvicorn src.api.main:app --reload --port 8000

serve-ui:
	streamlit run src/dashboard/app.py --server.port 8501

test:
	pytest tests/ -v --tb=short

lint:
	ruff check src/ && mypy src/

all: data features train eval

docker-up:
	docker compose up --build

docker-down:
	docker compose down`
  },
  {
    name: ".pre-commit-config.yaml",
    icon: "🔍",
    color: "#00e5ff",
    description: "Pre-commit hooks that run automatically before every git commit.",
    content: `repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/psf/black
    rev: 24.2.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, pandas-stubs]

  - repo: https://github.com/kynan/nbstripout
    rev: 0.7.1
    hooks:
      - id: nbstripout

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-merge-conflict
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace`
  },
  {
    name: "docker-compose.yml",
    icon: "🐳",
    color: "#ff4081",
    description: "One-command startup for the full serving stack — API backend + Streamlit demo UI.",
    content: `version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: api
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
      - ./data:/app/data
    env_file: .env
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dashboard:
    build:
      context: .
      dockerfile: Dockerfile
      target: dashboard
    ports:
      - "8501:8501"
    depends_on:
      api:
        condition: service_healthy
    env_file: .env
    environment:
      - API_URL=http://api:8000
    command: streamlit run src/dashboard/app.py --server.port 8501 --server.address 0.0.0.0

  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.10.0
    ports:
      - "5000:5000"
    volumes:
      - ./mlruns:/mlruns
    command: mlflow server --host 0.0.0.0 --port 5000`
  }
];

export default function ProjectPlan() {
  const [activePhase, setActivePhase] = useState(null);
  const [activeStep, setActiveStep] = useState(null);
  const [activeTab, setActiveTab] = useState("phases");
  const [activeSource, setActiveSource] = useState(null);
  const [activeFile, setActiveFile] = useState(null);
  const [copiedFile, setCopiedFile] = useState(null);

  const handleCopy = (content, name) => {
    navigator.clipboard.writeText(content);
    setCopiedFile(name);
    setTimeout(() => setCopiedFile(null), 1800);
  };

  return (
    <div style={{
      fontFamily: "'IBM Plex Mono', 'Courier New', monospace",
      background: "#080c10",
      color: "#c8d6e5",
      minHeight: "100vh",
      padding: "32px 24px",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600;700&family=Syne:wght@700;800&display=swap');
        * { box-sizing: border-box; }
        .phase-card { cursor: pointer; transition: border-color 0.2s; border: 1px solid #1a2332; background: #0d1521; border-radius: 6px; margin-bottom: 10px; overflow: hidden; }
        .phase-card:hover { border-color: #2a3f5f; }
        .phase-card.active { border-color: var(--accent); }
        .phase-header { display: flex; align-items: center; gap: 12px; padding: 13px 18px; }
        .phase-body { padding: 0 18px 18px; display: none; }
        .phase-body.open { display: block; }
        .step-item { border-left: 2px solid #1a2332; margin-left: 8px; padding: 10px 14px; margin-bottom: 6px; cursor: pointer; border-radius: 0 4px 4px 0; transition: all 0.15s; }
        .step-item:hover, .step-item.open { border-left-color: var(--accent); background: #0a1220; }
        .step-detail { font-size: 12px; color: #8a9bb0; line-height: 1.7; margin-top: 8px; display: none; }
        .step-detail.show { display: block; }
        .pill { display: inline-block; background: #0f1e2e; border: 1px solid #1e3048; border-radius: 3px; padding: 2px 8px; font-size: 10px; color: #6a8caa; margin: 2px; }
        .badge { display: inline-block; border-radius: 3px; padding: 2px 8px; font-size: 10px; font-weight: 600; }
        .stack-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(195px, 1fr)); gap: 10px; margin: 16px 0; }
        .stack-card { background: #0d1521; border: 1px solid #1a2332; border-radius: 6px; padding: 14px; }
        .divider { border: none; border-top: 1px solid #1a2332; margin: 24px 0; }
        .tag-row { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
        .chevron { transition: transform 0.2s; display: inline-block; margin-left: auto; font-size: 10px; color: #3a5070; }
        .chevron.open { transform: rotate(90deg); }
        .tab-btn { padding: 7px 16px; font-size: 10px; font-family: 'IBM Plex Mono', monospace; font-weight: 600; letter-spacing: 0.08em; border: 1px solid #1a2332; border-radius: 4px; cursor: pointer; background: transparent; color: #3a6090; transition: all 0.15s; }
        .tab-btn.active { background: #0d1521; border-color: #2a4a6a; color: #c8d6e5; }
        .tab-btn:hover { border-color: #2a4a6a; color: #a0b8d0; }
        .source-card { border: 1px solid #1a2332; border-radius: 6px; margin-bottom: 10px; overflow: hidden; background: #0d1521; cursor: pointer; transition: border-color 0.2s; }
        .source-card:hover { border-color: #2a3f5f; }
        .source-card.open { border-color: var(--accent); }
        .source-header { padding: 14px 18px; display: flex; align-items: center; gap: 12px; }
        .source-body { display: none; padding: 0 18px 18px; }
        .source-body.open { display: block; }
        .how-step { display: flex; gap: 10px; margin-bottom: 8px; align-items: flex-start; }
        .how-num { min-width: 20px; height: 20px; border-radius: 3px; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: 700; margin-top: 1px; flex-shrink: 0; }
        .code-block { background: #040810; border: 1px solid #1a2332; border-radius: 4px; padding: 14px; font-size: 11px; line-height: 1.7; color: #7ab8e0; overflow-x: auto; margin-top: 12px; }
        .caveat-box { background: #1a0d0a; border: 1px solid #3a1a12; border-radius: 4px; padding: 10px 14px; font-size: 11px; color: #9a6050; line-height: 1.6; margin-top: 10px; }
        .file-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(175px, 1fr)); gap: 10px; margin: 16px 0; }
        .file-card { border: 1px solid #1a2332; border-radius: 6px; padding: 14px; background: #0d1521; cursor: pointer; transition: border-color 0.2s; }
        .file-card:hover, .file-card.open { border-color: var(--accent); }
        .file-viewer { background: #040810; border: 1px solid #1a2332; border-radius: 6px; margin-top: 16px; overflow: hidden; }
        .file-viewer-header { padding: 10px 16px; border-bottom: 1px solid #1a2332; display: flex; align-items: center; justify-content: space-between; }
        .copy-btn { font-size: 10px; padding: 4px 10px; border: 1px solid #1e3048; border-radius: 3px; background: transparent; color: #5a8ab0; cursor: pointer; font-family: 'IBM Plex Mono', monospace; transition: all 0.15s; }
        .copy-btn:hover { background: #0f1e2e; color: #90c0e0; }
        .copy-btn.copied { border-color: #76ff03; color: #76ff03; }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 10, letterSpacing: "0.15em", color: "#2a5070", marginBottom: 8 }}>
          FOOTBALL INTELLIGENCE SYSTEM · UNIVERSITY ML RESEARCH PROJECT
        </div>
        <h1 style={{
          fontFamily: "'Syne', sans-serif",
          fontSize: 30, fontWeight: 800, margin: 0,
          background: "linear-gradient(120deg, #00e5ff 0%, #7ab8ff 50%, #e040fb 100%)",
          WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          letterSpacing: "-0.03em"
        }}>
          PitchIQ — Match Prediction Engine
        </h1>
        <p style={{ fontSize: 12, color: "#4a6080", marginTop: 8, lineHeight: 1.6, maxWidth: 620 }}>
          End-to-end ML system for football match outcome prediction · Stacked ensemble architecture · 6 phases · 21-day implementation plan
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
        {[["phases","IMPLEMENTATION PHASES"],["ingestion","DATA INGESTION GUIDE"],["context","CONTEXT FILES"]].map(([id, label]) => (
          <button key={id} className={`tab-btn ${activeTab === id ? "active" : ""}`} onClick={() => setActiveTab(id)}>{label}</button>
        ))}
      </div>

      {/* ── PHASES TAB ── */}
      {activeTab === "phases" && (
        <>
          <div style={{ fontSize: 10, letterSpacing: "0.12em", color: "#3a6090", marginBottom: 12 }}>FULL TECHNOLOGY STACK</div>
          <div className="stack-grid">
            {stackLayers.map(s => (
              <div className="stack-card" key={s.layer} style={{ borderTop: `2px solid ${s.color}` }}>
                <div style={{ fontSize: 10, fontWeight: 600, color: s.color, marginBottom: 8 }}>{s.layer.toUpperCase()}</div>
                <div className="tag-row">{s.tools.map(t => <span key={t} className="pill">{t}</span>)}</div>
              </div>
            ))}
          </div>
          <hr className="divider" />
          <div style={{ fontSize: 10, letterSpacing: "0.12em", color: "#3a6090", marginBottom: 12 }}>IMPLEMENTATION PHASES · CLICK TO EXPAND</div>
          {phases.map((phase, pi) => {
            const isActive = activePhase === pi;
            return (
              <div className={`phase-card ${isActive ? "active" : ""}`} key={phase.id} style={{ "--accent": phase.color }}>
                <div className="phase-header" onClick={() => { setActivePhase(isActive ? null : pi); setActiveStep(null); }}>
                  <span className="badge" style={{ background: phase.color + "18", color: phase.color, border: `1px solid ${phase.color}44` }}>{phase.id}</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: "#c8d6e5", flex: 1 }}>{phase.label}</span>
                  <span style={{ fontSize: 10, color: "#3a5070", marginRight: 12 }}>{phase.duration}</span>
                  <span className={`chevron ${isActive ? "open" : ""}`}>▶</span>
                </div>
                <div className={`phase-body ${isActive ? "open" : ""}`}>
                  <p style={{ fontSize: 11, color: "#5a7a9a", margin: "0 0 12px", lineHeight: 1.6 }}>
                    <span style={{ color: "#3a6090" }}>OBJECTIVE: </span>{phase.objective}
                  </p>
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 10, color: "#2a4a6a", marginBottom: 6 }}>STACK FOR THIS PHASE</div>
                    <div className="tag-row">{phase.stack.map(t => <span key={t} className="pill" style={{ borderColor: phase.color + "33", color: "#8aabcc" }}>{t}</span>)}</div>
                  </div>
                  <div style={{ fontSize: 10, color: "#2a4a6a", marginBottom: 8 }}>IMPLEMENTATION STEPS</div>
                  {phase.steps.map((step, si) => {
                    const stepKey = `${pi}-${si}`;
                    const isStepOpen = activeStep === stepKey;
                    return (
                      <div key={si} className={`step-item ${isStepOpen ? "open" : ""}`} style={{ "--accent": phase.color }} onClick={() => setActiveStep(isStepOpen ? null : stepKey)}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span style={{ fontSize: 10, color: phase.color, minWidth: 20 }}>{String(si + 1).padStart(2, "0")}</span>
                          <span style={{ fontSize: 12, color: "#b0c8e0", fontWeight: 600 }}>{step.title}</span>
                          <span className={`chevron ${isStepOpen ? "open" : ""}`} style={{ marginLeft: "auto" }}>▶</span>
                        </div>
                        <div className={`step-detail ${isStepOpen ? "show" : ""}`}>{step.detail}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
          <hr className="divider" />
          <div style={{ fontSize: 10, letterSpacing: "0.12em", color: "#3a6090", marginBottom: 12 }}>ENGINEERING PRINCIPLES · NON-NEGOTIABLE</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(255px, 1fr))", gap: 10 }}>
            {[
              { icon: "⛔", title: "No Data Leakage", body: "All rolling features use .shift(1). TimeSeriesSplit only. Future data never touches training." },
              { icon: "🔒", title: "Reproducibility", body: "Every run is seeded. DVC tracks data + models. Any experiment must be replayable from a commit hash." },
              { icon: "📐", title: "Schema-First", body: "Define pandera schemas before writing code. Validation runs on every pipeline stage." },
              { icon: "📊", title: "Beat the Baseline", body: "Betting odds implied probabilities are your real benchmark, not accuracy on a random split." },
              { icon: "🔍", title: "Explain Predictions", body: "SHAP values are not optional. A model your group can't interpret won't be trusted." },
              { icon: "🧪", title: "Test the Pipeline", body: "Unit test feature functions, not just models. A bug in rolling windows corrupts everything downstream." },
            ].map(p => (
              <div key={p.title} style={{ background: "#0d1521", border: "1px solid #1a2332", borderRadius: 6, padding: "14px 16px" }}>
                <div style={{ fontSize: 16, marginBottom: 6 }}>{p.icon}</div>
                <div style={{ fontSize: 11, fontWeight: 600, color: "#c8d6e5", marginBottom: 4 }}>{p.title}</div>
                <div style={{ fontSize: 11, color: "#4a6a8a", lineHeight: 1.6 }}>{p.body}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ── INGESTION TAB ── */}
      {activeTab === "ingestion" && (
        <>
          <div style={{ fontSize: 11, color: "#4a6a8a", marginBottom: 20, lineHeight: 1.7, maxWidth: 680 }}>
            Four data sources feed PitchIQ. Use them in combination — football-data.co.uk for bulk historical results, Understat for xG, FBref for advanced stats, and API-Football for live and recent data.
          </div>
          {dataSources.map((src, i) => {
            const isOpen = activeSource === i;
            return (
              <div key={src.name} className={`source-card ${isOpen ? "open" : ""}`} style={{ "--accent": src.color }}>
                <div className="source-header" onClick={() => setActiveSource(isOpen ? null : i)}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: src.color, flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: "#e0eaff" }}>{src.name}</div>
                    <div style={{ fontSize: 10, color: "#3a6080", marginTop: 2 }}>{src.type}</div>
                  </div>
                  <span className="badge" style={{ background: src.color + "15", color: src.color, border: `1px solid ${src.color}40`, fontSize: 9 }}>{src.tag}</span>
                  <span className={`chevron ${isOpen ? "open" : ""}`} style={{ marginLeft: 10 }}>▶</span>
                </div>
                <div className={`source-body ${isOpen ? "open" : ""}`}>
                  <p style={{ fontSize: 12, color: "#7a9ab8", lineHeight: 1.7, margin: "0 0 16px" }}>{src.what}</p>
                  <div style={{ fontSize: 10, color: src.color, letterSpacing: "0.1em", marginBottom: 10 }}>HOW TO ACCESS</div>
                  {src.howTo.map((step, si) => (
                    <div key={si} className="how-step">
                      <span className="how-num" style={{ background: src.color + "20", color: src.color }}>{si + 1}</span>
                      <span style={{ fontSize: 12, color: "#8aacc8", lineHeight: 1.6 }}>{step}</span>
                    </div>
                  ))}
                  <div className="caveat-box">
                    <span style={{ color: "#c06040", fontWeight: 600 }}>CAVEATS: </span>{src.caveats}
                  </div>
                  <div style={{ fontSize: 10, color: src.color, letterSpacing: "0.1em", margin: "14px 0 0" }}>STARTER CODE</div>
                  <div className="code-block">
                    <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{src.code}</pre>
                  </div>
                </div>
              </div>
            );
          })}
          <div style={{ marginTop: 20, background: "#0d1521", border: "1px solid #1a2332", borderRadius: 6, padding: "16px 18px" }}>
            <div style={{ fontSize: 10, color: "#3a6090", letterSpacing: "0.1em", marginBottom: 12 }}>RECOMMENDED INGESTION ORDER</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
              {[["football-data.co.uk","bulk history"],["Understat","xG data"],["FBref","advanced stats"],["API-Football","live / recent"]].map(([name, sub], i, arr) => (
                <div key={name} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ background: "#040810", border: "1px solid #1e3048", borderRadius: 4, padding: "8px 14px", fontSize: 11, color: "#7a9ab8", textAlign: "center" }}>
                    <div style={{ fontWeight: 600 }}>{name}</div>
                    <div style={{ fontSize: 9, color: "#3a5570", marginTop: 2 }}>{sub}</div>
                  </div>
                  {i < arr.length - 1 && <span style={{ color: "#2a4a6a", fontSize: 16 }}>→</span>}
                </div>
              ))}
            </div>
            <p style={{ fontSize: 11, color: "#3a5570", marginTop: 14, lineHeight: 1.6 }}>
              Run football-data.co.uk first to build the canonical match index. Enrich each match_id with xG from Understat, advanced stats from FBref, then pull recent fixtures from API-Football last to conserve the rate limit.
            </p>
          </div>
        </>
      )}

      {/* ── CONTEXT FILES TAB ── */}
      {activeTab === "context" && (
        <>
          <div style={{ fontSize: 11, color: "#4a6a8a", marginBottom: 20, lineHeight: 1.7, maxWidth: 680 }}>
            These files define the project's configuration contract. Every collaborator clones the repo, copies <span style={{ color: "#7ab8e0" }}>.env.example</span> to <span style={{ color: "#7ab8e0" }}>.env</span>, fills in credentials, and runs <span style={{ color: "#7ab8e0" }}>make install</span>. Click a file to view its contents, then copy it directly.
          </div>
          <div className="file-grid">
            {contextFiles.map((f, i) => (
              <div
                key={f.name}
                className={`file-card ${activeFile === i ? "open" : ""}`}
                style={{ "--accent": f.color, borderTop: activeFile === i ? `2px solid ${f.color}` : "1px solid #1a2332" }}
                onClick={() => setActiveFile(activeFile === i ? null : i)}
              >
                <div style={{ fontSize: 20, marginBottom: 8 }}>{f.icon}</div>
                <div style={{ fontSize: 11, fontWeight: 700, color: "#c8d6e5", marginBottom: 4 }}>{f.name}</div>
                <div style={{ fontSize: 10, color: "#3a5570", lineHeight: 1.5 }}>{f.description}</div>
              </div>
            ))}
          </div>
          {activeFile !== null && (
            <div className="file-viewer">
              <div className="file-viewer-header">
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 16 }}>{contextFiles[activeFile].icon}</span>
                  <span style={{ fontSize: 12, fontWeight: 700, color: "#c8d6e5" }}>{contextFiles[activeFile].name}</span>
                </div>
                <button
                  className={`copy-btn ${copiedFile === contextFiles[activeFile].name ? "copied" : ""}`}
                  onClick={() => handleCopy(contextFiles[activeFile].content, contextFiles[activeFile].name)}
                >
                  {copiedFile === contextFiles[activeFile].name ? "✓ COPIED" : "COPY"}
                </button>
              </div>
              <div style={{ padding: "16px 20px", fontSize: 11, lineHeight: 1.75, color: "#7ab8e0", overflowX: "auto" }}>
                <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{contextFiles[activeFile].content}</pre>
              </div>
            </div>
          )}
        </>
      )}

      <div style={{ marginTop: 36, fontSize: 10, color: "#1a3050", textAlign: "center" }}>
        PITCHIQ · FOOTBALL MATCH PREDICTION ENGINE · ML SYSTEM DESIGN
      </div>
    </div>
  );
}
