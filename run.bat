@echo off
REM PitchIQ - Windows CMD runner
REM Usage: run.bat <command>

if "%1"=="install"    goto install
if "%1"=="data"       goto data
if "%1"=="features"   goto features
if "%1"=="train"      goto train
if "%1"=="eval"       goto eval
if "%1"=="serve-api"  goto serve_api
if "%1"=="serve-ui"   goto serve_ui
if "%1"=="test"       goto test
if "%1"=="lint"       goto lint
if "%1"=="all"        goto all
if "%1"=="docker-up"  goto docker_up
if "%1"=="docker-down" goto docker_down
goto help

:install
poetry install && pre-commit install
goto end

:data
python -m src.ingestion.run_ingestion
goto end

:features
python -m src.features.build_features
goto end

:train
python -m src.training.train
goto end

:eval
python -m src.evaluation.evaluate
goto end

:serve_api
uvicorn src.api.main:app --reload --port 8000
goto end

:serve_ui
streamlit run src/dashboard/app.py --server.port 8501
goto end

:test
pytest tests/ -v --tb=short
goto end

:lint
ruff check src/ && mypy src/
goto end

:all
call run.bat data
call run.bat features
call run.bat train
call run.bat eval
goto end

:docker_up
docker compose up --build
goto end

:docker_down
docker compose down
goto end

:help
echo.
echo PitchIQ - Available commands:
echo   run.bat install      Install dependencies
echo   run.bat data         Run data ingestion
echo   run.bat features     Build feature store
echo   run.bat train        Train ensemble model
echo   run.bat eval         Run evaluation
echo   run.bat serve-api    Start FastAPI on :8000
echo   run.bat serve-ui     Start Streamlit on :8501
echo   run.bat test         Run tests
echo   run.bat lint         Run ruff + mypy
echo   run.bat all          Run full pipeline
echo   run.bat docker-up    Start all services via Docker
echo   run.bat docker-down  Stop Docker services
echo.

:end
