"""Data loading and transformation services for PitchIQ dashboard."""
import os
import pandas as pd
import numpy as np
import streamlit as st
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.domain.football import league_api_id, teams_for_league, normalize_league_id

# Import real-time football API service
from src.dashboard.services.football_api import (
    get_standings,
    get_fixtures,
    get_live_matches,
    get_top_scorers as api_get_top_scorers,
    get_recent_results,
    check_api_status,
    get_api_key,
)

API_BASE = os.getenv("API_URL", os.getenv("PITCHIQ_API_URL", "http://localhost:8000")).rstrip("/")


def is_real_api_configured() -> bool:
    """Check if real API is configured - reads fresh from environment."""
    return bool(get_api_key())


def use_real_api() -> bool:
    """Return True when API-Football credentials are available."""
    return is_real_api_configured()


# Backward-compatible alias for older imports.
USE_REAL_API = use_real_api


@st.cache_data(ttl=120)
def load_features() -> pd.DataFrame:
    """Load enhanced features with xG and advanced metrics from parquet (or API fallback)."""
    try:
        df = pd.read_parquet("data/features/features_v2.parquet")
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date")
        return df
    except Exception:
        # Fallback: return empty dataframe if parquet not available
        return pd.DataFrame()


@st.cache_data(ttl=30)
def get_live_scores(df: pd.DataFrame = None) -> pd.DataFrame:
    """Fetch live scores - real API or mock data."""
    def _normalize_live_scores(raw_df: pd.DataFrame) -> pd.DataFrame:
        if raw_df.empty:
            return raw_df

        normalized = raw_df.copy()
        # API-Football returns `league_name`; UI expects `league`.
        if "league" not in normalized.columns and "league_name" in normalized.columns:
            normalized["league"] = normalized["league_name"]

        required_cols = ["league", "home_team", "away_team", "home_goals", "away_goals"]
        for col in required_cols:
            if col not in normalized.columns:
                normalized[col] = 0 if col in ("home_goals", "away_goals") else ""

        normalized["home_goals"] = pd.to_numeric(normalized["home_goals"], errors="coerce").fillna(0).astype(int)
        normalized["away_goals"] = pd.to_numeric(normalized["away_goals"], errors="coerce").fillna(0).astype(int)

        return normalized[required_cols]

    if is_real_api_configured():
        live_df = get_live_matches()
        if not live_df.empty:
            return _normalize_live_scores(live_df)

        # If no matches are currently live, show latest completed match per league.
        latest_rows = []
        league_name_map = {
            "epl": "EPL",
            "laliga": "La Liga",
            "bundesliga": "Bundesliga",
            "seriea": "Serie A",
            "ligue1": "Ligue 1",
            "ucl": "Champions League",
        }
        for league_id, league_name in league_name_map.items():
            recent_df = get_recent_results(league_id, limit=1)
            if recent_df.empty:
                continue

            row = recent_df.iloc[0]
            latest_rows.append({
                "league": league_name,
                "home_team": row.get("home_team", ""),
                "away_team": row.get("away_team", ""),
                "home_goals": row.get("home_goals", 0),
                "away_goals": row.get("away_goals", 0),
            })

        if latest_rows:
            return _normalize_live_scores(pd.DataFrame(latest_rows))
    
    # Try local API fallback
    try:
        response = requests.get(f"{API_BASE}/v1/live-scores", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return _normalize_live_scores(pd.DataFrame(data))
    except Exception:
        pass
    
    # Return empty DataFrame if no data available
    return pd.DataFrame()


@st.cache_data(ttl=60)
def get_upcoming_fixtures(df: pd.DataFrame, league: str) -> pd.DataFrame:
    """Fetch upcoming fixtures - real API or mock data."""
    league_id = normalize_league_id(league)
    
    if is_real_api_configured():
        fixtures_df = get_fixtures(league_id, status="NS")
        if not fixtures_df.empty:
            return fixtures_df
    
    # Try local API fallback
    try:
        response = requests.get(f"{API_BASE}/v1/league/{league_id}/fixtures?status=upcoming", timeout=5)
        if response.status_code == 200:
            fixtures = response.json()
            return pd.DataFrame(fixtures) if fixtures else pd.DataFrame()
    except Exception:
        pass
    
    # Generate mock upcoming fixtures as fallback
    teams = teams_for_league(league)
    if not teams or len(teams) < 2:
        return pd.DataFrame()
    
    rows = []
    for i in range(min(10, len(teams) // 2)):
        rows.append({
            "league": league,
            "home_team": teams[i * 2],
            "away_team": teams[i * 2 + 1],
            "date": (datetime.now() + timedelta(days=i + 1)).isoformat(),
            "matchweek": f"Matchweek {30 + i}",
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=120)
def get_league_table(league: str) -> pd.DataFrame:
    """Fetch real league table - real API or mock data."""
    league_id = normalize_league_id(league)
    
    if is_real_api_configured():
        standings_df = get_standings(league_id)
        if not standings_df.empty:
            return standings_df
    
    # Try local API fallback
    try:
        response = requests.get(f"{API_BASE}/v1/league/{league_id}/table", timeout=5)
        if response.status_code == 200:
            table = response.json()
            return pd.DataFrame(table) if table else pd.DataFrame()
    except Exception:
        pass
    
    # Generate mock standings as fallback
    teams = teams_for_league(league)
    if not teams:
        return pd.DataFrame()
    
    np.random.seed(42)  # Consistent mock data
    rows = []
    for i, team in enumerate(teams):
        played = np.random.randint(25, 35)
        wins = np.random.randint(5, 20)
        draws = np.random.randint(3, 10)
        losses = played - wins - draws
        gf = np.random.randint(20, 70)
        ga = np.random.randint(15, 55)
        rows.append({
            "position": i + 1,
            "team": team,
            "p": played,
            "w": wins,
            "d": draws,
            "l": losses,
            "gf": gf,
            "ga": ga,
            "gd": gf - ga,
            "pts": wins * 3 + draws,
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values("pts", ascending=False).reset_index(drop=True)
    df["position"] = range(1, len(df) + 1)
    return df


@st.cache_data(ttl=120)
def get_top_scorers(league: str) -> pd.DataFrame:
    """Fetch real top scorers - real API or mock data."""
    league_id = normalize_league_id(league)
    
    if is_real_api_configured():
        scorers_df = api_get_top_scorers(league_id)
        if not scorers_df.empty:
            return scorers_df
    
    # Try local API fallback
    try:
        response = requests.get(f"{API_BASE}/v1/league/{league_id}/top-scorers", timeout=5)
        if response.status_code == 200:
            scorers = response.json()
            return pd.DataFrame(scorers) if scorers else pd.DataFrame()
    except Exception:
        pass
    
    # Generate mock top scorers as fallback
    teams = teams_for_league(league)
    if not teams:
        return pd.DataFrame()
    
    # Mock top scorers data
    mock_players = {
        "epl": [
            ("Erling Haaland", "Man City", 22, 5),
            ("Mohamed Salah", "Liverpool", 18, 10),
            ("Alexander Isak", "Newcastle", 15, 4),
            ("Cole Palmer", "Chelsea", 14, 8),
            ("Bukayo Saka", "Arsenal", 13, 9),
            ("Ollie Watkins", "Aston Villa", 12, 7),
            ("Dominic Solanke", "Tottenham", 11, 4),
            ("Chris Wood", "Nottingham", 10, 2),
        ],
        "laliga": [
            ("Robert Lewandowski", "Barcelona", 19, 6),
            ("Kylian Mbappé", "Real Madrid", 17, 8),
            ("Raphinha", "Barcelona", 14, 9),
            ("Vinícius Jr", "Real Madrid", 13, 7),
            ("Antoine Griezmann", "Atletico Madrid", 12, 5),
        ],
        "bundesliga": [
            ("Harry Kane", "Bayern Munich", 25, 8),
            ("Serhou Guirassy", "Borussia Dortmund", 18, 3),
            ("Florian Wirtz", "Bayer Leverkusen", 12, 10),
        ],
    }
    
    players = mock_players.get(league_id, [])
    if not players:
        # Generic fallback
        players = [(f"Player {i}", teams[i % len(teams)], 15 - i, 5 - i // 2) for i in range(8)]
    
    rows = []
    for i, (name, team, goals, assists) in enumerate(players, 1):
        rows.append({
            "rank": i,
            "player": name,
            "team": team,
            "goals": goals,
            "assists": assists,
        })
    
    return pd.DataFrame(rows)


@st.cache_data(ttl=120)
def get_recent_match_results(league: str, limit: int = 10) -> pd.DataFrame:
    """Fetch recent match results - real API or mock data."""
    league_id = normalize_league_id(league)
    
    if use_real_api():
        results_df = get_recent_results(league_id, limit)
        if not results_df.empty:
            return results_df
    
    # Generate mock recent results as fallback
    teams = teams_for_league(league)
    if not teams or len(teams) < 2:
        return pd.DataFrame()
    
    np.random.seed(int(datetime.now().timestamp()) % 1000)
    rows = []
    for i in range(min(limit, len(teams) // 2)):
        home_goals = np.random.randint(0, 5)
        away_goals = np.random.randint(0, 4)
        rows.append({
            "date": (datetime.now() - timedelta(days=i + 1)).isoformat(),
            "home_team": teams[(i * 2) % len(teams)],
            "away_team": teams[(i * 2 + 1) % len(teams)],
            "home_goals": home_goals,
            "away_goals": away_goals,
            "venue": f"{teams[(i * 2) % len(teams)]} Stadium",
        })
    return pd.DataFrame(rows)


def get_team_xg_snapshot(league: str, teams: List[str] = None, limit: int = 14) -> pd.DataFrame:
    """Get xG snapshot for teams in a league (placeholder)."""
    if teams is None or len(teams) == 0:
        return pd.DataFrame()
    
    # Create placeholder data with realistic xG values
    xg_rows = []
    for i, team in enumerate(teams[:limit]):
        xg_rows.append({
            "Team": team, 
            "Avg xG For": round(1.2 + (i % 5) * 0.3, 2), 
            "Avg xG Against": round(1.0 + ((i + 2) % 5) * 0.25, 2)
        })
    
    return pd.DataFrame(xg_rows)


# ===== OLD FUNCTIONS (DEPRECATED) - KEPT FOR REFERENCE =====

def build_league_table(league_df: pd.DataFrame) -> pd.DataFrame:
    """Build a standings table from match data (DEPRECATED - use get_league_table instead)."""
    if league_df.empty:
        return pd.DataFrame()

    teams = sorted(set(league_df["home_team"]).union(set(league_df["away_team"])))
    rows = []

    for team in teams:
        home = league_df[league_df["home_team"] == team]
        away = league_df[league_df["away_team"] == team]

        gf = int(home["home_goals"].fillna(0).sum() + away["away_goals"].fillna(0).sum())
        ga = int(home["away_goals"].fillna(0).sum() + away["home_goals"].fillna(0).sum())

        w = int((home["home_goals"] > home["away_goals"]).sum() + (away["away_goals"] > away["home_goals"]).sum())
        d = int((home["home_goals"] == home["away_goals"]).sum() + (away["away_goals"] == away["home_goals"]).sum())
        l = int((home["home_goals"] < home["away_goals"]).sum() + (away["away_goals"] < away["home_goals"]).sum())
        p = int(len(home) + len(away))
        pts = int(3 * w + d)

        rows.append({"Team": team, "P": p, "W": w, "D": d, "L": l, "GF": gf, "GA": ga, "GD": gf - ga, "Pts": pts})

    table = pd.DataFrame(rows).sort_values(["Pts", "GD", "GF"], ascending=False).reset_index(drop=True)
    table.insert(0, "Pos", table.index + 1)
    return table


# DEPRECATED - USE get_team_xg_snapshot() instead
def old_get_team_xg_snapshot(league_df: pd.DataFrame, teams: list[str], limit: int = 14) -> pd.DataFrame:
    """Calculate average xG for/against for teams in a league."""
    if league_df.empty:
        return pd.DataFrame()

    xg_rows = []
    for team in teams[:limit]:
        home_xg = league_df[league_df["home_team"] == team]["xg_home"].mean()
        away_xg = league_df[league_df["away_team"] == team]["xg_away"].mean()
        if not pd.isna(home_xg) and not pd.isna(away_xg):
            xg_rows.append({"Team": team, "Avg xG For": home_xg, "Avg xG Against": away_xg})

    return pd.DataFrame(xg_rows)
