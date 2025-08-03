"""
# Enhanced sentiment analysis dependencies
transformers>=4.21.0
torch>=1.12.0
pytrends>=4.9.0
feedparser>=6.0.0
newspaper3k>=0.2.8
praw>=7.6.0
scikit-learn>=1.1.0
numpy>=1.21.0
pandas>=1.4.0
"""

import os
import logging
from datetime import datetime
from .base_scraper import BaseScraper

from ..sentiment.sentiment_analyzer import EnhancedSentimentAnalyzer




class EnhancedSentimentScraper(BaseScraper):
    """
    Enhanced sentiment scraper that integrates with the existing scraper architecture.
    Clean, SOLID-compliant, and compatible with EnhancedSentimentAnalyzer.
    """

    def __init__(self, alpha_vantage_key: str = None, delay: int = 2):
        """
        Initialize the enhanced sentiment scraper.
        Args:
            alpha_vantage_key (str): Alpha Vantage API key
            delay (int): Delay between requests (increased for rate limiting)
        """
        super().__init__(delay=delay)
        self.alpha_vantage_key = alpha_vantage_key or os.environ.get("ALPHA_VANTAGE_API_KEY", "")
        self.analyzer = EnhancedSentimentAnalyzer(self.alpha_vantage_key)

    def _scrape_data(self, ticker: str) -> dict:
        """
        Scrape sentiment data for the given ticker.
        Args:
            ticker (str): Stock ticker symbol
        Returns:
            dict: Dictionary containing scraped sentiment data
        """
        if not self.analyzer:
            return {"error": "Enhanced sentiment analysis not available"}

        try:
            self.logger.info("Starting enhanced sentiment analysis for %s", ticker)
            sentiment_data = self.analyzer.get_comprehensive_sentiment_analysis(ticker)
            formatted_data = {}

            # Overall sentiment metrics
            overall = sentiment_data.get("overall_sentiment", {})
            formatted_data["Overall Sentiment Score (Enhanced)"] = f"{overall.get('score', 0):.3f}"
            formatted_data["Overall Sentiment Label (Enhanced)"] = overall.get('label', 'No Data')
            formatted_data["Sentiment Confidence (Enhanced)"] = f"{overall.get('confidence', 0):.3f}"
            formatted_data["Active Data Sources (Enhanced)"] = overall.get('data_sources_count', 0)

            # Google Trends data
            trends = sentiment_data.get("data_sources", {}).get("google_trends", {})
            if not trends.get("error"):
                formatted_data["Google Trends Interest (Enhanced)"] = trends.get('latest_interest', 0)
                formatted_data["Trends Direction (Enhanced)"] = trends.get('trend_direction', 'No Data')
                formatted_data["Avg Interest (Enhanced)"] = f"{trends.get('average_interest', 0):.1f}"

            # News sentiment data
            news = sentiment_data.get("data_sources", {}).get("news_sentiment", {})
            if not news.get("error"):
                news_overall = news.get("overall_sentiment", {})
                formatted_data["News Articles Analyzed (Enhanced)"] = news_overall.get('total_articles', 0)
                formatted_data["News Sentiment Score (Enhanced)"] = f"{news_overall.get('vader_avg_sentiment', 0):.3f}"
                formatted_data["Positive News Articles (Enhanced)"] = news_overall.get('positive_articles', 0)
                formatted_data["Negative News Articles (Enhanced)"] = news_overall.get('negative_articles', 0)
                formatted_data["FinBERT News Score (Enhanced)"] = f"{news_overall.get('finbert_avg_sentiment', 0):.3f}"

            # Reddit sentiment data
            reddit = sentiment_data.get("data_sources", {}).get("reddit_sentiment", {})
            if not reddit.get("error"):
                reddit_overall = reddit.get("overall_sentiment", {})
                formatted_data["Reddit Posts Analyzed (Enhanced)"] = reddit_overall.get('total_posts', 0)
                formatted_data["Reddit Sentiment Score (Enhanced)"] = f"{reddit_overall.get('avg_sentiment', 0):.3f}"
                formatted_data["Reddit Avg Score (Enhanced)"] = f"{reddit_overall.get('avg_score', 0):.1f}"
                formatted_data["Reddit Avg Comments (Enhanced)"] = f"{reddit_overall.get('avg_comments', 0):.1f}"
                formatted_data["Positive Reddit Posts (Enhanced)"] = reddit_overall.get('positive_posts', 0)

            # Topic analysis data
            topics = sentiment_data.get("data_sources", {}).get("topic_analysis", {})
            if not topics.get("error") and "topics" in topics:
                top_topics = topics["topics"][:3]  # Top 3 topics
                for i, topic in enumerate(top_topics):
                    topic_keywords = ", ".join(topic["keywords"][-5:])  # Top 5 keywords
                    formatted_data[f"Top Topic {i+1} Keywords (Enhanced)"] = topic_keywords
                formatted_data["Document Similarity (Enhanced)"] = f"{topics.get('avg_document_similarity', 0):.3f}"

            self.logger.info("Enhanced sentiment analysis completed for %s", ticker)
            return formatted_data

        except Exception as e:
            self.logger.error("Error in enhanced sentiment analysis for %s: %s", ticker, e)
            return {"Enhanced Sentiment Error": str(e)}

