"""Tests for domain models."""
import pytest
from src.domain.football import (
    normalize_league_id,
    try_normalize_league_id,
    league_name,
    normalize_team_key,
    teams_for_league,
    LEAGUES,
)


class TestLeagueNormalization:
    def test_normalize_epl_variants(self):
        assert normalize_league_id('epl') == 'epl'
        assert normalize_league_id('EPL') == 'epl'
        assert normalize_league_id('E0') == 'epl'

    def test_normalize_laliga_variants(self):
        assert normalize_league_id('laliga') == 'laliga'
        assert normalize_league_id('La Liga') == 'laliga'

    def test_try_normalize_returns_none_for_unknown(self):
        assert try_normalize_league_id('unknown_league') is None

    def test_league_name_returns_display_name(self):
        assert league_name('epl') == 'EPL'
        assert league_name('laliga') == 'La Liga'


class TestTeamNormalization:
    def test_normalize_team_key_standard(self):
        assert normalize_team_key('Liverpool') == 'liverpool'

    def test_normalize_team_key_aliases(self):
        assert normalize_team_key('Manchester United') == 'man united'
        assert normalize_team_key('Manchester City') == 'man city'


class TestTeamsForLeague:
    def test_teams_for_epl(self):
        teams = teams_for_league('epl')
        assert len(teams) == 20
        assert 'Liverpool' in teams

    def test_teams_for_laliga(self):
        teams = teams_for_league('laliga')
        assert 'Real Madrid' in teams


class TestLeaguesConstant:
    def test_leagues_has_required_fields(self):
        for league in LEAGUES:
            assert 'id' in league
            assert 'name' in league
