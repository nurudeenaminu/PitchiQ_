"""Backend API service for PitchIQ predictions."""
import os
import requests
from typing import Optional

API_URL = os.getenv("API_URL", os.getenv("PITCHIQ_API_URL", "http://localhost:8000")).rstrip("/")


def predict_match(home_team: str, away_team: str, league: str, matchweek: int, date: str) -> Optional[dict]:
    """Call the prediction endpoint and return probabilities + confidence."""
    try:
        payload = {
            "home_team": home_team,
            "away_team": away_team,
            "matchweek": matchweek,
            "league": league,
            "date": date,
        }
        response = requests.post(f"{API_URL}/v1/predict", json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def get_health() -> bool:
    """Check if API is healthy."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False
