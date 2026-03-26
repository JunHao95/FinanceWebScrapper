"""
Tests for GET /api/peers — Phase 16 peer comparison backend.

Tests are written TDD-first: they initially fail (RED) because the route
and get_peer_data() don't exist yet. They turn GREEN after Task 2.
"""
import pytest
from unittest.mock import patch, MagicMock
from webapp import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


def _make_peer_data():
    """Minimal valid get_peer_data() return value with 3 peer rows."""
    return {
        "sector": "Technology",
        "peers": ["MSFT", "GOOGL"],
        "peer_data": [
            {"ticker": "AAPL", "pe": 28.5, "pb": 5.2, "roe": 25.3, "op_margin": 30.2},
            {"ticker": "MSFT", "pe": 35.1, "pb": 11.0, "roe": 36.5, "op_margin": 42.1},
            {"ticker": "GOOGL", "pe": 22.4, "pb": 6.3, "roe": 18.7, "op_margin": 28.9},
        ],
    }


class TestPeersShape:
    """Happy path: correct JSON shape returned."""

    def test_peers_returns_shape(self, client):
        with patch(
            "src.scrapers.finviz_scraper.FinvizScraper.get_peer_data",
            return_value=_make_peer_data(),
        ):
            resp = client.get("/api/peers?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "sector" in data
        assert "peers" in data
        assert "peer_data" in data
        assert "percentiles" in data
        for field in ("pe", "pb", "roe", "op_margin"):
            assert field in data["percentiles"], f"percentiles missing field: {field}"

    def test_peers_percentiles_have_value_and_rank(self, client):
        with patch(
            "src.scrapers.finviz_scraper.FinvizScraper.get_peer_data",
            return_value=_make_peer_data(),
        ):
            resp = client.get("/api/peers?ticker=AAPL")
        data = resp.get_json()
        for field in ("pe", "pb", "roe", "op_margin"):
            assert "value" in data["percentiles"][field]
            assert "rank" in data["percentiles"][field]
            rank = data["percentiles"][field]["rank"]
            assert 0 <= rank <= 100, f"rank out of range for {field}: {rank}"


class TestPeersCacheHit:
    """Cache: second call with same ticker should not re-invoke get_peer_data."""

    def test_peers_cache_hit(self, client):
        # Clear cache state before test
        import webapp
        webapp._peer_cache.clear()

        with patch(
            "src.scrapers.finviz_scraper.FinvizScraper.get_peer_data",
            return_value=_make_peer_data(),
        ) as mock_gpd:
            client.get("/api/peers?ticker=AAPL")
            client.get("/api/peers?ticker=AAPL")

        assert mock_gpd.call_count == 1, (
            f"Expected 1 call (cache hit on 2nd), got {mock_gpd.call_count}"
        )


class TestPeersFailureStates:
    """Failure states: both return {error: ...} with HTTP 200."""

    def test_peers_fewer_than_two_peers(self, client):
        sparse = {
            "sector": "Technology",
            "peers": [],
            "peer_data": [
                {"ticker": "AAPL", "pe": 28.5, "pb": 5.2, "roe": 25.3, "op_margin": 30.2},
            ],
        }
        with patch(
            "src.scrapers.finviz_scraper.FinvizScraper.get_peer_data",
            return_value=sparse,
        ):
            resp = client.get("/api/peers?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "error" in data

    def test_peers_scrape_failure(self, client):
        with patch(
            "src.scrapers.finviz_scraper.FinvizScraper.get_peer_data",
            side_effect=Exception("Network timeout"),
        ):
            resp = client.get("/api/peers?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "error" in data
