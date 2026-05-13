"""
Unit tests for plan 30-04: Sentiment company name resolution for SGX tickers.

Covers:
- get_news_sentiment builds search terms including company_name when provided
- get_news_sentiment includes base ticker (without .SI) for dotted tickers
- get_news_sentiment backward-compatible for US tickers
- get_comprehensive_sentiment_analysis passes company_name to get_news_sentiment
- enhanced_sentiment_scraper calls yfinance for dotted tickers to resolve name
"""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# NewsCollector.get_news_sentiment — search term construction
# ---------------------------------------------------------------------------


def _make_news_collector():
    from src.sentiment.sentiment_analyzer import NewsCollector

    mock_analyzer = MagicMock()
    mock_analyzer.vader_analyzer = MagicMock()
    mock_analyzer.finbert_pipeline = None
    nc = NewsCollector(mock_analyzer)
    return nc


class TestGetNewsSentimentSearchTerms:

    @pytest.mark.unit
    @patch("feedparser.parse")
    @patch("src.sentiment.sentiment_analyzer.make_request")
    def test_company_name_in_search_terms(self, mock_req, mock_fp):
        """company_name kwarg must appear in the Google News URL search terms."""
        mock_req.return_value = MagicMock(content=b"")
        mock_fp.return_value = MagicMock(entries=[])
        nc = _make_news_collector()
        nc.get_news_sentiment("D05.SI", company_name="DBS Group Holdings Ltd")
        urls = [call_args[0][0] for call_args in mock_req.call_args_list]
        google_url = next((u for u in urls if "google.com/rss/search" in u), None)
        assert google_url is not None
        assert "dbs" in google_url.lower()

    @pytest.mark.unit
    @patch("feedparser.parse")
    @patch("src.sentiment.sentiment_analyzer.make_request")
    def test_base_ticker_added_for_dotted_ticker(self, mock_req, mock_fp):
        """For D05.SI, Google News URL uses company name only (not AND-joined ticker noise).
        The 'd05' base ticker is retained in search_terms for article-level filtering.
        """
        mock_req.return_value = MagicMock(content=b"")
        mock_fp.return_value = MagicMock(entries=[])
        nc = _make_news_collector()
        nc.get_news_sentiment("D05.SI", company_name="DBS Group Holdings Ltd")
        urls = [call_args[0][0] for call_args in mock_req.call_args_list]
        google_url = next((u for u in urls if "google.com/rss/search" in u), "")
        # URL must contain company name (not AND-join of all search_terms)
        assert "dbs" in google_url.lower()
        assert "d05.si" not in google_url.lower()

    @pytest.mark.unit
    @patch("feedparser.parse")
    @patch("src.sentiment.sentiment_analyzer.make_request")
    def test_us_ticker_uses_hardcoded_name(self, mock_req, mock_fp):
        """AAPL without company_name kwarg must still include 'apple' from dict."""
        mock_req.return_value = MagicMock(content=b"")
        mock_fp.return_value = MagicMock(entries=[])
        nc = _make_news_collector()
        nc.get_news_sentiment("AAPL")
        urls = [call_args[0][0] for call_args in mock_req.call_args_list]
        google_url = next((u for u in urls if "google.com/rss/search" in u), "")
        assert "apple" in google_url.lower()

    @pytest.mark.unit
    @patch("feedparser.parse")
    @patch("src.sentiment.sentiment_analyzer.make_request")
    def test_no_base_added_for_plain_ticker(self, mock_req, mock_fp):
        """AAPL (no dot) must not have a spurious base appended."""
        mock_req.return_value = MagicMock(content=b"")
        mock_fp.return_value = MagicMock(entries=[])
        nc = _make_news_collector()
        nc.get_news_sentiment("AAPL")
        urls = [call_args[0][0] for call_args in mock_req.call_args_list]
        google_url = next((u for u in urls if "google.com/rss/search" in u), "")
        # Should not contain a spurious base like 'aapl' duplicated in weird way
        # The base logic only fires when "." in ticker
        terms_str = google_url.split("?q=")[-1].split("&")[0].lower()
        assert terms_str.count("aapl") <= 1

    @pytest.mark.unit
    @patch("feedparser.parse")
    @patch("src.sentiment.sentiment_analyzer.make_request")
    def test_short_name_variant_added(self, mock_req, mock_fp):
        """First word of resolved company name must appear in the Google News URL."""
        mock_req.return_value = MagicMock(content=b"")
        mock_fp.return_value = MagicMock(entries=[])
        nc = _make_news_collector()
        nc.get_news_sentiment("D05.SI", company_name="DBS Group Holdings Ltd")
        urls = [call_args[0][0] for call_args in mock_req.call_args_list]
        google_url = next((u for u in urls if "google.com/rss/search" in u), "")
        assert (
            "dbs" in google_url.lower()
        ), "short name 'dbs' must appear in Google News URL"
        assert (
            "d05.si" not in google_url.lower()
        ), "raw ticker must not pollute the Google News query"


