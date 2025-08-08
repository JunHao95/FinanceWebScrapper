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
from typing import Dict, List, Any
import random
from functools import wraps

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
        # Map tickers to company names for better matching
        company_names = {
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "GOOGL": "Alphabet",
            "AMZN": "Amazon",
            "TSLA": "Tesla",
            "META": "Meta",
            "NVDA": "Nvidia",
            # Add more as needed
        }
        search_terms = [ticker.lower()]
        if ticker.upper() in company_names:
            search_terms.append(company_names[ticker.upper()].lower())
        # Expanded, reliable public news RSS feeds (general and business)
        news_sources = [
            'http://feeds.bbci.co.uk/news/business/rss.xml',  # BBC Business
            'https://rss.nytimes.com/services/xml/rss/nyt/Business.xml',  # NYT Business
            'https://feeds.a.dj.com/rss/RSSWorldNews.xml',  # WSJ World News
            'https://www.npr.org/rss/rss.php?id=1006',  # NPR Business
            'https://news.google.com/rss/search?q={}&hl=en-US&gl=US&ceid=US:en'.format(
                '+'.join(search_terms)
            ),  # Google News search for ticker/company
        ]
        failed_feeds = []
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsCollector/1.0; +https://github.com/JunHao95/FinanceWebScrapper)"}
        for source in news_sources:
            try:
                for attempt in range(2):  # Retry once on transient errors
                    try:
                        resp = requests.get(source, timeout=7, headers=headers)
                        resp.raise_for_status()
                        feed = feedparser.parse(resp.content)
                        if not hasattr(feed, 'entries') or not feed.entries:
                            raise ValueError("No entries found in feed")
                        for entry in feed.entries[:max(1, num_articles//len(news_sources))]:
                            title = str(getattr(entry, 'title', ''))
                            summary = str(entry.get('summary', '')) if hasattr(entry, 'get') else ''
                            text_to_search = (title + " " + summary).lower()
                            if any(term in text_to_search for term in search_terms):
                                news_data.append({
                                    'title': title,
                                    'summary': summary,
                                    'published': str(entry.get('published', '')) if hasattr(entry, 'get') else '',
                                    'link': str(entry.get('link', '')) if hasattr(entry, 'get') else '',
                                    'source': source
                                })
                        break  # Success, break retry loop
                    except requests.exceptions.HTTPError as he:
                        code = he.response.status_code if he.response else None
                        # Skip known forbidden/unauthorized feeds
                        if code in [401, 403, 404, 429, 500, 400]:
                            failed_feeds.append({"source": source, "error": f"HTTP {code}: {he}"})
                            break
                        elif attempt == 1:
                            failed_feeds.append({"source": source, "error": str(he)})
                    except Exception as e:
                        if attempt == 1:
                            failed_feeds.append({"source": source, "error": str(e)})
            except Exception as e:
                failed_feeds.append({"source": source, "error": str(e)})
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
        result = {
            "overall_sentiment": overall_sentiment,
            "articles": sentiment_results[:10]
        }
        if failed_feeds:
            result["failed_feeds"] = failed_feeds
        return result


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


def rate_limit_handler(func):
    """Decorator to handle rate limiting"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 2
        base_delay = 0.05
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 3)
                    print(f"Rate limited. Waiting {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    raise
        return None
    return wrapper

class GoogleTrendsCollector:
    """Collects Google Trends data for a ticker"""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.pytrends = TrendReq(hl='en-US', tz=360)
            self.last_request_time = 0
            self.min_request_interval = 2 
            self.logger.info("Google Trends collector initialized")
        except Exception as e:
            self.logger.error("Error initializing Google Trends: %s", e)
            self.pytrends = None

    @rate_limit_handler
    def get_google_trends_data(self, ticker: str, timeframe: str = 'today 1-m', geo='', gprop='') -> Dict[str, Any]:
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
                self.logger.warning("No interest data found for the specified timeframe.")
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

    def get_google_trends_data(self, ticker: str, timeframe: str = 'today 1-m') -> Dict[str, Any]:
        return self.google_trends_collector.get_google_trends_data(ticker, timeframe)

    def get_news_sentiment(self, ticker: str, num_articles: int = 10) -> Dict[str, Any]:
        return self.news_collector.get_news_sentiment(ticker, num_articles)

    def get_reddit_sentiment(self, ticker: str, subreddits: List[str] = [], limit: int = 50) -> Dict[str, Any]:
        if not subreddits:
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
        print(f"debugging trends_data: {trends_data}")
        results["data_sources"]["google_trends"] = trends_data
        print(f"Analyzing news sentiment for {ticker}...")
        news_sentiment = self.get_news_sentiment(ticker)
        results["data_sources"]["news_sentiment"] = news_sentiment
        print(f"Analyzing Reddit sentiment for {ticker}...")
        reddit_sentiment = self.get_reddit_sentiment(ticker)
        results["data_sources"]["reddit_sentiment"] = reddit_sentiment
        all_texts = []
        if news_sentiment.get('articles'):
            for article in news_sentiment["articles"]:
                all_texts.append(f"{article.get('title', '')} {article.get('summary', '')}")
        if reddit_sentiment.get('posts'):
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

        """
        Sentiment vs Confidence 
        Sentiment: 
            - Measures the emotional tone/opinion of the stock
            - Ranges from -1 (very negative) to +1 (very positive)
        Confidence:
            - Measures the certainty of the sentiment analysis
            - Ranges from 0 (no confidence) to 1 (full confidence)
        
        Confidence Calculation:
            - Based on agreement between sources (news and Reddit)
            - Agreement between different models (VADER and FinBERT)
               * VADER : General purpose sentiment analysis, especially in informal or social media contexts
               * FinBERT : Financial sentiment analysis, tailored for financial texts with high contextual accuracy
            - Factors in data volume (number of articles/posts analyzed)
            - Final confidence is the average of agreement and volume confidence
        """
        confidence_factors = []

        # Check if sources (news and reddit) agree
        if news_sentiment.get("overall_sentiment") and reddit_sentiment.get("overall_sentiment"):
            news_score = news_sentiment["overall_sentiment"].get("vader_avg_sentiment", 0)
            reddit_score = reddit_sentiment["overall_sentiment"].get("avg_sentiment", 0)
            agreement = 1 - min(abs(news_score - reddit_score), 1)
            confidence_factors.append(agreement)

        # Factor in data volume
        total_items = (news_sentiment.get("overall_sentiment", {}).get("total_articles", 0) + 
                    reddit_sentiment.get("overall_sentiment", {}).get("total_posts", 0))
        volume_confidence = min(total_items / 50, 1.0)  # 50 items = full confidence
        confidence_factors.append(volume_confidence)

        # Calculate final confidence
        confidence = np.mean(confidence_factors) if confidence_factors else 0.5
        results["overall_sentiment"] = {
            "score": overall_sentiment_score,
            "label": overall_sentiment_label,
            "confidence": confidence,
            "data_sources_count": len([k for k, v in results["data_sources"].items() if not v.get("error")])
        }
        return results