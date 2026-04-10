"""Integration tests for the API."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from src.api.main import app
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get('/health')
        assert response.status_code == 200


class TestLeaguesEndpoint:
    def test_leagues_returns_200(self, client):
        response = client.get('/v1/leagues')
        assert response.status_code == 200

    def test_leagues_returns_list(self, client):
        response = client.get('/v1/leagues')
        assert isinstance(response.json(), list)


class TestPredictValidation:
    def test_predict_validates_empty_team(self, client):
        response = client.post('/v1/predict', json={
            'home_team': '',
            'away_team': 'Chelsea',
            'league': 'epl',
            'date': '2024-04-15',
            'matchweek': 30
        })
        assert response.status_code == 422

    def test_predict_validates_invalid_league(self, client):
        response = client.post('/v1/predict', json={
            'home_team': 'Liverpool',
            'away_team': 'Chelsea',
            'league': 'invalid_league',
            'date': '2024-04-15',
            'matchweek': 30
        })
        assert response.status_code == 422

    def test_predict_blocks_xss(self, client):
        response = client.post('/v1/predict', json={
            'home_team': '<script>alert(1)</script>',
            'away_team': 'Chelsea',
            'league': 'epl',
            'date': '2024-04-15',
            'matchweek': 30
        })
        assert response.status_code == 422
