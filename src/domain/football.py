"""Shared league/team canonicalization.

This centralizes the league IDs/names/codes and team lists so ingestion, feature
building, the API, and the dashboard don't drift out of sync.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _norm_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _slug(value: Any) -> str:
    # Keep only alphanumerics; collapse spaces/punctuation differences.
    return re.sub(r"[^a-z0-9]+", "", _norm_text(value))


@dataclass(frozen=True)
class LeagueDef:
    id: str
    name: str  # Display name used in UI/API ("La Liga", "Serie A", etc.)
    country: str
    season: str
    football_data_code: Optional[str]  # E0/SP1/D1/I1/F1


# Canonical league list exposed by the API and used by the dashboard.
LEAGUES: List[Dict[str, str]] = [
    {"id": "epl", "name": "EPL", "country": "England", "season": "2024/25"},
    {"id": "laliga", "name": "La Liga", "country": "Spain", "season": "2024/25"},
    {"id": "bundesliga", "name": "Bundesliga", "country": "Germany", "season": "2024/25"},
    {"id": "seriea", "name": "Serie A", "country": "Italy", "season": "2024/25"},
    {"id": "ligue1", "name": "Ligue 1", "country": "France", "season": "2024/25"},
    {"id": "ucl", "name": "Champions League", "country": "Europe", "season": "2024/25"},
]


_LEAGUE_DEFS: List[LeagueDef] = [
    LeagueDef(id="epl", name="EPL", country="England", season="2024/25", football_data_code="E0"),
    LeagueDef(id="laliga", name="La Liga", country="Spain", season="2024/25", football_data_code="SP1"),
    LeagueDef(id="bundesliga", name="Bundesliga", country="Germany", season="2024/25", football_data_code="D1"),
    LeagueDef(id="seriea", name="Serie A", country="Italy", season="2024/25", football_data_code="I1"),
    LeagueDef(id="ligue1", name="Ligue 1", country="France", season="2024/25", football_data_code="F1"),
    LeagueDef(id="ucl", name="Champions League", country="Europe", season="2024/25", football_data_code=None),
]

LEAGUE_DEF_BY_ID: Dict[str, LeagueDef] = {d.id: d for d in _LEAGUE_DEFS}


LEAGUE_ID_BY_ANY: Dict[str, str] = {}
for d in _LEAGUE_DEFS:
    LEAGUE_ID_BY_ANY[_slug(d.id)] = d.id
    LEAGUE_ID_BY_ANY[_slug(d.name)] = d.id
    if d.football_data_code:
        LEAGUE_ID_BY_ANY[_slug(d.football_data_code)] = d.id

# Extra common aliases
LEAGUE_ID_BY_ANY.update(
    {
        "premierleague": "epl",
        "pl": "epl",
        "e0": "epl",
        "sp1": "laliga",
        "d1": "bundesliga",
        "i1": "seriea",
        "f1": "ligue1",
        "ucl": "ucl",
        "championsleague": "ucl",
        "uefachampionsleague": "ucl",
    }
)


def normalize_league_id(value: Any, default: str = "epl") -> str:
    key = _slug(value)
    return LEAGUE_ID_BY_ANY.get(key, default if default else key)


def try_normalize_league_id(value: Any) -> Optional[str]:
    """Return a canonical league id if known, else None."""
    return LEAGUE_ID_BY_ANY.get(_slug(value))


def league_name(value: Any) -> str:
    return LEAGUE_DEF_BY_ID[normalize_league_id(value)].name


def league_api_id(value: Any) -> str:
    return normalize_league_id(value)


def football_data_code(value: Any) -> Optional[str]:
    return LEAGUE_DEF_BY_ID[normalize_league_id(value)].football_data_code


def try_football_data_code(value: Any) -> Optional[str]:
    lid = try_normalize_league_id(value)
    if lid is None:
        return None
    return LEAGUE_DEF_BY_ID[lid].football_data_code


def feature_store_league_norm(value: Any) -> str:
    """League key used in the feature store (e.g. 'e0', 'sp1', ..., 'ucl')."""
    lid = try_normalize_league_id(value)
    if lid is None:
        return _slug(value)

    if lid == "ucl":
        return "ucl"

    code = LEAGUE_DEF_BY_ID[lid].football_data_code
    return code.lower() if code else "ucl"


def feature_build_leagues() -> List[Tuple[str, str]]:
    """List of (football-data code, league name) pairs for feature building."""
    pairs: List[Tuple[str, str]] = []
    for d in _LEAGUE_DEFS:
        if d.football_data_code is None:
            continue
        pairs.append((d.football_data_code, d.name))
    return pairs


# Canonical team lists used by mock endpoints and synthetic data generation.
TEAMS_BY_LEAGUE_NAME: Dict[str, List[str]] = {
    "EPL": [
        "Arsenal",
        "Chelsea",
        "Liverpool",
        "Man City",
        "Man United",
        "Tottenham",
        "Newcastle",
        "Brighton",
        "Fulham",
        "Crystal Palace",
        "Everton",
        "Wolves",
        "Aston Villa",
        "Southampton",
        "West Ham",
        "Leicester",
        "Brentford",
        "Bournemouth",
        "Nottingham",
        "Ipswich",
    ],
    "La Liga": [
        "Real Madrid",
        "Barcelona",
        "Atletico Madrid",
        "Sevilla",
        "Valencia",
        "Villarreal",
        "Real Sociedad",
        "Granada",
        "Levante",
        "Getafe",
        "Celta Vigo",
        "Athletic Bilbao",
        "Espanyol",
        "Mallorca",
        "Osasuna",
        "Elche",
        "Cadiz",
        "Real Betis",
        "Alaves",
        "Valladolid",
    ],
    "Bundesliga": [
        "Bayern Munich",
        "Borussia Dortmund",
        "Bayer Leverkusen",
        "RB Leipzig",
        "Union Berlin",
        "Freiburg",
        "Wolfsburg",
        "Mainz",
        "Borussia Monchengladbach",
        "Stuttgart",
        "Augsburg",
        "Werder Bremen",
        "Hertha Berlin",
        "Hoffenheim",
        "Koln",
        "Schalke",
        "Eintracht Frankfurt",
        "Arminia Bielefeld",
    ],
    "Serie A": [
        "Juventus",
        "Inter",
        "AC Milan",
        "Roma",
        "Napoli",
        "Lazio",
        "Sassuolo",
        "Verona",
        "Torino",
        "Udinese",
        "Bologna",
        "Empoli",
        "Fiorentina",
        "Spezia",
        "Genoa",
        "Cagliari",
        "Venezia",
        "Salernitana",
        "Sampdoria",
        "Atalanta",
    ],
    "Ligue 1": [
        "PSG",
        "Lyon",
        "Monaco",
        "Marseille",
        "Lille",
        "Nice",
        "Lens",
        "Rennes",
        "Strasbourg",
        "Montpellier",
        "Nantes",
        "Brest",
        "Metz",
        "Angers",
        "Troyes",
        "Lorient",
        "Clermont",
        "Reims",
        "Saint-Etienne",
        "Bordeaux",
    ],
    "Champions League": [
        "Real Madrid",
        "Bayern Munich",
        "Liverpool",
        "Barcelona",
        "Man City",
        "Arsenal",
        "Inter",
        "PSG",
        "Borussia Dortmund",
        "Atletico Madrid",
        "Bayer Leverkusen",
        "Juventus",
        "AC Milan",
        "Benfica",
        "Feyenoord",
        "Celtic",
    ],
}


def teams_for_league(value: Any) -> List[str]:
    return TEAMS_BY_LEAGUE_NAME.get(league_name(value), [])


# Team normalization (key used for matching into the feature store).
TEAM_KEY_ALIASES: Dict[str, str] = {
    # EPL
    _slug("Manchester United"): _norm_text("Man United"),
    _slug("Manchester City"): _norm_text("Man City"),
    # La Liga
    _slug("Betis"): _norm_text("Real Betis"),
    _slug("Sociedad"): _norm_text("Real Sociedad"),
    # Bundesliga
    _slug("Dortmund"): _norm_text("Borussia Dortmund"),
    _slug("Leverkusen"): _norm_text("Bayer Leverkusen"),
    _slug("Monchengladbach"): _norm_text("Borussia Monchengladbach"),
    _slug("Moenchengladbach"): _norm_text("Borussia Monchengladbach"),
    _slug("Frankfurt"): _norm_text("Eintracht Frankfurt"),
    _slug("Ein Frankfurt"): _norm_text("Eintracht Frankfurt"),
    _slug("1. FC Koln"): _norm_text("Koln"),
    _slug("FC Koln"): _norm_text("Koln"),
    # Serie A
    _slug("Milan"): _norm_text("AC Milan"),
}


_CANONICAL_TEAM_KEY_BY_SLUG: Dict[str, str] = {}
for _teams in TEAMS_BY_LEAGUE_NAME.values():
    for _t in _teams:
        _CANONICAL_TEAM_KEY_BY_SLUG[_slug(_t)] = _norm_text(_t)


def normalize_team_key(value: Any) -> str:
    """Return a stable lowercase key for a team name (used for joins/matching)."""
    raw = _norm_text(value)
    key = _slug(raw)
    if key in TEAM_KEY_ALIASES:
        return TEAM_KEY_ALIASES[key]
    if key in _CANONICAL_TEAM_KEY_BY_SLUG:
        return _CANONICAL_TEAM_KEY_BY_SLUG[key]
    return raw
