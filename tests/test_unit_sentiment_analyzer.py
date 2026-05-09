"""
Unit tests for src/sentiment/sentiment_analyzer.py

Covers: finbert_avg_sentiment None when FinBERT unavailable,
NewsCollector overall_sentiment structure with/without FinBERT scores.

No live network calls — mocked feedparser and SentimentAnalyzer.
"""

from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# finbert_avg_sentiment — None when FinBERT pipeline unavailable


def _make_news_collector(finbert_available=True):
    """Return a NewsCollector with a mocked SentimentAnalyzer."""
    from src.sentiment.sentiment_analyzer import NewsCollector

    mock_analyzer = MagicMock()
    mock_analyzer.vader_analyzer = MagicMock()

    if finbert_available:
        mock_analyzer.finbert_pipeline = MagicMock()
        mock_analyzer.analyze.return_value = {
            "vader_compound": 0.5,
            "vader_positive": 0.4,
            "vader_negative": 0.1,
            "vader_neutral": 0.5,
            "finbert_label": "positive",
            "finbert_score": 0.92,
        }
    else:
        mock_analyzer.finbert_pipeline = None
        mock_analyzer.analyze.return_value = {
            "vader_compound": 0.5,
            "vader_positive": 0.4,
            "vader_negative": 0.1,
            "vader_neutral": 0.5,
            # no finbert_score key
        }

    collector = NewsCollector(mock_analyzer)
    return collector


def _make_entry(title, summary):
    """Simulate a feedparser entry that supports both getattr and .get()."""
    entry = MagicMock()
    entry.title = title
    entry.get = lambda key, default="": {
        "summary": summary,
        "published": "",
        "link": "",
    }.get(key, default)
    return entry


FAKE_FEED = MagicMock()
FAKE_FEED.entries = [
    _make_entry("AMD beats earnings", "AMD reported strong results."),
    _make_entry("AMD new GPU launch", "AMD releases RDNA 4."),
]


def _make_fake_response(content=b"<rss/>"):
    mock_resp = MagicMock()
    mock_resp.content = content
    return mock_resp


class TestNewsCollectorFinBERT:
    @patch("src.sentiment.sentiment_analyzer.make_request")
    @patch("feedparser.parse")
    def test_finbert_score_present_when_pipeline_available(self, mock_parse, mock_req):
        mock_req.return_value = _make_fake_response()
        mock_parse.return_value = FAKE_FEED
        collector = _make_news_collector(finbert_available=True)
        result = collector.get_news_sentiment("AMD", num_articles=5)
        overall = result.get("overall_sentiment", {})
        assert overall.get("finbert_avg_sentiment") is not None
        assert isinstance(overall["finbert_avg_sentiment"], float)

    @patch("src.sentiment.sentiment_analyzer.make_request")
    @patch("feedparser.parse")
    def test_finbert_score_none_when_pipeline_unavailable(self, mock_parse, mock_req):
        mock_req.return_value = _make_fake_response()
        mock_parse.return_value = FAKE_FEED
        collector = _make_news_collector(finbert_available=False)
        result = collector.get_news_sentiment("AMD", num_articles=5)
        overall = result.get("overall_sentiment", {})
        assert overall.get("finbert_avg_sentiment") is None

    @patch("src.sentiment.sentiment_analyzer.make_request")
    @patch("feedparser.parse")
    def test_finbert_score_none_when_no_articles(self, mock_parse, mock_req):
        mock_req.return_value = _make_fake_response()
        mock_parse.return_value = {"bozo": False, "entries": []}
        collector = _make_news_collector(finbert_available=False)
        result = collector.get_news_sentiment("AMD", num_articles=5)
        overall = result.get("overall_sentiment", {})
        assert overall.get("finbert_avg_sentiment") is None


# ---------------------------------------------------------------------------
# enhanced_sentiment_scraper — FinBERT field omitted when None


class TestEnhancedSentimentScraperFinBERT:
    def _format_finbert(self, finbert_avg_sentiment):
        """Mirrors the logic in EnhancedSentimentScraper._scrape_data."""
        finbert_val = finbert_avg_sentiment
        return f"{finbert_val:.3f}" if finbert_val is not None else "--"

    def test_finbert_field_shows_dash_when_none(self):
        result = self._format_finbert(None)
        assert result == "--"

    def test_finbert_field_present_when_available(self):
        result = self._format_finbert(0.87)
        assert result == "0.870"
