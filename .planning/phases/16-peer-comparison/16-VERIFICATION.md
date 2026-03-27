---
phase: 16-peer-comparison
verified: 2026-03-27T00:00:00Z
status: human_needed
score: 11/11 automated must-haves verified
re_verification: false
human_verification:
  - test: "Scrape AAPL — confirm Peer Comparison section shows spinner during load, then four percentile rows with FAVOURABLE/UNFAVOURABLE badges"
    expected: "Collapsed header reads 'Peer Comparison: N/4 favourable'. Expanding shows P/E Ratio, P/B Ratio, ROE, Op. Margin rows each with a percentile label and a coloured badge."
    why_human: "Visual rendering in a live browser; spinner timing and badge colour can't be verified by static analysis."
  - test: "Confirm 'Comparable group: ...' peer label is visible in expanded view"
    expected: "A line reading 'Comparable group: MSFT, GOOGL, ...' (or equivalent sector peers) appears below the metric rows."
    why_human: "Requires live Finviz response with real peer data."
  - test: "Click 'Show peers' toggle — confirm raw peer table appears, second click hides it"
    expected: "Table with columns Ticker | P/E | P/B | ROE | Op. Margin renders on first click; button label changes to 'Hide peers'; second click collapses the table."
    why_human: "Toggle interaction requires a live browser session."
  - test: "Scrape a ticker Finviz has no similar-stocks data for — confirm graceful failure state"
    expected: "Peer Comparison section shows 'Peer Comparison: Unavailable' with muted (opacity 0.55) style and no expand arrow."
    why_human: "Depends on live Finviz response returning no peer data."
  - test: "Scrape MSFT (same Technology sector as AAPL) after AAPL to verify cache hit"
    expected: "Peer section for MSFT populates nearly instantly with no visible spinner delay — same sector cache reused."
    why_human: "Cache timing can only be perceived in a running browser session."
  - test: "DevTools console shows no red JS errors throughout the above flows"
    expected: "Zero JavaScript errors in the browser console."
    why_human: "Runtime JS errors require a live browser environment."
---

# Phase 16: Peer Comparison Verification Report

**Phase Goal:** Each ticker card displays the ticker's P/E, P/B, ROE, and operating margin as percentile ranks against 5–10 sector peers fetched from Finviz, with a toggle to reveal the raw peer data table — peers are cached in-memory for 30 minutes to avoid redundant network calls.
**Verified:** 2026-03-27
**Status:** human_needed — all automated checks pass; browser UI flows require human confirmation
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | GET /api/peers?ticker=AAPL returns JSON with sector, peers, peer_data, and percentiles keys | VERIFIED | 5/5 pytest tests pass including test_peers_returns_shape and test_peers_percentiles_have_value_and_rank |
| 2  | A second identical request within 30 minutes returns from cache (get_peer_data called only once) | VERIFIED | test_peers_cache_hit passes; _ticker_sector_map fast-path logic confirmed in webapp.py lines 2079-2106 |
| 3  | When Finviz returns fewer than 2 peers, /api/peers returns {error: ...} with HTTP 200 | VERIFIED | test_peers_fewer_than_two_peers passes; webapp.py line 2113 checks len(peer_data) < 2 |
| 4  | Network exception returns {error: ...} without raising unhandled exception | VERIFIED | test_peers_scrape_failure passes; try/except at webapp.py line 2149 |
| 5  | Operating Margin field present in get_peer_data output | VERIFIED | finviz_scraper.py line 247 maps "Operating Margin (Finviz)" -> op_margin; _scrape_data parses "Oper. Margin" header at line 92-93 |
| 6  | peerComparison.js exposes window.PeerComparison = { renderIntoGroup, clearSession } | VERIFIED | peerComparison.js line 225 confirmed; 230-line substantive IIFE implementation |
| 7  | peerComparison.js fetches /api/peers and renders spinner -> percentile rows -> raw table toggle | VERIFIED | fetch call at line 169; buildLoadingHTML/buildSuccessHTML/buildFailureHTML all present; LOWER_IS_BETTER inversion for P/E, P/B |
| 8  | pageContext.tickerData[ticker].peerComparison is written after fetch resolves | VERIFIED | peerComparison.js lines 180-188 write sector/peers/percentiles to pageContext on success |
| 9  | displayManager.js calls PeerComparison.renderIntoGroup after DCFValuation block | VERIFIED | displayManager.js lines 157-159 confirmed; positioned after DCFValuation block at lines 153-155 |
| 10 | index.html loads peerComparison.js in correct order (after dcfValuation.js, before displayManager.js) | VERIFIED | index.html lines 1334-1338 confirmed: healthScore -> earningsQuality -> dcfValuation -> peerComparison -> displayManager |
| 11 | Failure state renders "Peer Comparison: Unavailable" with muted style and no expand arrow | VERIFIED | buildFailureHTML() at line 31-37 uses opacity:0.55 and no onclick; no arrow element |

