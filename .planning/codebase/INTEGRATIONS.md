# External Integrations

**Analysis Date:** 2026-04-26

## Market Data APIs

### Yahoo Finance
- **Library:** `yfinance`
- **Auth:** None (public, unofficial)
- **Usage:** Primary price/fundamentals source — OHLCV, financials, company info, options chains
- **Files:** `src/scrapers/yahoo_scraper.py` (`YahooFinanceScraper`), `src/analytics/financial_analytics.py`
- **Risk:** Unofficial API; subject to rate limits and breaking changes without notice

### Alpha Vantage
- **Env var:** `ALPHA_VANTAGE_API_KEY`
- **Auth:** API key in query string
- **Usage:** Supplemental price/earnings data
- **Files:** `src/scrapers/api_scraper.py` (`AlphaVantageAPIScraper`)
- **Rate limit:** 5 calls/min on free tier

### Finnhub
- **Env var:** `FINHUB_API_KEY`
- **Auth:** API key in query string
- **Usage:** Real-time quotes, earnings calendar, company news
- **Files:** `src/scrapers/api_scraper.py` (`FinhubAPIScraper`)

### CNN Fear & Greed Index
- **Auth:** None (public endpoint)
- **Usage:** Market sentiment indicator scraped from CNN
- **Files:** `src/scrapers/cnn_scraper.py` (`CNNFearGreedScraper`)
- **Risk:** HTML scraping — fragile to CNN page layout changes

### Finviz
- **Auth:** None (HTML scraping)
- **Usage:** Screener data, technical ratings, analyst estimates
- **Files:** `src/scrapers/finviz_scraper.py` (`FinvizScraper`)
- **Risk:** HTML scraping — no official API; IP rate limiting possible

### Google Finance
- **Auth:** None (HTML scraping)
- **Usage:** Supplemental price data
- **Files:** `src/scrapers/google_scraper.py` (`GoogleFinanceScraper`)
- **Risk:** HTML scraping — fragile

---

## Sentiment Sources

### Reddit (PRAW)
- **Env vars:** `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
- **Auth:** OAuth2 client credentials
- **Usage:** Subreddit post/comment sentiment (r/wallstreetbets, r/stocks, r/investing)
- **Files:** `src/sentiment/sentiment_analyzer.py` (`RedditCollector`)

### Google Trends
- **Library:** `pytrends`
- **Auth:** None (unofficial)
- **Usage:** Search interest trends for ticker symbols
- **Files:** `src/sentiment/sentiment_analyzer.py` (`GoogleTrendsCollector`)
- **Risk:** Unofficial library; blocked by Google rate limiting; marked unmaintained

### News RSS Feeds
- **Auth:** None (public)
- **Sources:** BBC, NYT, WSJ, NPR, Google News
- **Usage:** News headline collection for sentiment scoring
- **Files:** `src/sentiment/sentiment_analyzer.py` (`NewsCollector`)

---

## AI / LLM

### Groq Cloud (Primary)
- **Env var:** `GROQ_API_KEY`
- **Model:** `llama3-8b-8192`
- **Usage:** Chatbot responses, financial Q&A
- **Files:** `webapp.py` (chatbot route)

### Ollama (Fallback)
- **Endpoint:** `http://localhost:11434`
- **Auth:** None (local)
- **Usage:** Local LLM fallback when Groq unavailable
- **Files:** `webapp.py` (chatbot route)

### OpenAI SDK
- **Status:** Package installed, imported, but **unused** — dead import
- **Risk:** Confusion/dead dependency; safe to remove

---

## Sentiment ML Models

### FinBERT (Hugging Face)
- **Model:** `ProsusAI/finbert` (~500MB)
- **Auth:** None (public model)
- **Usage:** Financial-domain BERT sentiment classification
- **Files:** `src/scrapers/enhanced_sentiment_scraper.py`, `src/sentiment/sentiment_analyzer.py`
- **Status:** Disabled on cloud (memory constraint); runs locally only
- **Frontend relevance:** Heavy model load blocks web response — any frontend must account for async sentiment requests

### VADER (NLTK)
- **Auth:** None
- **Usage:** Lightweight rule-based sentiment scoring (fallback to FinBERT)
- **Files:** `src/sentiment/sentiment_analyzer.py`

---

## Email

### Gmail SMTP
- **Env vars:** `FINANCE_SENDER_EMAIL`, `FINANCE_SENDER_PASSWORD`
- **Library:** Python stdlib `smtplib`
- **Usage:** HTML financial report delivery; supports multiple recipients
- **Files:** `src/utils/email_utils.py` (1281 lines)
- **Config:** Recipients in `config.json`

---

## Database

### MongoDB (Local Only)
- **Library:** `pymongo`
- **Usage:** Optional local persistence for scraped data
- **Files:** `src/utils/mongodb_storage.py` (`MongoDBStorage`)
- **Status:** Explicitly disabled for web app; CLI (`main.py`) only
- **Cloud:** Not available on Render (no persistent disk on free tier)

---

## Hosting & Deployment

### Render
- **URL:** `https://finance-web-scrapper.onrender.com`
- **Plan:** Free tier (512MB RAM, spins down after inactivity)
- **Config:** `render.yaml`, `Procfile`, `runtime.txt`
- **Process:** `gunicorn webapp:app` (single worker)

### GitHub Actions
- **File:** `.github/workflows/keep-alive.yml`
- **Status:** Deprecated — replaced by external Uptime Monitor service

---

## Frontend Dependencies (CDN)

### Plotly.js
- **Version:** 2.27.0
- **Source:** CDN (loaded in `templates/index.html`)
- **Usage:** All charts — volatility surface, price history, portfolio metrics
- **Frontend enhancement note:** Plotly has official React (`react-plotly.js`) and Vue wrappers — direct migration path if adopting a framework

### Google Fonts
- **Fonts:** Inter, JetBrains Mono
- **Source:** CDN
- **Usage:** Typography across all UI

---

## Frontend Enhancement Integration Points

The following existing integration patterns are compatible with incremental frontend framework adoption:

| Integration Point | Current | Framework Path |
|---|---|---|
| API contract | 30+ `POST /api/*` JSON endpoints | No change needed — React/Vue fetches same endpoints |
| CORS | `flask-cors` already installed | Enable for dev server (`localhost:5173` etc.) |
| State management | `state.js` (global object) | Replace with React context / Zustand / Pinia |
| Charts | Plotly.js CDN | Use `react-plotly.js` or `vue-plotly` wrappers |
| Real-time updates | SSE stream (`/api/stream`) | `EventSource` API works identically in any framework |
| Auth | None currently | No breaking change for frontend adoption |

---

*Integrations analysis: 2026-04-26*
