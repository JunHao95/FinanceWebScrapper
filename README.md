# Stock Financial Metrics Scraper

A high-performance Python application for scraping and analyzing financial metrics from multiple sources. Available as both a **CLI tool** and a **web application** with **advanced analytics**.

## 📊 System Architecture

![Finance Data Platform Architecture](finance_data_platform.png)

> **🔗 Live Demo**: [https://finance-web-scrapper.onrender.com](https://finance-web-scrapper.onrender.com)  
> **⚡ Keep-Alive**: Use a free Uptime Monitor to hit `/health` and prevent Render.com free tier spin-down.

## 🌟 Key Features

### Dual Interface
- **🖥️ CLI Mode**: Scriptable, automated analysis for scheduled runs
- **🌐 Web Interface**: Interactive browser-based analysis with tabbed interface

### Tabbed Web Interface
- **Tab 1 - Stock Details**: Individual stock metrics, technical indicators, CNN Fear & Greed Index; collapsible ticker cards with smooth animations
- **Tab 2 - Advanced Analytics**: Portfolio-level analytics with visual indicators showing when data is ready
- **Tab 3 - Stochastic Models**: Heston calibration (with SSE streaming), Markov chain credit transitions, interest rate models (CIR/Vasicek), ML/RL finance modules — all interactive with auto-run on scrape completion
- **Tab 4 - Trading Indicators**: Lazy-loaded 2×2 Plotly grid per ticker (Volume Profile, Anchored VWAP, Order Flow, Liquidity Sweep) with a composite Bullish/Bearish/Neutral bias badge and lookback dropdown
- **Smart Organization**: Clean separation of individual stock data vs. portfolio analysis
- **Stock Count Badge**: Shows number of analyzed stocks at a glance

### High-Performance Architecture
- ⚡ **Parallel Processing**: Concurrent data fetching with ThreadPoolExecutor
- 🔄 **Connection Pooling**: HTTP connection reuse for faster execution
- 🚀 **Fast Mode**: 90% speed boost with optimized concurrent processing
- 📈 **Scalable**: Handles multiple tickers efficiently

### Multi-Source Data Collection
- **Scrapers**: Yahoo Finance, Finviz, Google Finance
- **APIs**: Alpha Vantage, Finhub (API keys required)
- **Sentiment**: News, Reddit, Google Trends analysis
- **Indicators**: RSI, Moving Averages, Bollinger Bands, MACD

### Advanced Financial Analytics
- **Linear Regression**: Beta, Alpha analysis vs SPY benchmark (returns-based)
- **Correlation Analysis**: Correlation matrix and diversification metrics
- **Monte Carlo Simulation**: Value at Risk (VaR) and Expected Shortfall (ES)
- **PCA Analysis**: Portfolio structure with data standardization (3+ stocks)

### Fundamental Analysis & Investment Rating
- **4-Category Scoring**: Valuation (P/E, P/B, P/S), Profitability (ROE, ROA, margins), Financial Health (debt ratios, liquidity), Growth (revenue/earnings trends)
- **Investment Outlook**: 0-10 scale with 6 ratings: Strong Buy (≥8.0), Buy (≥7.0), Moderate Buy (≥6.0), Hold (≥5.0), Moderate Sell (≥4.0), Sell (<4.0)
- **Smart Parsing**: Handles financial notation (125.82B, 99.58M) and flexible metric extraction
- **Actionable Insights**: Automated strengths/concerns identification and investment summary

### AI Chatbot Assistant (Phase 10 / 10.1 / 12)
- **Floating chat widget**: Fixed bottom-right overlay with open/close toggle, accessible from any tab without interrupting analysis workflow.
- **Dual-agent personas**: Toggle between **QuantAssistant** (quant finance — derivatives, stochastic models, VaR, regime detection) and **FinancialAnalyst** (sell-side — fundamentals, P/E, EPS, revenue trends); unknown agent keys fall back to QuantAssistant for backward compatibility.
- **Scraped-data context**: Chat widget injects the current page's scraped ticker data (metrics, analytics, model outputs) into the system prompt so responses are grounded in the user's actual portfolio, not generic examples.
- **`/api/chat` route**: Accepts `{ message, agent, context }` JSON; dispatches to the appropriate system prompt; Groq API used when `GROQ_API_KEY` is set, stub response otherwise.

### Portfolio Health Summary Card (Phase 8 / 9)
- **Portfolio-level health score**: Composite card rendered above the Analytics tab showing weighted Sharpe ratio, regime distribution, and aggregate VaR across all scraped tickers.
- **Auto-run integration**: Health card initialises synchronously before AutoRun triggers so users see a live card updating in real time as regime badges resolve — no manual refresh needed.
- **Deep links**: Each metric in the health card links directly to the relevant section in the Analytics tab (e.g., clicking VaR jumps to the Monte Carlo panel for that ticker).
- **`/api/portfolio_sharpe`**: Returns annualised Sharpe, daily VaR, and expected shortfall computed from yfinance returns; uses `yf.Ticker().history()` to avoid multi-ticker DataFrame shape issues.

### Auto-Run Extended Analysis (Phase 7)
- **Zero-click analytics**: After each scrape completes, `autoRun.js` automatically fires regime detection (HMM) for every scraped ticker in parallel using `Promise.allSettled` — results populate the Analytics tab without user intervention.
- **MDP portfolio analysis**: When 2+ tickers are scraped, a Markov Decision Process run is triggered automatically and results injected into a dedicated auto-MDP panel; single-ticker scrapes silently skip MDP.
- **Isolated error handling**: Each per-ticker auto-run is wrapped independently — a failure on one ticker does not block others; failed tickers show a dash in their regime badge.

### Deep Analysis Modules (Milestone v2.1)
- **Financial Health Score** (Phase 13): Letter-grade scoring (A–F) based on current ratio, quick ratio, debt-to-equity, and interest coverage; expandable deep-analysis panel per ticker with expand-state preserved across re-scrapes
- **Earnings Quality** (Phase 14): Accruals ratio (net income vs OCF / total assets), cash conversion ratio (OCF / net income), and EPS consistency flag — flags whether reported earnings are backed by real cash flow
- **DCF Valuation** (Phase 15): 2-stage free cash flow DCF model — 5-year explicit projection (Stage 1) + Gordon Growth terminal value (Stage 2); adjustable WACC, growth rates; intrinsic value per share with premium/discount badge; recalculate button for scenario analysis

### Derivative Pricing
- **Options Pricing Calculator**: Black-Scholes, Binomial, Trinomial models
- **Implied Volatility Engine**: Newton-Raphson IV extraction with validation
- **Greeks Calculator**: Delta, Gamma, Theta, Vega, Rho
- **Model Comparison**: Side-by-side pricing with convergence analysis
- **Volatility Surface Viewer**: Interactive 3D Plotly visualization
  - Real-time options data from Yahoo Finance (auto-fallback to historical when market closed)
  - 3D surface with rotation/zoom, color-coded IV heatmap
  - ATM volatility term structure charts
  - Data quality filters: moneyness, volume, bid-ask spread
  - Works 24/7 with automatic live/historical data switching

### Data Persistence
- 💾 **MongoDB Integration**: Automatic local storage of time series data (CLI only)
- 🔍 **Queryable History**: Fast retrieval with indexed fields
- 🚫 **Deduplication**: Unique indexes prevent duplicate records
- 📊 **Analytics Ready**: Data structured for analysis

### Output & Reporting
- Multiple formats: CSV, Excel, Text reports
- Email reports with HTML formatting
- Summary comparison reports
- Interactive web visualizations

### Troubleshooting Snippets
- **📁 Location**: `snippets/python_snippets.py` (244 lines)
- **Purpose**: Short, focused snippets to reproduce and debug webapp functionality
- **8 Snippets**: 
  - Scrapers: Yahoo, Finviz, Google Finance, CNN Fear & Greed, Sentiment
  - Analytics: Fundamental analysis, Monte Carlo VaR, Correlation analysis
- **Usage**: `python snippets/python_snippets.py` (run from project root)
- **Import Example**: `from python_snippets import snippet_yahoo_scraper`
- **Key Feature**: Uses webapp's actual implementation classes for consistent results

### Trading Indicators (Phase 19 — Volume Profile)
- **GET /api/trading_indicators?ticker=AAPL&lookback=90**: Returns real Volume Profile data (`traces`, `layout`, `signal`, `bin_width_usd`, `poc`, `vah`, `val`) using proportional-overlap volume distribution. POC, VAH, and VAL are computed via greedy expansion to capture ≥70% of total volume (value area).
- **Volume Profile chart**: Dual-subplot Plotly figure — candlestick on the left, horizontal bar histogram on the right (shared y-axis). POC marked in orange, VAH/VAL in green/red dashed lines, 70% value area shaded in blue-transparent.
- **Price-in-value-area badge**: Displayed below the chart in green ("Price inside value area") or red ("Price outside value area") depending on where the latest close sits relative to VAH/VAL.
- **tradingIndicators.js**: Updated from Phase 18 stub to real `fetch` + `_renderTickerCard` with `Plotly.newPlot(..., { staticPlot: true })` and DOM badge rendering.

### Trading Indicators (Phase 20 — Anchored VWAP)
- **Anchored VWAP panel**: Rendered below the Volume Profile chart per ticker. Displays a candlestick chart (500px) with three AVWAP lines anchored to the 52-week High (blue), 52-week Low (orange), and most recent earnings date (purple).
- **Right-edge labels**: Plotly annotations pinned to the chart's right edge show each AVWAP line name plus its signed percentage distance from the current price (e.g. "52-wk High: +2.1%").
- **Convergence badge**: Warns when any AVWAP line is within 0.3% of current price; shows a muted confirmation when no lines converge.
- **Earnings-unavailable note**: For ETFs (GLD, TLT) and tickers with no past earnings, a grey note replaces the earnings AVWAP line and explains the omission.

### Trading Indicators (Phase 21 — Order Flow)
- **Order Flow panel**: Rendered below the AVWAP panel per ticker. Displays green/red delta bars (buy vs sell pressure per bar, computed as `(Close−Low)/(High−Low)×Volume`) with a cumulative delta line overlay on the right axis.
- **Volume Divergence badge**: Always visible below the chart — shows "⚠ Volume Divergence" with price and volume slope values when price and volume trends diverge over the last 10 bars, or a muted "✔ No divergence" when aligned.
- **Imbalance candle annotations**: ▲/▼ markers appear on bars where the body exceeds 70% of the high-low range AND volume exceeds 1.2× the 20-day average, flagging high-conviction directional moves.

### Trading Indicators (Phase 22 — Liquidity Sweep, Composite Bias & Tab Wiring)
- **Liquidity Sweep panel**: 4th cell of the 2×2 grid. Detects bullish/bearish sweep events using adaptive n (≥5% of bar count) with a look-ahead-safe loop bound `range(n, len−n)`. Displays sweep markers and dashed horizontal lines at swept price levels; shows "No confirmed swings in selected window (n=X)" when no swings are detected.
- **Composite bias badge**: Appears above the 2×2 grid for each ticker. Aggregates signals from all four sub-indicators into a single Bullish / Bearish / Neutral verdict with a one-line rationale naming the dissenting sub-indicator. Denominator counts only successfully computed modules (e.g., "3/4 indicators"); failed sub-indicators render as grey "unavailable" cells.
- **2×2 interactive grid**: Volume Profile (top-left), Anchored VWAP (top-right), Order Flow (bottom-left), Liquidity Sweep (bottom-right) — all charts use `responsive: true, displayModeBar: true, scrollZoom: true` for full interactivity.
- **Lookback dropdown**: 30 / 90 / 180 / 365 day selector in the tab header; changing selection clears the per-ticker session cache and re-fetches all charts automatically without requiring a re-scrape.
- **Lazy-load on tab activate**: Trading Indicators tab fetches data only when first activated; `TradingIndicators.clearSession()` called from `stockScraper.js` on each new scrape to prevent stale renders.

### Footprint Delta Heatmap — Backend (Phase 24-01)
- **`fetch_intraday(ticker, days=60)`**: Fetches 15-minute OHLCV data via `yf.Ticker().history(interval='15m')`, hard-capped at 60 days (yfinance intraday horizon limit), returning a tz-naive DatetimeIndex DataFrame.
- **`compute_footprint(df_15m, ticker)`**: Builds a per-day delta heatmap (buy − sell volume per adaptive price bin) as a Plotly dark-theme figure, adds a POC scatter and current-close reference line, and returns `{traces, layout, signal, cum_delta, total_volume}`. Signal is `bullish`/`bearish`/`neutral` based on a 5% cumulative-delta threshold.
- **`GET /api/footprint?ticker=AAPL&days=60`**: New Flask route returning the full footprint payload for a given ticker and day window.
- **5-voice composite bias**: `compute_composite_bias()` now accepts an optional `footprint_result` kwarg, extending the scoring denominator to 5 when footprint is available (backward-compatible — existing callers unchanged).

### Footprint Delta Heatmap — Frontend (Phase 24-02)
- **3-column Trading Indicators grid**: `.ti-2x2-grid` CSS expanded from 2 to 3 columns, adding a Footprint heatmap panel (row 2, position 2) and an empty placeholder cell for a future 6th indicator.
- **Parallel fetch**: `fetchForTicker` now fires `/api/trading_indicators` and `/api/footprint` simultaneously via `Promise.all`, eliminating the sequential fetch waterfall.
- **Footprint cell**: renders the heatmap with Plotly, shows a colour-coded cumulative delta badge (✔ Bullish / ⚠ Bearish / — Neutral with share count), and a note indicating the 60-day / 15m horizon.
- **Client-side 5-voice composite badge**: composite bias score is now computed in JS after both fetches resolve, including Footprint as the 5th voice (e.g. "Bullish (4/5)"), replacing the server-side 4-voice badge.

### Footprint Delta Heatmap — Test Suite (Phase 24-03)
- **11 unit tests** (`tests/test_unit_footprint.py`): cover `fetch_intraday` tz-stripping and empty-raise, `compute_footprint` keys/heatmap/signal logic, and 5-voice composite bias scenarios (all-available, unavailable fallback, dissenter).
- **3 integration tests** (`TestFootprintRoute`): verify `/api/footprint` schema on 200, JSON error on missing ticker, and 500 on invalid ticker.
- **2 regression tests** with a frozen 30-row 15m fixture (`tests/fixtures/footprint_15m_ohlcv.csv`): pin cumulative delta to `-189166.667` and signal to `bearish` — any numerical drift fails immediately.

### End-to-End Test Suite (Phase 23)
- **Three-tier test architecture**: Unit (pytest markers), Integration (Flask test client, 25 routes covered), and Regression (frozen fixture snapshots) tiers managed via `Makefile` targets (`make test-unit`, `make test-integration`, `make test-regression`).
- **Frozen fixture regression**: Analytics modules (correlation, Monte Carlo VaR, DCF, credit transitions) snapshot their outputs; any numerical drift breaks the regression tier immediately.
- **conftest.py fixtures**: Shared app factory, sample ticker data, and mock helpers eliminate boilerplate across all test files.

### Peer Comparison
- **GET /api/peers?ticker=AAPL**: Returns sector peers with P/E, P/B, ROE, and Operating Margin for each comparable company, plus percentile ranks showing where the primary ticker stands relative to peers.
- **Sector-Scoped Cache**: 30-minute TTL cache keyed by sector — tickers in the same sector share one fetch, avoiding redundant Finviz requests.
- **Updated Finviz parsing**: peer tickers now extracted from `data-boxover-ticker` span attributes (new 2025 layout); sector extracted from `sec_` screener link. Legacy `Similar` td fallback retained.
- **Peer Comparison UI**: `peerComparison.js` IIFE module renders percentile rows with above/below-median badges inside the Deep Analysis section. Shows a spinner during load, "Peer Comparison: Unavailable" on failure, and a collapsible "N/4 above median" header with an optional raw peer table on success.

### Collapsible Ticker Display
- **Click-to-Expand**: Ticker details collapsed by default for reduced clutter
- **Smooth Animations**: 0.4s transitions with arrow icon rotation (▼ → ▶)
- **Visual Feedback**: Gradient hover effects on ticker headers
- **Mobile-Friendly**: Less scrolling, faster navigation to relevant data

---

## 📦 Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/stock-scraper.git
cd stock-scraper
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure MongoDB (Optional for CLI)
```bash
# Install MongoDB (macOS with Homebrew)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Or use Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Verify MongoDB is running
python check_mongodb.py
```

### 5. Set Up Configuration

#### For CLI Mode
Copy and configure `config.json`:
```bash
cp config.json.example config.json
# Edit config.json with your settings
```

Example `config.json`:
```json
{
  "mongodb": {
    "enabled": true,
    "connection_string": "mongodb://localhost:27017/",
    "database": "stock_data"
  },
  "alpha_vantage": {
    "mode": "time_series_daily",
    "fallback_to_yahoo": true,
    "batch_size": 100,
    "enable_retry_on_rate_limit": true
  },
  "email": {
    "enabled": true
  }
}
```

#### For Web Mode
Create a `.env` file:
```bash
# API Keys (optional but recommended)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINHUB_API_KEY=your_finhub_key

# Email Configuration (required for email feature)
FINANCE_SENDER_EMAIL=your-email@gmail.com
FINANCE_SENDER_PASSWORD=your-app-password
FINANCE_SMTP_SERVER=smtp.gmail.com
FINANCE_SMTP_PORT=587
FINANCE_USE_TLS=True

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=False
PORT=5173
```

**Gmail Users**: Use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

---

## 🚀 Quick Start

### Web Application (Recommended for Interactive Use)

#### Starting the Web App

**Unix/macOS/Linux:**
```bash
chmod +x start_webapp.sh
./start_webapp.sh
```

**Windows:**
```cmd
start_webapp.bat
```

**Direct Python:**
```bash
python webapp.py
```

The web app will start on `http://localhost:5173`

#### Using the Tabbed Web Interface

1. **Enter Ticker Symbols**
   - Type stock ticker symbols separated by commas
   - Example: `AAPL, MSFT, GOOG, TSLA`

2. **Select Data Sources**
   - Choose "All Sources" for comprehensive analysis, or
   - Select specific sources (Yahoo Finance, Finviz, etc.)
   - Enable "Technical Indicators" and "Sentiment Analysis"

3. **Add API Keys** (Optional)
   - Enter Alpha Vantage API key for technical indicators
   - Enter Finhub API key for additional data
   - Or set them in `.env` file

4. **Analyze & View Results**
   - Click "🔍 Analyze Stocks"
   - Results appear in **Tab 1: Stock Details** (default view)
     - Shows CNN Fear & Greed Index
     - Individual stock cards with all metrics
     - Stock count badge shows number of analyzed stocks
   
5. **View Advanced Analytics**
   - Click **"� Advanced Analytics"** tab to see:
     - Correlation Analysis (2+ stocks)
     - PCA Analysis (3+ stocks)
     - Linear Regression vs SPY (per ticker)
     - Monte Carlo VaR/ES Analysis (per ticker)
   - Green "✓ Ready" badge appears when analytics are available

6. **Email Report** (Optional)
   - Enter email address
   - Add CC/BCC recipients if needed
   - Click "📨 Send Email Report"

### CLI Mode (For Automation & Scripting)

#### Basic Usage
```bash
# Single ticker
python main.py --tickers AAPL

# Multiple tickers
python main.py --tickers AAPL,MSFT,GOOG

# From file
python main.py --ticker-file tickers.txt

# With analytics
python main.py --tickers AAPL,MSFT,GOOG --all

# Email report
python main.py --tickers AAPL,MSFT --email recipient@example.com
```

#### Performance Mode
```bash
# Fast mode with parallel processing
python main.py --tickers AAPL,MSFT,GOOG --fast-mode --parallel

# High-performance with custom workers
python main.py --tickers AAPL,MSFT,GOOG,AMZN,TSLA,NVDA,META,NFLX \
  --fast-mode --parallel --max-workers 8 --format excel --summary
```

#### Automated Runs
```bash
./run_scraper.sh        # Production run
./uat_run_scraper.sh    # UAT/Testing run
```

---

## 🎯 Understanding the Tabbed Interface

### Tab 1: 📊 Stock Details (Default View)
**Shows individual stock information:**
- CNN Fear & Greed Index (market sentiment)
- Stock count badge (e.g., "2" for 2 stocks)
- Individual stock cards with:
  - Basic info (price, market cap, company name)
  - Valuation metrics (P/E, P/B, PEG, etc.)
  - Technical indicators (RSI, Moving Averages, MACD)
  - Sentiment analysis
  - Performance metrics

### Tab 2: 📈 Advanced Analytics
**Shows portfolio-level analytics:**
- **Correlation Analysis**: How stocks move together
- **PCA Analysis**: Portfolio structure (requires 3+ stocks)
- **Per-Ticker Analytics**:
  - **Regression vs SPY**: Beta, Alpha, R-Squared, Correlation
  - **Monte Carlo Analysis**: VaR, Expected Shortfall, scenarios

**Visual Indicators:**
- **Green "✓ Ready" badge**: Appears when analytics are available
- **"No Analytics Available" message**: Shows when:
  - Only 1 stock analyzed (need 2+ for portfolio analytics)
  - Analytics computation failed
  - No data available

### Navigation Tips
- **Default view**: Tab 1 (Stock Details) loads first
- **Quick switching**: Click tab buttons to switch views
- **Active tab indicator**: Purple bottom border and text
- **Stock count**: Badge on Tab 1 shows number of analyzed stocks
- **Smooth animations**: Content fades in when switching tabs

---

## 🔧 Advanced Analytics Explained

### Linear Regression vs SPY
**Purpose**: Understand how each stock moves relative to the S&P 500 benchmark

**Key Metrics:**
- **Beta**: Market sensitivity (Beta > 1 = more volatile than market)
- **Alpha**: Excess returns above market (positive = outperforming)
- **R-Squared**: How well returns correlate with SPY (higher = stronger relationship)
- **Correlation**: Direction of relationship (-1 to +1)

**Interpretation**:
- High Beta + Positive Alpha = Aggressive growth stock
- Low Beta + Positive Alpha = Stable outperformer
- High Beta + Negative Alpha = Volatile underperformer

### Monte Carlo Simulation
**Purpose**: Estimate potential losses under adverse market conditions

**Key Metrics:**
- **VaR (95%)**: Maximum expected loss at 95% confidence over 1 day
- **Expected Shortfall (ES)**: Average loss beyond VaR threshold
- **Best/Worst Case**: Potential outcomes in simulations

**Interpretation**:
- VaR: "95% confident we won't lose more than X% tomorrow"
- ES: "If we exceed VaR, average additional loss is Y%"
- Use for risk management and position sizing

### Correlation Analysis
**Purpose**: Measure diversification and portfolio risk

**Key Metrics:**
- **Correlation Matrix**: Pairwise correlations between stocks
- **Diversification Score**: Portfolio diversification quality

**Interpretation**:
- Correlation near +1: Stocks move together (low diversification)
- Correlation near 0: Independent movements (good diversification)
- Correlation near -1: Opposite movements (excellent hedge)

### PCA (Principal Component Analysis)
**Purpose**: Identify main drivers of portfolio variation

**Key Metrics:**
- **PC1, PC2, PC3**: Principal components explaining portfolio variance
- **Explained Variance**: How much variation each component captures

**Interpretation**:
- PC1 > 50%: Portfolio driven by single factor (market beta)
- PC1 < 40%: Well-diversified with multiple factors
- Use to understand portfolio concentration risk

---

## � Deployment & Keep-Alive

### Render.com Deployment

This app is deployed on Render.com free tier at: **https://finance-web-scrapper.onrender.com**

### Keep-Alive Solutions ⚡

Render.com free tier spins down after 15 minutes of inactivity. We've implemented **3 keep-alive solutions**:

#### 1. **Client-Side Keep-Alive** (Built-in) ✅
- Automatically pings server every 10 minutes when web page is open
- No setup required - works out of the box
- Pauses when tab is hidden to save resources

#### 2. **GitHub Actions Keep-Alive** (Recommended for 24/7) ⭐
- Automated workflow pings server every 10 minutes
- Completely free (GitHub Actions free tier)
- Works even when no one is using the website
- Setup: Just enable GitHub Actions in your repo

#### 3. **External Uptime Monitor** (Recommended for 24/7) ⭐
- Use a free service like [UptimeRobot](https://uptimerobot.com/) or [Cron-job.org](https://cron-job.org/)
- Ping the `/health` endpoint (`https://finance-web-scrapper.onrender.com/health`) every 5-10 minutes
- Completely free and prevents the server from spinning down
- **Note:** The included `keep_alive.py` script is now deprecated in favor of this zero-maintenance solution.

---

## �🐛 Troubleshooting

### Common Issues

#### 1. "I don't see analytics!"
**Solution**: Click the **"📈 Advanced Analytics"** tab at the top of results

**Why**: Analytics are in Tab 2, which is hidden by default. Tab 1 (Stock Details) shows first.

**Check for**: Green "✓ Ready" badge on Advanced Analytics tab - if present, analytics are loaded and ready to view.

#### 2. "Analytics tab says 'No Analytics Available'"
**Causes**:
- Only 1 stock analyzed (need 2+ for portfolio analytics)
- Backend couldn't compute analytics (check logs)
- Analytics data empty in API response

**Solution**:
```bash
# Check backend logs
tail -50 logs/webapp.log | grep -i "analytics"

# Should see: "Analytics computed: ['correlation', ...]"
```

#### 3. MongoDB Connection Failed (CLI)
```bash
# Check if MongoDB is running
brew services list | grep mongodb
# Or
docker ps | grep mongo

# Verify connection
python check_mongodb.py

# Disable MongoDB if not needed
# In config.json, set "mongodb.enabled" to false
```

#### 4. Web App Won't Start
```bash
# Check if port is in use
lsof -i :5173

# Try different port
export PORT=8000
python webapp.py

# Check Flask is installed
pip install flask
```

#### 5. API Rate Limits
- **Alpha Vantage**: Free tier = 25 requests/day, 5 calls/minute
- **Solution**: Use `--sources yahoo finviz` instead
- **Or**: Enable `fallback_to_yahoo` in config.json

#### 6. Email Not Sending
```bash
# Check .env file exists
ls -la .env

# For Gmail, use App Password, not regular password
# Enable "Less secure app access" if needed

# Test email configuration
python -c "from src.utils.email_utils import send_consolidated_report; print('Email module loaded successfully')"
```

#### 7. Volatility Surface Issues

**"Could not calculate IV for any options"**
- **Market Closed**: Normal behavior outside trading hours (9:30 AM - 4:00 PM ET)
- **Solution**: Feature automatically uses historical data (previous day's lastPrice)
- **Yellow Banner**: Appears when using historical data, explains data source
- **Test During Market Hours**: For live quotes, access during trading hours

**"No options with valid quotes"**
- **Cause**: All bid/ask prices are $0.00 (market makers not posting quotes)
- **Solution**: Wait for market hours or use more liquid tickers (SPY, QQQ, AAPL)
- **Check Filters**: Try `min_volume: 0` and `max_spread_pct: 0.50` for maximum coverage

**"JSON.parse error" or blank surface**
- **Fixed**: NaN/Inf values now converted to null for valid JSON
- **Solution**: Update to latest version with enhanced `convert_numpy_types()`
- **Verify**: `webapp.py` should handle NaN/Inf in float conversion

**Surface looks sparse or incomplete**
- **Cause**: Not enough options data points (illiquid ticker or extreme filters)
- **Solution**: 
  - Use liquid tickers: SPY (best), QQQ, AAPL, MSFT, TSLA
  - Reduce `min_volume` to 0
  - Increase `max_spread_pct` to 50%
- **Expected**: 200-500+ data points for quality surface

**Deep ITM options pricing errors**
- **Normal**: Some deep ITM options have market_price < intrinsic_value
- **Handled**: Skipped with 5% tolerance, logged as debug (not errors)
- **Impact**: Minimal, surface built from remaining valid options

---

## 🏗️ Project Structure

```
stock_scraper/
│
├── webapp.py                         # Flask web application
├── main.py                           # CLI application
├── requirements.txt                  # Python dependencies
├── config.json                       # CLI configuration
├── .env                              # Web app environment variables
├── start_webapp.sh                   # Unix/macOS startup script
├── start_webapp.bat                  # Windows startup script
├── run_scraper.sh                    # Production CLI script
├── uat_run_scraper.sh                # UAT CLI script
├── diagnose_volatility_surface.py    # Volatility surface diagnostics
├── validate_volatility_surface.py    # Volatility surface validation
│
├── templates/                        # Web application templates
│   └── index.html                    # Main web interface (with volatility surface viewer)
│
├── src/                              # Source code
│   ├── derivatives/                  # Derivative pricing modules
│   │   ├── options_pricer.py         # Black-Scholes, Binomial, Trinomial
│   │   ├── implied_volatility.py     # IV extraction engine
│   │   ├── volatility_surface.py     # 3D surface builder (445 lines)
│   │   └── trinomial_model.py        # Trinomial tree implementation
│   ├── scrapers/                     # Web scraper modules
│   ├── analytics/                    # Financial analytics
│   ├── indicators/                   # Technical indicators
│   ├── sentiment/                    # Sentiment analysis
│   └── utils/                        # Utility functions
│
├── data/                             # Data storage
├── output/                           # Output files
├── logs/                             # Log files
└── tests/                            # Test modules
    ├── conftest.py                   # Shared fixtures, Flask test client, marker registration
    ├── fixtures/                     # Frozen data: OHLCV CSVs, SPY .npy, Heston JSON
    └── test_*.py                     # 25 test files across unit, integration, and regression tiers
```

### Running Tests

```bash
make test-unit        # Fast unit tests only (no network calls)
make test-integration # Flask route integration tests
make test-regression  # Regression tests — pin Volume Profile, Order Flow, Heston RMSE, HMM regimes
make test             # All tiers sequentially
```

Tests are tiered via `pytest` markers (`unit`, `integration`, `regression`, `e2e`). Phase 23 added unit tests for `options_pricer`, `rl_models`, `financial_analytics`, and `ml_models` (TEST-03), plus regression tests that pin expected outputs for Volume Profile, Order Flow, Heston calibration, and HMM regime detection against frozen fixture data. Phase 23-04 added a Playwright E2E golden-path test (`tests/test_e2e_golden_path.py`) that exercises the full browser-to-server pipeline — enters AAPL, clicks Run Analysis, and verifies all four result tabs render without JS errors; all external scrapers and analytics API routes are mocked so no live network calls are required.

---

## 📊 Performance Benchmarks

### Speed Improvements
- **Connection Pooling**: 30-40% faster
- **Parallel Processing**: 2-3x faster for multiple tickers
- **Fast Mode**: Up to 90% reduction in execution time
- **Combined**: 5-10x faster than sequential without pooling

### Scalability
- **Concurrent Workers**: Supports 8-12 parallel workers efficiently
- **Memory Efficient**: Connection reuse reduces overhead

---

## 💡 Tips & Best Practices

### For Web Users
1. **Analyze 2+ stocks** to see portfolio analytics in Tab 2
2. **Look for "✓ Ready" badge** on Analytics tab when data is available
3. **Click Analytics tab** to view advanced metrics (hidden by default)
4. **Set API keys in .env** to avoid entering each time
5. **Use stock count badge** to verify all tickers processed

### For CLI Users
1. **Use ticker files** for large batches: `--ticker-file tickers.txt`
2. **Enable fast mode** for speed: `--fast-mode --parallel`
3. **Save bandwidth** with selective sources: `--sources yahoo finviz`
4. **Schedule runs** with cron for regular updates
5. **Monitor MongoDB** with `check_mongodb.py` after runs

### For Analytics
1. **Minimum 2 stocks** required for correlation and portfolio analytics
2. **3+ stocks** recommended for PCA analysis
3. **Beta interpretation**: >1 = more volatile, <1 = less volatile than market
4. **VaR use case**: Risk management and position sizing
5. **Correlation insights**: <0.7 = good diversification

### For Volatility Surface
1. **Use liquid tickers** for best results: SPY, QQQ, AAPL, MSFT, TSLA
2. **Set min_volume: 0** for maximum data coverage (recommended)
3. **Set max_spread_pct: 0.50** (50%) for realistic options filtering
4. **Expect 30-60 seconds** processing time for data fetching and interpolation
5. **Market hours**: Access during 9:30 AM - 4:00 PM ET for live quotes
6. **Historical fallback**: Feature works 24/7, auto-switches to previous day data when market closed
7. **Interpret patterns**: Look for volatility smile, term structure, and skew

---

## 🎯 Use Cases

### CLI Mode Best For:
- Scheduled/automated runs (cron jobs)
- Bulk analysis (large ticker lists)
- Data collection with MongoDB
- Batch reports
- Scripting and integration

### Web Mode Best For:
- Interactive analysis
- Ad-hoc queries
- Tabbed visualization
- Sharing with non-technical users
- Quick email reports

### Analytics Mode Best For:
- Portfolio risk assessment
- Beta/Alpha analysis
- Diversification analysis
- Monte Carlo simulations
- Quantitative research

---

## 📄 License

This project is for educational purposes. Web scraping may violate terms of service of some websites. Use responsibly and check each website's terms before scraping.

---

## 📝 Changelog

### Milestone v2.2 — Trading Indicators Complete (April 2026)
- 🆕 **Liquidity Sweep** (Phase 22): Adaptive-n swing detection with look-ahead-safe loop bounds; sweep markers and dashed price levels on chart; "No confirmed swings" fallback
- 🆕 **Composite Bias Badge** (Phase 22): Aggregates VP + AVWAP + Order Flow + Sweep into a single Bullish/Bearish/Neutral verdict with dissenter identification; denominator reflects only computed modules
- 🆕 **Full 2×2 Trading Indicators Tab** (Phase 22): Interactive Plotly grid per ticker; lookback dropdown (30/90/180/365d) clears cache and re-fetches on change; lazy-loaded on tab activation
- 🐛 **Phase 22 interactive charts**: Reverted `staticPlot: true` — all four indicator charts are fully interactive with scroll-zoom and modebar

### Phase 25 — Codebase Health Wave 1 (April 2026)
- 🐛 **BUG-01 — Debug prints removed**: All bare `print()` calls in `src/` replaced with `logging` calls at the appropriate level (`debug`/`info`/`warning`/`error`); production log output is now clean.
- 🐛 **BUG-02 — Advanced settings drawer fix**: `stockScraper.js` now references `settings-drawer` (the actual div ID) instead of the non-existent `advanced-settings`; open-state check updated to `classList.contains('drawer-open')`.
- 🐛 **BUG-03 — Peer percentile rank fixed**: `percentile_rank` in `webapp.py` replaced broken exact-float-equality check with `bisect.bisect_left`; rankings now span the full 0–100 range instead of always returning 50.
- 🔒 **SEC-01 — SECRET_KEY startup guard**: App now raises `RuntimeError` on startup if `SECRET_KEY` env var is missing; hardcoded fallback removed.
- 🔒 **SEC-02 — Email recipient allowlist**: `/api/send-email` validates the recipient against `config.json["recipients"]`; unrecognised addresses receive HTTP 403.
- 🔒 **SEC-03 — Rate limiting**: Flask-Limiter 4.1.1 added; 8 compute-heavy routes protected (10 req/min on scrape, 5 req/min on calibration/regime/RL routes).
- 🔒 **SEC-04 — API keys env-only**: Client-side Alpha Vantage and Finhub key inputs removed from the settings drawer; backend reads keys from environment variables only.

### Phase 21 Hotfix (April 2026)
- 🐛 **Order Flow panel not rendering**: Fixed a scoping bug in `tradingIndicators.js` where the Order Flow DOM block was placed outside `_renderTickerCard`, causing a `TypeError` at IIFE load time that silently prevented all Trading Indicators charts from rendering.

### Milestone v2.1 — Deeper Stock Analysis (March 2026)
- 🆕 **Financial Health Score** (Phase 13): Client-side letter-grade (A–F) scoring using current ratio, quick ratio, debt-to-equity, and interest coverage; collapsible deep-analysis panel with state preserved across re-scrapes
- 🆕 **Earnings Quality** (Phase 14): Accruals ratio, cash conversion ratio (OCF / net income), and EPS consistency flag — surfaces whether earnings are cash-backed; Net Income and Total Assets added to Yahoo scraper
- 🆕 **DCF Valuation** (Phase 15): 2-stage FCF DCF (5-year projection + Gordon Growth terminal value); adjustable WACC/growth inputs; intrinsic value per share with premium/discount badge; recalculate button for scenario analysis; AlphaVantage FCF with Yahoo fallback

### Latest Updates (Volatility Surface Release - December 2025)
- 🆕 **Interactive Volatility Surface Viewer**: 3D Plotly visualization with rotation/zoom
- 🆕 **Real-Time Options Data**: Yahoo Finance integration with live options chain
- 🆕 **Historical Data Fallback**: Auto-detects market closure, uses previous day's lastPrice
- 🆕 **Data Quality Filters**: Moneyness (70%-130%), bid/ask validation, spread filtering
- 🆕 **ATM Term Structure**: Extract at-the-money volatility across maturities
- 🆕 **NaN-Safe JSON Serialization**: Handles scipy interpolation edge cases (NaN/Inf → null)
- 🆕 **Market Status Warnings**: Yellow banner when using historical data
- ✅ **Production-Ready**: Works 24/7 with automatic live/historical data switching
- ✅ **Comprehensive Testing**: Diagnostics and validation tools included

### Previous Updates (Derivative Pricing Release)
- 🆕 **Options Pricing Calculator**: Black-Scholes, Binomial, Trinomial models
- 🆕 **Implied Volatility Engine**: Newton-Raphson IV extraction with validation
- 🆕 **Greeks Calculator**: Delta, Gamma, Theta, Vega, Rho
- 🆕 **Model Comparison**: Side-by-side pricing with convergence analysis

### Earlier Updates (Advanced Analytics Release)
- ✅ **Tabbed Interface**: Clean 2-tab layout (Stock Details + Advanced Analytics)
- ✅ **Advanced Analytics**: Linear regression, PCA, Monte Carlo, correlation
- ✅ **Returns-based Analysis**: All analytics use returns instead of prices
- ✅ **MongoDB Storage**: CLI-only time series persistence
- ✅ **Email Reporting**: HTML reports with analytics
- ✅ **Performance Optimization**: Parallel processing, connection pooling

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check troubleshooting section above
- Review logs: `logs/webapp.log` (web) or `logs/stock_scraper.log` (CLI)
- Check browser console (F12) for frontend errors

---

**Happy Analyzing! 📈💹**

