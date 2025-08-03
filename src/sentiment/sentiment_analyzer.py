"""
Advanced Sentiment Analysis Module for Financial Data
Integrates multiple data sources and sentiment analysis techniques
"""

import pandas as pd
import numpy as np
import requests
import logging
import time
import re
from datetime import datetime
from typing import Dict, List, Any
import os
import warnings
warnings.filterwarnings('ignore')

# Core sentiment analysis libraries
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers.pipelines import pipeline

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
# Download required NLTK data
nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# Text analysis libraries
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD, NMF
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

# Data source libraries
from pytrends.request import TrendReq
import feedparser
from newspaper import Article
import newspaper
import praw

SKLEARN_AVAILABLE = True # For advanced text analysis using scikit-learn
PYTRENDS_AVAILABLE = True # For Google Trends analysis
FEEDPARSER_AVAILABLE = True # For RSS feed analysis
NEWSPAPER_AVAILABLE = True # For news article extraction
PRAW_AVAILABLE = True # For Reddit sentiment analysis

class SentimentAnalyzer:
    """Handles sentiment analysis using VADER and FinBERT"""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.vader_analyzer = SentimentIntensityAnalyzer()
            self.logger.info("VADER sentiment analyzer initialized")
        except Exception as e:
            self.logger.error("Error initializing VADER: %s", e)
            self.vader_analyzer = None
        try:
            model_name = "ProsusAI/finbert"
            self.finbert_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.finbert_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.finbert_pipeline = pipeline(
                task="sentiment-analysis",
                model=self.finbert_model,
                tokenizer=self.finbert_tokenizer
            )
            self.logger.info("FinBERT sentiment analyzer initialized")
        except Exception as e:
            self.logger.error("Error initializing FinBERT: %s", e)
            self.finbert_pipeline = None

    def analyze(self, text: str) -> Dict[str, Any]:
        results = {}
        if self.vader_analyzer:
            try:
                vader_scores = self.vader_analyzer.polarity_scores(text)
                results.update({
                    'vader_compound': vader_scores['compound'],
                    'vader_positive': vader_scores['pos'],
                    'vader_negative': vader_scores['neg'],
                    'vader_neutral': vader_scores['neu']
                })
            except Exception as e:
                self.logger.error("Error with VADER analysis: %s", e)
        if self.finbert_pipeline:
            try:
                text_truncated = text[:512] if len(text) > 512 else text
                finbert_result = self.finbert_pipeline(text_truncated)[0]
                results.update({
                    'finbert_label': finbert_result['label'],
                    'finbert_score': finbert_result['score']
                })
            except Exception as e:
                self.logger.error("Error with FinBERT analysis: %s", e)
        return results


