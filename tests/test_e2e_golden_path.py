"""
E2E golden path test — full browser flow with all external APIs mocked.

Flow: enter AAPL → Run Analysis → results appear → verify 4 tabs render.
All external calls (yfinance, scrapers, auto-analysis routes) are mocked so
no live network calls are made.
"""
import json
import pytest

pytestmark = pytest.mark.e2e

_MOCK_TRADING_INDICATORS = json.dumps({
    'ticker': 'AAPL',
    'volume_profile': {'poc': 175.0, 'vah': 180.0, 'val': 170.0},
    'vwap': 175.5,
    'order_flow': {'delta': 1200, 'cumulative_delta': 3500},
    'liquidity_sweep': {'sweep_detected': False},
    'composite_bias': 'bullish',
})

_MOCK_FOOTPRINT = json.dumps({
    'ticker': 'AAPL',
    'footprint': [],
})

_MOCK_REGIME = json.dumps({
    'success': True,
    'regime': 'Bull',
    'regimes': ['Bull'],
    'probabilities': [1.0],
})

_MOCK_PORTFOLIO_MDP = json.dumps({
    'success': True,
    'portfolio': {},
})


def test_golden_path_all_tabs_render(page, flask_server):
    """
    Golden path E2E (all external APIs mocked):
    1. Navigate to app
    2. Add AAPL via quick-ticker badge
    3. Click Run Analysis
    4. Wait for stock results to appear
    5. Verify each of the 4 result tabs has visible content
    6. Assert no unhandled JS page errors
    """
    page_errors = []
    page.on('pageerror', lambda err: page_errors.append(str(err)))

    # Intercept routes that fetch live market data
    page.route('**/api/trading_indicators**',
               lambda route: route.fulfill(status=200,
                                           content_type='application/json',
                                           body=_MOCK_TRADING_INDICATORS))
    page.route('**/api/footprint**',
               lambda route: route.fulfill(status=200,
                                           content_type='application/json',
                                           body=_MOCK_FOOTPRINT))
    page.route('**/api/regime_detection**',
               lambda route: route.fulfill(status=200,
                                           content_type='application/json',
                                           body=_MOCK_REGIME))
    page.route('**/api/stoch_portfolio_mdp**',
               lambda route: route.fulfill(status=200,
                                           content_type='application/json',
                                           body=_MOCK_PORTFOLIO_MDP))

    page.goto(flask_server, wait_until='networkidle')

    # Add AAPL via the quick-select badge (sets hidden #tickers field via chip-input)
    page.click('button.ticker-badge[data-ticker="AAPL"]')
    page.click('#runAnalysisBtn')

    # Wait for loading to finish and results section to become active
    page.wait_for_selector('#resultsSection.active', timeout=20000)

    # --- Tab 1: Stock Details ---
    # Wait for ticker card to be appended (JS appends before setting resultsSection.active,
    # but use wait_for_function to avoid Playwright's strict visibility check on nested elements)
    page.wait_for_function(
        "() => document.querySelector('#tickerResults').children.length > 0",
        timeout=10000,
    )
    page.wait_for_timeout(500)
    stocks_text = page.evaluate("document.getElementById('stocksTabContent').innerText")
    assert len(stocks_text.strip()) > 10, (
        f'Stocks tab rendered empty. innerText: {stocks_text!r}')

    # --- Tab 2: Advanced Analytics ---
    page.click('#analyticsTab')
    # Either real analytics or the "No Analytics Available" fallback message is acceptable
    analytics_text = page.evaluate("document.getElementById('analyticsTabContent').innerText")
    assert len(analytics_text.strip()) > 0, 'Analytics tab has no visible content'

    # --- Tab 3: Auto Analysis ---
    page.click('#autoanalysisTab')
    assert page.locator('#autoanalysisTabContent').is_visible()

    # --- Tab 4: Trading Indicators (served from mocked route) ---
    page.click('#tradingIndicatorsTab')
    # Give the JS time to call fetchForTicker and render the card with mocked data
    page.wait_for_function(
        "() => document.getElementById('tradingIndicatorsTabContent').innerText.trim().length > 0",
        timeout=8000,
    )
    trading_text = page.evaluate("document.getElementById('tradingIndicatorsTabContent').innerText")
    assert len(trading_text.strip()) > 0, 'Trading Indicators tab has no visible content'

    # No unhandled JS exceptions
    assert page_errors == [], 'Unhandled JavaScript errors:\n' + '\n'.join(page_errors)
