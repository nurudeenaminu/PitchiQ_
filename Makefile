# PitchIQ Makefile
# Compatible with GnuWin32 make (winget install GnuWin32.Make)
# Install: winget install GnuWin32.Make
# Usage: make <target>

# On Windows with GnuWin32, set SHELL so commands resolve correctly
ifeq ($(OS),Windows_NT)
	SHELL = cmd.exe
	PYTHON = python
else
	PYTHON = python3
endif

.PHONY: install install-ml data features train eval serve-api serve-ui test lint all docker-up docker-down clean

## ── Setup ────────────────────────────────────────────────────────────────────
install:
	poetry install --no-root
	pre-commit install

install-ml:
	poetry install --no-root --extras ml
	pre-commit install

## ── Pipeline ─────────────────────────────────────────────────────────────────
data:
	$(PYTHON) -m src.ingestion.run_ingestion

features:
	$(PYTHON) -m src.features.build_features

train:
	$(PYTHON) -m src.training.train

eval:
	$(PYTHON) -m src.evaluation.evaluate

## ── Full pipeline ─────────────────────────────────────────────────────────────
all: data features train eval

## ── Serving ──────────────────────────────────────────────────────────────────
serve-api:
	uvicorn src.api.main:app --reload --port 8000

serve-ui:
	streamlit run src/dashboard/app.py --server.port 8501

## ── Quality ──────────────────────────────────────────────────────────────────
test:
	pytest tests/ -v --tb=short

lint:
	ruff check src/
	mypy src/

## ── Docker ───────────────────────────────────────────────────────────────────
docker-up:
	docker compose up --build

docker-down:
	docker compose down

## ── Clean ────────────────────────────────────────────────────────────────────
clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