class NewsCollector:
    """Collects and analyzes news sentiment for a ticker"""
    def __init__(self, sentiment_analyzer: SentimentAnalyzer):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.sentiment_analyzer = sentiment_analyzer

    def get_news_sentiment(self, ticker: str, num_articles: int = 10) -> Dict[str, Any]:
        news_data = []
        news_sources = [
            'https://feeds.finance.yahoo.com/rss/2.0/headline',
            'https://feeds.marketwatch.com/marketwatch/topstories/',
            'https://feeds.bloomberg.com/markets/news.rss'
        ]
        for source in news_sources:
            try:
                feed = feedparser.parse(source)
                for entry in feed.entries[:num_articles//len(news_sources)]:
                    if ticker.lower() in entry.title.lower() or ticker.lower() in entry.get('summary', '').lower():
                        news_data.append({
                            'title': entry.title,
                            'summary': entry.get('summary', ''),
                            'published': entry.get('published', ''),
                            'link': entry.get('link', ''),
                            'source': source
                        })
            except Exception as e:
                self.logger.warning("Error parsing RSS feed %s: %s", source, e)
        sentiment_results = []
        for article in news_data:
            text = f"{article['title']} {article['summary']}"
            sentiment = self.sentiment_analyzer.analyze(text)
            sentiment_results.append({
                **article,
                **sentiment
            })
        if sentiment_results:
            vader_scores = [r.get('vader_compound', 0) for r in sentiment_results if r.get('vader_compound') is not None]
            finbert_scores = [r.get('finbert_score', 0) for r in sentiment_results if r.get('finbert_score') is not None]
            overall_sentiment = {
                "total_articles": len(sentiment_results),
                "vader_avg_sentiment": np.mean(vader_scores) if vader_scores else 0,
                "finbert_avg_sentiment": np.mean(finbert_scores) if finbert_scores else 0,
                "positive_articles": len([r for r in sentiment_results if r.get('vader_compound', 0) > 0.05]),
                "negative_articles": len([r for r in sentiment_results if r.get('vader_compound', 0) < -0.05]),
                "neutral_articles": len([r for r in sentiment_results if -0.05 <= r.get('vader_compound', 0) <= 0.05])
            }
        else:
            overall_sentiment = {
                "total_articles": 0,
                "vader_avg_sentiment": 0,
                "finbert_avg_sentiment": 0,
                "positive_articles": 0,
                "negative_articles": 0,
                "neutral_articles": 0
            }
        return {
            "overall_sentiment": overall_sentiment,
            "articles": sentiment_results[:10]
        }


class RedditCollector:
    """Collects and analyzes Reddit sentiment for a ticker"""
    def __init__(self, sentiment_analyzer: SentimentAnalyzer):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.sentiment_analyzer = sentiment_analyzer
        reddit_client_id = os.environ.get("REDDIT_CLIENT_ID")
        reddit_client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
        reddit_user_agent = os.environ.get("REDDIT_USER_AGENT", "FinanceScraper/1.0")
        if reddit_client_id and reddit_client_secret:
            self.reddit = praw.Reddit(
                client_id=reddit_client_id,
                client_secret=reddit_client_secret,
                user_agent=reddit_user_agent
            )
            self.logger.info("Reddit collector initialized")
        else:
            self.reddit = None
            self.logger.warning("Reddit credentials not found")


    def get_reddit_sentiment(self, ticker: str, subreddits: List[str], limit: int = 50) -> Dict[str, Any]:
        if not self.reddit:
            return {"error": "Reddit not available"}
        reddit_posts = []
        try:
            for subreddit_name in subreddits:
                subreddit = self.reddit.subreddit(subreddit_name)
                for post in subreddit.search(ticker, limit=limit//len(subreddits)):
                    if post.selftext or post.title:
                        text = f"{post.title} {post.selftext}"
                        sentiment = self.sentiment_analyzer.analyze(text)
                        reddit_posts.append({
                            'title': post.title,
                            'text': post.selftext[:500],
                            'score': post.score,
                            'comments': post.num_comments,
                            'created': datetime.fromtimestamp(post.created_utc).isoformat(),
                            'subreddit': subreddit_name,
                            **sentiment
                        })
                time.sleep(1)
        except Exception as e:
            self.logger.error("Error getting Reddit data: %s", e)
            return {"error": str(e)}
        if reddit_posts:
            vader_scores = [p.get('vader_compound', 0) for p in reddit_posts if p.get('vader_compound') is not None]
            overall_sentiment = {
                "total_posts": len(reddit_posts),
                "avg_sentiment": np.mean(vader_scores) if vader_scores else 0,
                "positive_posts": len([p for p in reddit_posts if p.get('vader_compound', 0) > 0.05]),
                "negative_posts": len([p for p in reddit_posts if p.get('vader_compound', 0) < -0.05]),
                "avg_score": np.mean([p['score'] for p in reddit_posts]),
                "avg_comments": np.mean([p['comments'] for p in reddit_posts])
            }
        else:
            overall_sentiment = {
                "total_posts": 0,
                "avg_sentiment": 0,
                "positive_posts": 0,
                "negative_posts": 0,
                "avg_score": 0,
                "avg_comments": 0
            }
        return {
            "overall_sentiment": overall_sentiment,
            "posts": reddit_posts[:10]
        }


class GoogleTrendsCollector:
    """Collects Google Trends data for a ticker"""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.pytrends = TrendReq(hl='en-US', tz=360)
            self.logger.info("Google Trends collector initialized")
        except Exception as e:
            self.logger.error("Error initializing Google Trends: %s", e)
            self.pytrends = None


    def get_google_trends_data(self, ticker: str, timeframe: str = 'today 6-m') -> Dict[str, Any]:
        if not self.pytrends:
            return {"error": "Google Trends not available"}
        try:
            keywords = [ticker, f"{ticker} stock", f"{ticker} price"]
            self.pytrends.build_payload(keywords, timeframe=timeframe)
            interest_over_time = self.pytrends.interest_over_time()
            related_queries = self.pytrends.related_queries()
            if not interest_over_time.empty:
                latest_interest = interest_over_time[ticker].iloc[-1] if ticker in interest_over_time.columns else 0
                avg_interest = interest_over_time[ticker].mean() if ticker in interest_over_time.columns else 0
                trend_direction = "Increasing" if latest_interest > avg_interest else "Decreasing"
            else:
                latest_interest = avg_interest = 0
                trend_direction = "No data"
            return {
                "latest_interest": latest_interest,
                "average_interest": avg_interest,
                "trend_direction": trend_direction,
                "interest_over_time": interest_over_time.to_dict() if not interest_over_time.empty else {},
                "related_queries": {
                    "top": related_queries.get(ticker, {}).get('top', pd.DataFrame()).to_dict() if related_queries.get(ticker) else {},
                    "rising": related_queries.get(ticker, {}).get('rising', pd.DataFrame()).to_dict() if related_queries.get(ticker) else {}
                }
            }
        except Exception as e:
            self.logger.error("Error getting Google Trends data: %s", e)
            return {"error": str(e)}


class TopicAnalyzer:
    """Performs topic analysis on a collection of texts"""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',   
            ngram_range=(1, 2)
        )
        self.logger.info("Text analyzers initialized")


    def perform_topic_analysis(self, texts: List[str], n_topics: int = 5) -> Dict[str, Any]:
        if not texts:
            return {"error": "No texts provided"}
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            nmf = NMF(n_components=n_topics, random_state=42)
            nmf.fit(tfidf_matrix)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            topics = []
            for topic_idx, topic in enumerate(nmf.components_):
                top_words = [feature_names[i] for i in topic.argsort()[-10:]]
                topics.append({
                    'topic_id': topic_idx,
                    'keywords': top_words,
                    'weight': float(topic.max())
                })
            lsa = TruncatedSVD(n_components=min(10, len(texts)), random_state=42)
            lsa_matrix = lsa.fit_transform(tfidf_matrix)
            similarities = cosine_similarity(lsa_matrix)
            avg_similarity = float(np.mean(similarities))
            return {
                "topics": topics,
                "avg_document_similarity": avg_similarity,
                "explained_variance_ratio": lsa.explained_variance_ratio_.tolist()
            }
        except Exception as e:
            self.logger.error("Error in topic analysis: %s", e)
            return {"error": str(e)}


class EnhancedSentimentAnalyzer:
    """
    Orchestrates the sentiment analysis pipeline using specialized components.
    """
    def __init__(self, alpha_vantage_key: str = ""):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.alpha_vantage_key = alpha_vantage_key
        self.sentiment_analyzer = SentimentAnalyzer()
        self.news_collector = NewsCollector(self.sentiment_analyzer)
        self.reddit_collector = RedditCollector(self.sentiment_analyzer)
        self.google_trends_collector = GoogleTrendsCollector()
        self.topic_analyzer = TopicAnalyzer()

    def get_google_trends_data(self, ticker: str, timeframe: str = 'today 6-m') -> Dict[str, Any]:
        return self.google_trends_collector.get_google_trends_data(ticker, timeframe)

    def get_news_sentiment(self, ticker: str, num_articles: int = 10) -> Dict[str, Any]:
        return self.news_collector.get_news_sentiment(ticker, num_articles)

    def get_reddit_sentiment(self, ticker: str, subreddits: List[str] = None, limit: int = 50) -> Dict[str, Any]:
        if subreddits is None:
            subreddits = ['stocks', 'SecurityAnalysis', 'ValueInvesting', 'StockMarket', 'WallStreetBets', 'CryptoCurrency']
        return self.reddit_collector.get_reddit_sentiment(ticker, subreddits, limit)

    def analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        return self.sentiment_analyzer.analyze(text)

    def perform_topic_analysis(self, texts: List[str], n_topics: int = 5) -> Dict[str, Any]:
        return self.topic_analyzer.perform_topic_analysis(texts, n_topics)

    def get_comprehensive_sentiment_analysis(self, ticker: str) -> Dict[str, Any]:
        results = {
            "ticker": ticker,
            "analysis_timestamp": datetime.now().isoformat(),
            "data_sources": {}
        }
        print(f"Analyzing Google Trends for {ticker}...")
        trends_data = self.get_google_trends_data(ticker)
        results["data_sources"]["google_trends"] = trends_data
        print(f"Analyzing news sentiment for {ticker}...")
        news_sentiment = self.get_news_sentiment(ticker)
        results["data_sources"]["news_sentiment"] = news_sentiment
        print(f"Analyzing Reddit sentiment for {ticker}...")
        reddit_sentiment = self.get_reddit_sentiment(ticker)
        results["data_sources"]["reddit_sentiment"] = reddit_sentiment
        all_texts = []
        if "articles" in news_sentiment:
            for article in news_sentiment["articles"]:
                all_texts.append(f"{article.get('title', '')} {article.get('summary', '')}")
        if "posts" in reddit_sentiment:
            for post in reddit_sentiment["posts"]:
                all_texts.append(f"{post.get('title', '')} {post.get('text', '')}")
        if all_texts:
            print(f"Performing topic analysis for {ticker}...")
            topic_analysis = self.perform_topic_analysis(all_texts)
            results["data_sources"]["topic_analysis"] = topic_analysis
        sentiment_scores = []
        if news_sentiment.get("overall_sentiment", {}).get("vader_avg_sentiment"):
            sentiment_scores.append(news_sentiment["overall_sentiment"]["vader_avg_sentiment"])
        if reddit_sentiment.get("overall_sentiment", {}).get("avg_sentiment"):
            sentiment_scores.append(reddit_sentiment["overall_sentiment"]["avg_sentiment"])
        if sentiment_scores:
            overall_sentiment_score = np.mean(sentiment_scores)
            if overall_sentiment_score > 0.05:
                overall_sentiment_label = "Positive"
            elif overall_sentiment_score < -0.05:
                overall_sentiment_label = "Negative"
            else:
                overall_sentiment_label = "Neutral"
        else:
            overall_sentiment_score = 0
            overall_sentiment_label = "No Data"
        results["overall_sentiment"] = {
            "score": overall_sentiment_score,
            "label": overall_sentiment_label,
            "confidence": abs(overall_sentiment_score),
            "data_sources_count": len([k for k, v in results["data_sources"].items() if not v.get("error")])
        }
        return results