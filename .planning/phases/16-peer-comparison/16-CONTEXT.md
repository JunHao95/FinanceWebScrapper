# Phase 16: Peer Comparison - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Each ticker card displays the ticker's P/E, P/B, ROE, and operating margin as percentile ranks against 5–10 sector peers fetched from Finviz's "Similar Stocks" section, with a toggle to reveal the raw peer data table. Peers are cached in-memory per sector for 30 minutes. Phase 16 appends its section into the existing `div.deep-analysis-group` container created in Phase 13. No other deep-analysis sections are touched.

</domain>

<decisions>
## Implementation Decisions

### Fetch trigger & loading UX
- Peer fetch fires **automatically after scrape** — same timing as health score, earnings quality, DCF renders
- On cache miss: section header shows `📊 Peer Comparison  ⊗` (spinner) in collapsed state; section is not expandable until data arrives
- On cache hit (same sector scraped earlier): section populates **instantly** with no spinner
- Multiple tickers scraped at once: peer fetches fire **in parallel** — all start immediately after scrape completes
- Each ticker fires its own `/api/peers?ticker=X` request; backend deduplicates via sector cache
- **No retry button** on failure — failure is a static state; user re-scrapes to try again

### Peer selection method
- Peers sourced from **Finviz "Similar Stocks"** section on the ticker's quote page (`finviz.com/quote.ashx?t={ticker}`)
- Existing `finviz_scraper.py` already hits this URL — extend it to also extract the similar-stocks list
- For each peer ticker in that list: scrape their Finviz quote page to get P/E, P/B, ROE, operating margin (reuse existing `finviz_scraper.py` logic)
- The **scraped ticker is included** in the peer group for percentile calculation (N+1 total data points)
- **Minimum peers threshold**: if Finviz returns fewer than 2 comparable companies, render failure state and suppress all percentile rows

### Percentile display format
- **Collapsed header** (success state): `📊 Peer Comparison: 3/4 above median  ▼`
- **Collapsed header** (loading state): `📊 Peer Comparison  ⊗`
- **Collapsed header** (failure state): `📊 Peer Comparison: Unavailable` — muted style, no expand arrow
- **Expanded view — four metric rows**, each formatted as:
  - `P/E Ratio       45th percentile  [BELOW MEDIAN]`
  - Coloured badge: above median = `.badge-success` (green), below median = `.badge-danger` (red)
- Below the four metric rows: **"Show peers ▼" toggle** that reveals the raw peer table
- **Raw peer table columns**: Ticker | P/E | P/B | ROE | Op. Margin (no company name column)
- Peer group label visible in expanded view: e.g., "Comparable group: MSFT, GOOGL, META ..."

### Cache & failure handling
- **Cache key**: sector string (e.g., `"Technology"`) — shared across all tickers in the same sector
- **Cache store**: in-process Python dict in `webapp.py` — same pattern as `_ticker_validation_cache`
- **Cache structure**: `{ sector: { "data": [...], "fetched_at": timestamp } }`
- **TTL**: 30 minutes (`time.time() - fetched_at > 1800`)
- **New Flask route**: `GET /api/peers?ticker={ticker}` — returns `{ peers: [...], sector: "...", percentiles: {...} }` or `{ error: "..." }`
- **Failure triggers "Unavailable" state**: HTTP error, timeout, Finviz block, fewer than 2 peers returned
- Section hidden when failed: not expandable, no unhandled exception surfaces

### Claude's Discretion
- Exact CSS for the collapsed header states (spinner style, muted failure style)
- Element IDs and CSS class names for peer section elements
- Exact wording for the peer group label line in expanded view
- Percentile calculation method (nearest-rank vs. linear interpolation — both acceptable for N≈10)
- Timeout value for each individual peer Finviz scrape

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `finviz_scraper.py`: Already scrapes `P/E Ratio (Finviz)`, `P/B Ratio (Finviz)`, `ROE (Finviz)` from each ticker's Finviz quote page — extend to also parse the "Similar Stocks" section and expose `Operating Margin (Finviz)`
- `dcfValuation.js` / `earningsQuality.js`: Full module pattern to replicate — IIFE, `window.PeerComparison = { renderIntoGroup, clearSession }`
- `renderIntoGroup(ticker, data, cardRoot)`: Queries `#deep-analysis-content-{ticker}`, silently returns if not found (pattern from phases 13–15)
- `.badge`, `.badge-success`, `.badge-danger` (styles.css:824–836): Reuse for above/below median badges
- `_ticker_validation_cache` (webapp.py:2064): Reference pattern for in-process TTL cache

### Established Patterns
- Window global module pattern: `window.PeerComparison` follows `window.HealthScore` / `window.EarningsQuality` / `window.DCFValuation`
- Phase 13–15 modules return HTML strings from pure synchronous computation — Phase 16 differs: `renderIntoGroup` must fire an async `fetch('/api/peers?ticker=X')` call and update the DOM on response
- Post-scrape `pageContext` update: write `pageContext.tickerData[ticker].peerComparison = { sector, peers, percentiles }` after render (for FinancialAnalyst chatbot)
- Emoji-header collapsed state follows pattern: `📊 Peer Comparison: 3/4 above median  ▼`

### Integration Points
- `displayManager.js createTickerCard(ticker, data)`: Add `PeerComparison.renderIntoGroup(ticker, data, div)` call after DCFValuation call — this initiates the async fetch
- `index.html`: Add `<script src="/static/js/peerComparison.js">` after dcfValuation.js and before displayManager.js
- `stockScraper.js`: Write peerComparison results into `pageContext.tickerData[ticker]` after fetch resolves
- `webapp.py`: New route `GET /api/peers?ticker={ticker}` — calls backend peer fetch logic with sector cache
- `finviz_scraper.py`: Extend `_scrape_data()` to parse "Similar Stocks" list; add `get_peer_data(ticker)` method that returns peer tickers + their four metrics

</code_context>

<specifics>
## Specific Ideas

- Collapsed header format confirmed: `📊 Peer Comparison: 3/4 above median  ▼`
- The ticker itself is included in the peer group (N+1 points) — percentile reflects rank within the full comparable set
- Raw peer table is secondary disclosure: user must first expand the section, then click "Show peers ▼"
- Cache is sector-scoped: AAPL and MSFT both in Technology → single Finviz request serves both

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 16-peer-comparison*
*Context gathered: 2026-03-26*