**Score:** 11/11 automated truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/test_peer_comparison.py` | pytest tests: shape, cache hit, failure states | VERIFIED | 5 tests, all GREEN (0.91s) |
| `webapp.py` | /api/peers route + _peer_cache + _ticker_sector_map | VERIFIED | Lines 2066-2151; sector-scoped 30-min TTL; percentile calculation; exception handling |
| `src/scrapers/finviz_scraper.py` | get_peer_data() returning sector, peers, peer_data | VERIFIED | Lines 151-260; 2025 Finviz HTML parsing (data-boxover-ticker spans + sec_ sector link); legacy fallback included |
| `static/js/peerComparison.js` | IIFE module with renderIntoGroup, clearSession, fetch to /api/peers | VERIFIED | 230 lines; full implementation including badge inversion fix (LOWER_IS_BETTER) from plan 03 iteration |
| `static/js/displayManager.js` | PeerComparison.renderIntoGroup call after DCFValuation | VERIFIED | Lines 156-159 |
| `templates/index.html` | peerComparison.js script tag before displayManager.js | VERIFIED | Line 1337 |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| webapp.py /api/peers | finviz_scraper.py FinvizScraper.get_peer_data | scraper.get_peer_data(ticker) at line 2109 | WIRED | Direct call; return value consumed immediately |
| _peer_cache | fetched_at TTL check | time.time() - entry['fetched_at'] < 1800 at line 2082 | WIRED | 30-minute TTL enforced; time module imported at line 19 |
| peerComparison.js renderIntoGroup | /api/peers?ticker=X | fetch('/api/peers?ticker=' + encodeURIComponent(ticker)) at line 169 | WIRED | Fire-and-forget; spinner injected before fetch; success/failure/catch all handled |
| displayManager.js createTickerCard | peerComparison.js renderIntoGroup | PeerComparison.renderIntoGroup(ticker, data, div) at line 158 | WIRED | Guarded with typeof check; positioned after DCFValuation block |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PEER-01 | 16-01, 16-02 | User can see P/E, P/B, ROE, op margin ranked as percentile against 5-10 sector peers | SATISFIED | Backend computes nearest-rank percentiles (webapp.py 2087-2130); frontend renders four metric rows in buildSuccessHTML() |
| PEER-02 | 16-02 | User can see which sector peer group was used | SATISFIED | peerComparison.js buildSuccessHTML() renders "Comparable group: {peers}" label; sector returned in /api/peers response |
| PEER-03 | 16-02 | Visual above/below-median indicator for each metric | SATISFIED | badge-success/badge-danger rendered per metric; LOWER_IS_BETTER inversion applied for P/E and P/B (badge shows FAVOURABLE/UNFAVOURABLE) |
| PEER-04 | 16-02 | Toggle "Show peers" to reveal raw peer data table | SATISFIED | peer-toggle-btn, peer-raw-table (display:none), _wireToggle() click handler all present in peerComparison.js |
| PEER-05 | 16-01, 16-02 | Module shows "Peer data unavailable" and hides percentile rows if fetch fails | SATISFIED | buildFailureHTML() renders muted unavailable state; _fetchAndRender catch + error response branch both call buildFailureHTML() |

All 5 PEER requirements satisfied by automated evidence.

---

## Anti-Patterns Found

No blockers or warnings found.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | — | — | No anti-patterns detected |

Scanned: peerComparison.js, webapp.py (/api/peers section), finviz_scraper.py (get_peer_data), displayManager.js (PeerComparison block), index.html (script tags). No TODO/FIXME/placeholder comments, no empty implementations, no console-log-only handlers.

---

## Human Verification Required

Plan 16-03 was a mandatory human browser checkpoint. The 16-03-SUMMARY.md records "Result: APPROVED" with two post-verification fixes applied (Finviz 2025 HTML parsing, badge logic inversion). However, the automated verifier cannot confirm the browser approval independently — the six items below require a human to re-confirm if any doubt exists about the summary's accuracy.

### 1. Spinner and percentile rows on success

**Test:** Enter "AAPL" and click Run Analysis. Watch the Peer Comparison sub-section within Deep Analysis.
**Expected:** Brief hourglass spinner, then collapsed header "Peer Comparison: N/4 favourable" with four expandable metric rows each showing an ordinal percentile and a FAVOURABLE/UNFAVOURABLE badge.
**Why human:** Visual timing and badge rendering require a live browser.

### 2. Comparable group label

**Test:** Expand the Peer Comparison section.
**Expected:** "Comparable group: MSFT, GOOGL, ..." line visible below metric rows.
**Why human:** Requires a live Finviz response.

### 3. Show/Hide peers toggle

**Test:** Click "Show peers" button.
**Expected:** Raw table with columns Ticker | P/E | P/B | ROE | Op. Margin appears; button changes to "Hide peers"; clicking again collapses the table.
**Why human:** DOM toggle interaction requires a live browser.

### 4. Failure state for no-peer ticker

**Test:** Scrape a ticker Finviz lists no similar stocks for.
**Expected:** Peer Comparison section shows "Peer Comparison: Unavailable" with greyed-out styling; no expand arrow.
**Why human:** Depends on live Finviz returning an empty peer list.

### 5. Cache hit performance

**Test:** Scrape AAPL, then scrape MSFT (same Technology sector) without reloading.
**Expected:** MSFT's peer section populates near-instantly (no spinner visible).
**Why human:** Cache timing is perceptible only in a running browser session.

### 6. No JavaScript console errors

**Test:** Open DevTools console and perform all tests above.
**Expected:** Zero red JS errors.
**Why human:** Runtime JS errors require a live browser environment.

---

## Gaps Summary

No automated gaps. All 11 must-haves verified. All 5 PEER requirements have implementation evidence. All 6 referenced commits exist in git history. All 5 pytest tests pass GREEN.

The only remaining items are the 6 human verification tests above, which replicate the plan 16-03 browser checkpoint. The 16-03-SUMMARY.md records user approval with two issues found and fixed (c89ee5e, 4891a48). If the user accepts that summary as the approval record, the phase is complete.

---

_Verified: 2026-03-27_
_Verifier: Claude (gsd-verifier)_
