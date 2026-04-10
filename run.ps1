# PitchIQ - Windows PowerShell runner
# Usage: .\run.ps1 <command>
# Example: .\run.ps1 docker-up

param([string]$Command = "help")

function Run-Install    { poetry install; pre-commit install }
function Run-Data       { python -m src.ingestion.run_ingestion }
function Run-Features   { python -m src.features.build_features }
function Run-Train      { python -m src.training.train }
function Run-Eval       { python -m src.evaluation.evaluate }
function Run-ServeApi   { uvicorn src.api.main:app --reload --port 8000 }
function Run-ServeUi    { streamlit run src/dashboard/app.py --server.port 8501 }
function Run-Test       { pytest tests/ -v --tb=short }
function Run-Lint       { ruff check src/; mypy src/ }
function Run-All        { Run-Data; Run-Features; Run-Train; Run-Eval }
function Run-DockerUp   { docker compose up --build }
function Run-DockerDown { docker compose down }
function Run-Help {
    Write-Host ""
    Write-Host "PitchIQ - Available commands:" -ForegroundColor Cyan
    Write-Host "  .\run.ps1 install      Install dependencies"
    Write-Host "  .\run.ps1 data         Run data ingestion"
    Write-Host "  .\run.ps1 features     Build feature store"
    Write-Host "  .\run.ps1 train        Train ensemble model"
    Write-Host "  .\run.ps1 eval         Run evaluation"
    Write-Host "  .\run.ps1 serve-api    Start FastAPI on :8000"
    Write-Host "  .\run.ps1 serve-ui     Start Streamlit on :8501"
    Write-Host "  .\run.ps1 test         Run tests"
    Write-Host "  .\run.ps1 lint         Run ruff + mypy"
    Write-Host "  .\run.ps1 all          Run full pipeline"
    Write-Host "  .\run.ps1 docker-up    Start all services via Docker"
    Write-Host "  .\run.ps1 docker-down  Stop Docker services"
    Write-Host ""
}

switch ($Command.ToLower()) {
    "install"    { Run-Install }
    "data"       { Run-Data }
    "features"   { Run-Features }
    "train"      { Run-Train }
    "eval"       { Run-Eval }
    "serve-api"  { Run-ServeApi }
    "serve-ui"   { Run-ServeUi }
    "test"       { Run-Test }
    "lint"       { Run-Lint }
    "all"        { Run-All }
    "docker-up"  { Run-DockerUp }
    "docker-down"{ Run-DockerDown }
    default      { Run-Help }
}