# ---------------------------------------------------------------------------
# EnhancedSentimentAnalyzer.get_comprehensive_sentiment_analysis
# — passes company_name to get_news_sentiment
# ---------------------------------------------------------------------------


class TestComprehensiveSentimentPassthrough:

    def _make_analyzer(self):
        from src.sentiment.sentiment_analyzer import EnhancedSentimentAnalyzer

        with patch("src.sentiment.sentiment_analyzer.SentimentAnalyzer"):
            with patch("src.sentiment.sentiment_analyzer.NewsCollector"):
                with patch("src.sentiment.sentiment_analyzer.RedditCollector"):
                    with patch("src.sentiment.sentiment_analyzer.TopicAnalyzer"):
                        a = EnhancedSentimentAnalyzer.__new__(EnhancedSentimentAnalyzer)
                        a.logger = MagicMock()
                        a.news_collector = MagicMock()
                        a.reddit_collector = MagicMock()
                        a.google_trends_collector = MagicMock()
                        a.sentiment_analyzer = MagicMock()
                        a.topic_analyzer = MagicMock()
                        return a

    @pytest.mark.unit
    def test_company_name_forwarded_to_news_sentiment(self):
        """company_name kwarg must be passed through to get_news_sentiment."""
        a = self._make_analyzer()
        a.news_collector.get_news_sentiment.return_value = {"articles": []}
        a.reddit_collector.get_reddit_sentiment.return_value = {"posts": []}
        a.google_trends_collector.get_google_trends_data.return_value = {}

        a.get_comprehensive_sentiment_analysis("D05.SI", company_name="DBS Group")

        a.news_collector.get_news_sentiment.assert_called_once()
        _, kwargs = a.news_collector.get_news_sentiment.call_args
        assert kwargs.get("company_name") == "DBS Group"


# ---------------------------------------------------------------------------
# EnhancedSentimentScraper._scrape_data — yfinance resolution for .SI tickers
# ---------------------------------------------------------------------------


class TestEnhancedSentimentScraperNameResolution:

    def _make_scraper(self):
        from src.scrapers.enhanced_sentiment_scraper import EnhancedSentimentScraper

        s = EnhancedSentimentScraper.__new__(EnhancedSentimentScraper)
        s.logger = MagicMock()
        s.analyzer = MagicMock()
        s.analyzer.get_comprehensive_sentiment_analysis.return_value = {
            "overall_sentiment": {"score": 0.1, "label": "Neutral"},
            "data_sources": {},
        }
        return s

    @pytest.mark.unit
    def test_yfinance_called_for_dotted_ticker(self):
        """_scrape_data must call yfinance when ticker contains a dot."""
        scraper = self._make_scraper()
        mock_info = {"longName": "DBS Group Holdings Ltd"}
        with patch("yfinance.Ticker") as mock_yf:
            mock_yf.return_value.info = mock_info
            scraper._scrape_data("D05.SI")
            mock_yf.assert_called_once_with("D05.SI")

    @pytest.mark.unit
    def test_resolved_name_passed_to_analyzer(self):
        """Resolved longName must be forwarded to get_comprehensive_sentiment_analysis."""
        scraper = self._make_scraper()
        with patch("yfinance.Ticker") as mock_yf:
            mock_yf.return_value.info = {"longName": "DBS Group Holdings Ltd"}
            scraper._scrape_data("D05.SI")
        scraper.analyzer.get_comprehensive_sentiment_analysis.assert_called_once_with(
            "D05.SI", company_name="DBS Group Holdings Ltd"
        )

    @pytest.mark.unit
    def test_yfinance_not_called_for_plain_ticker(self):
        """_scrape_data must NOT call yfinance for plain US tickers (no dot)."""
        scraper = self._make_scraper()
        with patch("yfinance.Ticker") as mock_yf:
            scraper._scrape_data("AAPL")
            mock_yf.assert_not_called()

    @pytest.mark.unit
    def test_company_name_none_on_yfinance_failure(self):
        """If yfinance raises, company_name=None is passed — no crash."""
        scraper = self._make_scraper()
        with patch("yfinance.Ticker", side_effect=Exception("network error")):
            scraper._scrape_data("D05.SI")
        scraper.analyzer.get_comprehensive_sentiment_analysis.assert_called_once_with(
            "D05.SI", company_name=None
        )
