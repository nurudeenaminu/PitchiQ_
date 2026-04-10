"""Real-time football data service using API-Football.

This module provides live data for:
- League standings
- Upcoming fixtures
- Live scores
- Top scorers
- Recent results

API-Football free tier: 100 requests/day
Docs: https://www.api-football.com/documentation-v3
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_PROJECT_ROOT / ".env")

# API Configuration
API_FOOTBALL_HOST = "v3.football.api-sports.io"
API_BASE_URL = f"https://{API_FOOTBALL_HOST}"


def get_api_key() -> str:
    """Get API key - reads fresh from environment each time."""
    return os.getenv("API_FOOTBALL_KEY", "")


# For backward compatibility
@property
def API_FOOTBALL_KEY() -> str:
    return get_api_key()


# League IDs for API-Football
LEAGUE_IDS = {
    "epl": 39,        # Premier League
    "laliga": 140,    # La Liga
    "bundesliga": 78, # Bundesliga
    "seriea": 135,    # Serie A
    "ligue1": 61,     # Ligue 1
    "ucl": 2,         # UEFA Champions League
}

def _current_api_season() -> int:
    """Return the API-Football season year for the current football season."""
    override = os.getenv("API_FOOTBALL_SEASON")
    if override:
        try:
            return int(override)
        except ValueError:
            pass

    today = datetime.now()
    return today.year if today.month >= 7 else today.year - 1


# Current season for API-Football (e.g. 2025 for the 2025/26 season)
CURRENT_SEASON = _current_api_season()


def _season_candidates() -> List[int]:
    """Return season candidates, prioritizing configured/current season first."""
    candidates: List[int] = [CURRENT_SEASON]

    fallback_env = os.getenv("API_FOOTBALL_FALLBACK_SEASONS", "2024,2023,2022")
    for raw in fallback_env.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            season = int(raw)
            if season not in candidates:
                candidates.append(season)
        except ValueError:
            continue

    return candidates


def _get_headers() -> Dict[str, str]:
    """Get API headers with authentication."""
    return {
        "x-apisports-key": get_api_key(),
        "x-rapidapi-host": API_FOOTBALL_HOST,
    }


def _api_request(endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
    """Make an API request with error handling."""
    if not get_api_key():
        return None
    
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(
                f"{API_BASE_URL}/{endpoint}",
                headers=_get_headers(),
                params=params or {},
            )
            if response.status_code == 200:
                data = response.json()
                return data
    except Exception:
        pass
    return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_standings(league_id: str) -> pd.DataFrame:
    """Fetch current league standings."""
    api_league_id = LEAGUE_IDS.get(league_id)
    if not api_league_id:
        return pd.DataFrame()

    for season in _season_candidates():
        data = _api_request("standings", {
            "league": api_league_id,
            "season": season,
        })

        if not data or not data.get("response"):
            continue

        try:
            standings = data["response"][0]["league"]["standings"][0]
            rows = []
            for team in standings:
                rows.append({
                    "position": team["rank"],
                    "team": team["team"]["name"],
                    "p": team["all"]["played"],
                    "w": team["all"]["win"],
                    "d": team["all"]["draw"],
                    "l": team["all"]["lose"],
                    "gf": team["all"]["goals"]["for"],
                    "ga": team["all"]["goals"]["against"],
                    "gd": team["goalsDiff"],
                    "pts": team["points"],
                    "form": team.get("form", ""),
                    "logo": team["team"].get("logo", ""),
                    "season": season,
                })
            return pd.DataFrame(rows)
        except (KeyError, IndexError, TypeError):
            continue

    return pd.DataFrame()


@st.cache_data(ttl=120)  # Cache for 2 minutes
def get_fixtures(league_id: str, status: str = "NS") -> pd.DataFrame:
    """Fetch fixtures for a league.
    
    Status codes:
    - NS: Not Started (upcoming)
    - LIVE: Live matches
    - FT: Finished
    - All statuses: TBD, NS, 1H, HT, 2H, ET, P, FT, AET, PEN, BT, SUSP, INT, PST, CANC, ABD, AWD, WO
    """
    api_league_id = LEAGUE_IDS.get(league_id)
    if not api_league_id:
        return pd.DataFrame()
    
    for season in _season_candidates():
        params = {
            "league": api_league_id,
            "season": season,
        }

        # Free plan restricts "next"; use status filtering instead.
        if status == "NS":
            params["status"] = "NS"
        elif status == "LIVE":
            params["live"] = "all"
        else:
            params["status"] = status

        data = _api_request("fixtures", params)

        if not data or not data.get("response"):
            continue

        try:
            rows = []
            for fixture in data["response"]:
                fixture_data = fixture["fixture"]
                teams = fixture["teams"]
                goals = fixture["goals"]

                rows.append({
                    "fixture_id": fixture_data["id"],
                    "date": fixture_data["date"],
                    "timestamp": fixture_data["timestamp"],
                    "venue": fixture_data.get("venue", {}).get("name", ""),
                    "status": fixture_data["status"]["short"],
                    "status_long": fixture_data["status"]["long"],
                    "elapsed": fixture_data["status"].get("elapsed"),
                    "home_team": teams["home"]["name"],
                    "home_logo": teams["home"].get("logo", ""),
                    "away_team": teams["away"]["name"],
                    "away_logo": teams["away"].get("logo", ""),
                    "home_goals": goals.get("home"),
                    "away_goals": goals.get("away"),
                    "league": league_id,
                    "matchweek": fixture.get("league", {}).get("round", ""),
                    "season": season,
                })

            df = pd.DataFrame(rows)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.dropna(subset=["date"]).sort_values("date")
                if status == "NS":
                    df = df.head(20)
                return df
        except (KeyError, IndexError, TypeError):
            continue

    return pd.DataFrame()


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_live_matches() -> pd.DataFrame:
    """Fetch all currently live matches across all leagues."""
    if not get_api_key():
        return pd.DataFrame()
    
    data = _api_request("fixtures", {"live": "all"})
    
    if not data or not data.get("response"):
        return pd.DataFrame()
    
    try:
        rows = []
        for fixture in data["response"]:
            fixture_data = fixture["fixture"]
            teams = fixture["teams"]
            goals = fixture["goals"]
            league = fixture["league"]
            
            rows.append({
                "fixture_id": fixture_data["id"],
                "league_name": league["name"],
                "league_logo": league["logo"],
                "home_team": teams["home"]["name"],
                "away_team": teams["away"]["name"],
                "home_goals": goals["home"] or 0,
                "away_goals": goals["away"] or 0,
                "elapsed": fixture_data["status"].get("elapsed", 0),
                "status": fixture_data["status"]["short"],
            })
        return pd.DataFrame(rows)
    except (KeyError, IndexError):
        return pd.DataFrame()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_top_scorers(league_id: str, limit: int = 10) -> pd.DataFrame:
    """Fetch top scorers for a league."""
    api_league_id = LEAGUE_IDS.get(league_id)
    if not api_league_id:
        return pd.DataFrame()
    
    for season in _season_candidates():
        data = _api_request("players/topscorers", {
            "league": api_league_id,
            "season": season,
        })

        if not data or not data.get("response"):
            continue

        try:
            rows = []
            for i, player_data in enumerate(data["response"][:limit], 1):
                player = player_data["player"]
                stats = player_data["statistics"][0]

                rows.append({
                    "rank": i,
                    "player": player["name"],
                    "photo": player.get("photo", ""),
                    "team": stats["team"]["name"],
                    "team_logo": stats["team"].get("logo", ""),
                    "goals": stats["goals"].get("total") or 0,
                    "assists": stats["goals"].get("assists") or 0,
                    "matches": stats["games"].get("appearences") or 0,
                    "season": season,
                })
            return pd.DataFrame(rows)
        except (KeyError, IndexError, TypeError):
            continue

    return pd.DataFrame()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_recent_results(league_id: str, limit: int = 10) -> pd.DataFrame:
    """Fetch recent match results for a league."""
    api_league_id = LEAGUE_IDS.get(league_id)
    if not api_league_id:
        return pd.DataFrame()
    
    for season in _season_candidates():
        data = _api_request("fixtures", {
            "league": api_league_id,
            "season": season,
            "status": "FT",
        })

        if not data or not data.get("response"):
            continue

        try:
            rows = []
            for fixture in data["response"]:
                fixture_data = fixture["fixture"]
                teams = fixture["teams"]
                goals = fixture["goals"]

                rows.append({
                    "date": fixture_data["date"],
                    "home_team": teams["home"]["name"],
                    "away_team": teams["away"]["name"],
                    "home_goals": goals.get("home"),
                    "away_goals": goals.get("away"),
                    "venue": fixture_data.get("venue", {}).get("name", ""),
                    "season": season,
                })

            df = pd.DataFrame(rows)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.dropna(subset=["date"]).sort_values("date", ascending=False).head(limit)
                return df
        except (KeyError, IndexError, TypeError):
            continue

    return pd.DataFrame()


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_team_info(team_name: str, league_id: str) -> Optional[Dict]:
    """Get detailed team information including form and stats."""
    api_league_id = LEAGUE_IDS.get(league_id)
    if not api_league_id:
        return None
    
    # First, search for the team
    data = _api_request("teams", {
        "search": team_name,
    })
    
    if not data or not data.get("response"):
        return None
    
    try:
        team = data["response"][0]["team"]
        team_id = team["id"]
        
        # Get team statistics
        stats_data = _api_request("teams/statistics", {
            "team": team_id,
            "league": api_league_id,
            "season": CURRENT_SEASON,
        })
        
        if stats_data and stats_data.get("response"):
            stats = stats_data["response"]
            return {
                "id": team_id,
                "name": team["name"],
                "logo": team["logo"],
                "country": team.get("country", ""),
                "venue": stats.get("venue", {}).get("name", ""),
                "form": stats.get("form", ""),
                "fixtures": stats.get("fixtures", {}),
                "goals": stats.get("goals", {}),
            }
        
        return {
            "id": team_id,
            "name": team["name"],
            "logo": team["logo"],
        }
    except (KeyError, IndexError):
        return None


def check_api_status() -> Dict[str, Any]:
    """Check API status and remaining requests."""
    api_key = get_api_key()
    if not api_key:
        return {
            "configured": False,
            "message": "API_FOOTBALL_KEY not set",
        }
    
    try:
        with httpx.Client(timeout=5) as client:
            response = client.get(
                f"{API_BASE_URL}/status",
                headers=_get_headers(),
            )
            if response.status_code == 200:
                data = response.json()
                account = data.get("response", {}).get("account", {})
                requests_info = data.get("response", {}).get("requests", {})
                return {
                    "configured": True,
                    "plan": account.get("plan", "unknown"),
                    "requests_used": requests_info.get("current", 0),
                    "requests_limit": requests_info.get("limit_day", 100),
                }
    except Exception as e:
        return {
            "configured": True,
            "error": str(e),
        }
    
    return {"configured": True, "error": "Unknown error"}
