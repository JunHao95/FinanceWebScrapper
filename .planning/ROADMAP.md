# Roadmap: MFE Showcase Web App

## Overview

This milestone completes the Stochastic Models section and builds the ML-in-Finance section of an interactive MFE portfolio showcase. The work proceeds in four phases ordered by risk: fix math correctness first (Phase 1), close backend gaps so all planned features have callable APIs (Phase 2), wire the frontend with Plotly visualizations so recruiters can interact with live models (Phase 3), then build the ML-in-Finance module as a new main tab when the semester begins (Phase 4). Phases 1-3 complete the current semester deliverable; Phase 4 is the next semester deliverable.

Milestone v2.0 (One-Click Analysis Dashboard) adds Phases 6-8, delivering one-click analysis with smart form defaults, auto-run extended analytics, and a Portfolio Health summary card. Phase 9 closes gaps identified by the v2.0 milestone audit.

Milestone v2.1 (Deeper Stock Analysis) adds Phases 13-16, expanding each ticker card with a "Deep Analysis" group containing financial health grading, earnings quality scoring, DCF intrinsic value estimation, and peer percentile comparison.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Math Correctness** - Fix all recruiter-visible model errors in the stochastic model backends before any UI is wired (completed 2026-03-03)
- [x] **Phase 2: Backend Completeness** - Close backend gaps so every planned stochastic feature has a callable Flask API (completed 2026-03-05)
- [x] **Phase 3: Frontend Wiring and Visualization** - Wire all stochastic model sub-tabs with interactive inputs and Plotly charts (completed 2026-03-07)
- [x] **Phase 4: ML-in-Finance Module** - Build the new ML main tab with supervised, unsupervised, and time-series models (completed 2026-03-08)
- [x] **Phase 5: Stochastic Models UI Completion** - Wire Markov Chain sub-tab and Vasicek model selector (gap closure phase from v1.0 audit) (completed 2026-03-08)
- [x] **Phase 6: Form Streamlining & Smart Defaults** - Reduce visible form to ticker input + Run Analysis button; data sources default silently; allocation supports % Weight and Value modes (completed 2026-03-09)
- [x] **Phase 7: Auto-Run Extended Analysis After Scrape** - After scrape completes, Regime Detection and Portfolio MDP trigger automatically with inline results and status badges in the Analytics tab (completed 2026-03-10)
- [x] **Phase 8: Portfolio Health Summary Card** - A concise Portfolio Health card appears at the top of results after all analyses complete, showing VaR, Sharpe, and regime per ticker (completed 2026-03-10)
- [x] **Phase 9: Health Card Deep-Links & Auto-Run Hardening** - Health card metric clicks navigate to specific analytics sections; autoRun.js implicit global dependencies hardened (gap closure from v2.0 audit) (completed 2026-03-11)
- [ ] **Phase 10: Chatbot Integration** - Floating chatbot widget with QuantAssistant persona and Flask /api/chat backend
- [ ] **Phase 10.1: FinancialAnalyst Agent & Chatbot Toggle** (INSERTED) - FinancialAnalyst persona alongside QuantAssistant with UI agent toggle
- [ ] **Phase 11: Responsive Layout & Dashboard Customisation** - Mobile-first CSS and localStorage personalisation
- [ ] **Phase 12: Chatbot Context Wiring** - Structured page-state snapshot injected into every chatbot message
- [x] **Phase 13: Financial Health Score** - Altman Z-score-inspired composite A–F grade per ticker card, computed from already-scraped balance sheet fields with no new network calls (completed 2026-03-22)
- [x] **Phase 14: Earnings Quality** - Accruals ratio, cash conversion, and consistency flag per ticker card using scraped OCF/EPS, no new network calls (completed 2026-03-22)
- [x] **Phase 15: DCF Valuation** - FCF-based intrinsic value estimate with user-overridable WACC/growth inputs, recalculates without re-scraping (completed 2026-03-25)
- [x] **Phase 16: Peer Comparison** - Percentile ranks for P/E, P/B, ROE, and operating margin vs. 5–10 sector peers fetched from Finviz with a 30-minute in-memory TTL cache (completed 2026-03-27)
- [ ] **Phase 17: Bug Fixes — Re-scrape & DCF Badge** - Fix peer section silently empty on re-scrape (BREAK-01) and stale DCF premium badge after Recalculate (BREAK-02); update REQUIREMENTS.md v2.1 docs (gap closure from v2.1 audit)

## Phase Details

### Phase 1: Math Correctness
**Goal**: All six stochastic model backends produce results that a quantitative recruiter cannot fault — no non-monotone survival curves, no flat IV smiles, no Heston prices below intrinsic value, no HMM mislabeling of known stress periods, no Feller violations silently accepted.
**Depends on**: Nothing (first phase)
**Requirements**: MATH-01, MATH-02, MATH-03, MATH-04, MATH-05
**Success Criteria** (what must be TRUE):
  1. Running credit transition bond valuation on a par bond produces a price of 100 (within 0.01), confirming coupon discounting is time-correct.
  2. Heston calibration on SPY options produces a non-flat fitted IV smile where OTM options show measurably different implied vol than ATM, confirming relative MSE weighting is active.
  3. Setting CIR parameters that violate the Feller condition (2κθ < σ²) causes the calibrator to reject or flag them as invalid — the bad parameter set does not produce a silently wrong yield curve.
  4. Running HMM regime detection on SPY for March 2020 labels that period RISK_OFF (not RISK_ON), confirming label-switching is resolved.
  5. All model backends pass a documented validation check against a closed-form or textbook benchmark before Phase 2 begins.
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Fix coupon discounting (MATH-01) and CIR Feller hard constraint (MATH-03)
- [ ] 01-02-PLAN.md — Fix Heston relative MSE calibration (MATH-02) and HMM dual-criterion labels (MATH-04)
- [ ] 01-03-PLAN.md — Benchmark test suite validating all five fixes (MATH-05)

### Phase 2: Backend Completeness
**Goal**: Every stochastic model feature described in requirements has a callable Python function and a Flask route — no planned UI element will be blocked by a missing backend when frontend wiring starts.
**Depends on**: Phase 1
**Requirements**: MARKOV-01, MARKOV-02, MARKOV-03, MARKOV-04, MARKOV-05, MARKOV-06, CREDIT-01, CREDIT-02, CREDIT-03, CREDIT-04, CREDIT-05, RATE-01, RATE-02, RATE-03, RATE-04, RATE-05
**Success Criteria** (what must be TRUE):
  1. A POST to `/api/markov_chain` with a valid transition matrix returns a steady-state distribution and absorption probabilities in JSON.
  2. A POST to `/api/markov_chain` with a 3-state matrix returns an n-step power matrix (P^n) and the associated default term structure series.
  3. A POST to `/api/calibrate_bcc` returns calibrated BCC parameters and a fitted vs. market IV comparison JSON — the route exists and returns 200.
  4. A POST to `/api/regime` returns a `filtered_probs` time series (not just a final signal) suitable for rendering a probability chart over time.
  5. CIR and Vasicek route responses include a `feller_satisfied` boolean and `feller_ratio` value that the frontend can display as a badge.
**Plans**: 4 plans

Plans:
- [ ] 02-01-PLAN.md — Markov chain Python functions: steady_state_distribution, absorption_probabilities, portfolio_mdp_value_iteration (MARKOV-01 through MARKOV-05, CREDIT-02, CREDIT-03)
- [ ] 02-02-PLAN.md — Vasicek model functions + extend /api/interest_rate_model with model selector and feller_ratio (RATE-01 through RATE-05)
- [ ] 02-03-PLAN.md — /api/calibrate_bcc Flask route wrapping BCCCalibrator (CREDIT-01, CREDIT-04, CREDIT-05)
- [ ] 02-04-PLAN.md — /api/markov_chain unified Flask route for all five modes (MARKOV-06, CREDIT-01, CREDIT-02, CREDIT-03, CREDIT-05) [depends on 02-01]

### Phase 3: Frontend Wiring and Visualization
**Goal**: The Stochastic Models tab is fully interactive — every sub-tab has parameter inputs, a working submit button, and Plotly chart output matching the quality of the existing Volatility Surface tab. A recruiter can run any stochastic model live without touching code.
**Depends on**: Phase 2
**Requirements**: REGIME-01, REGIME-02, REGIME-03, REGIME-04, REGIME-05, HESTON-01, HESTON-02, HESTON-03, HESTON-04, HESTON-05, CALIB-01, CALIB-02, CALIB-03, CALIB-04, CALIB-05
**Success Criteria** (what must be TRUE):
  1. A user can enter a ticker and date range in the Regime Detection sub-tab, click Run, and see a filtered-probability time series chart with regime shading on the price chart — SPY March 2020 shows RISK_OFF shading.
  2. A user can enter Heston parameters in the Heston Pricing sub-tab and see both the Heston price and the Black-Scholes price for the same contract side-by-side, plus an IV surface chart showing a non-flat smile.
  3. A user can click Calibrate Heston for a default ticker and see a calibration progress indicator (iteration count or stage label) while the calibration runs, then see a fitted vs. market IV comparison and relative RMSE with a qualitative label (Good / Acceptable / Poor).
  4. The BCC calibration sub-tab exists, accepts inputs, and returns calibrated parameters and a fitted vs. market IV chart — the route is wired end-to-end.
  5. Every stochastic model sub-tab (Markov, Credit, Rates, Regime, Heston, Calibration) displays results as Plotly charts (not raw tables) and shows a CIR Feller condition badge where applicable.
**Plans**: 5 plans

Plans:
- [x] 03-01-PLAN.md — Regime Detection tab: webapp.py patch (prices/dates/regime_sequence) + two Plotly charts (REGIME-01 through REGIME-05)
- [ ] 03-02-PLAN.md — Heston Pricing tab: new sub-tab, /api/heston_iv_surface route, price cards, 3D IV surface (HESTON-01 through HESTON-05)
- [ ] 03-03-PLAN.md — Heston Calibration SSE: callback in HestonCalibrator, /api/calibrate_heston_stream, EventSource JS, IV chart + RMSE badge (CALIB-01, CALIB-03, CALIB-04)
- [ ] 03-04-PLAN.md — BCC Calibration tab: new sub-tab HTML + runBCCCalibration JS wiring to existing /api/calibrate_bcc (CALIB-02, CALIB-05)
- [ ] 03-05-PLAN.md — Markov/Credit/Rates Plotly upgrade: heatmap, survival curve, yield curve + Feller badge; full integration smoke test checkpoint (all 15 requirements verified)

### Phase 4: ML-in-Finance Module
**Goal**: A new Reinforcement Learning main tab exists in the UI, contains 4 interactive sub-tabs (Investment MDP, Gridworld, Portfolio Rotation PI, Portfolio Rotation QL), and allows a user to run all four RL demos with interactive parameter inputs and Plotly output — all backed by Python RL algorithms already implemented in rl_models.py.
**Depends on**: Phase 3
**Requirements**: ML-01, ML-02, ML-03, ML-04, ML-05, ML-06, ML-07, ML-08, ML-09
**Success Criteria** (what must be TRUE):
  1. A user can adjust gamma and click Run Policy Iteration in the Investment MDP sub-tab, seeing Buy/Sell/Sell policy cards, a V* bar chart, and a Q-value heatmap.
  2. A user can toggle wind and run Gridworld PI, seeing a 4×4 arrow policy grid and V* heatmap, converging in 4 iterations.
  3. A user can set train/test dates and run Portfolio Rotation (PI), seeing a cumulative return line chart vs 60/40 benchmark with CAGR/Vol/Sharpe metrics.
  4. A user can adjust alpha/epochs/epsilon and run Portfolio Rotation (QL), seeing the same line chart plus a 12×5 Q-table heatmap.
  5. The Reinforcement Learning tab appears as a top-level tab in the nav bar after Stochastic Models.
  6. All models use TimeSeriesSplit-equivalent leakage-free design: vol terciles on train data only, signals lagged 1 month.
**Plans**: 1 plan

Plans:
- [ ] 04-01-PLAN.md — Add RL nav button and complete rlTab HTML to index.html (ML-01 through ML-09)

### Phase 5: Stochastic Models UI Completion
**Goal**: Every stochastic model feature that has a backend API is reachable by a user from the UI — Markov Chain modes (steady-state, absorption, MDP) have an interactive sub-tab, and the Interest Rate sub-tab exposes both CIR and Vasicek via a model selector.
**Depends on**: Phase 2 (backends already complete), Phase 3 (UI structure already exists)
**Requirements**: MARKOV-01, MARKOV-02, MARKOV-03, MARKOV-04, MARKOV-05, MARKOV-06, RATE-02, RATE-03
**Gap Closure**: Closes gaps from v1.0 audit — Markov sub-tab missing, Vasicek UI path missing
**Success Criteria** (what must be TRUE):
  1. A user can open the Stochastic Models tab, navigate to a Markov Chain sub-tab, enter a transition matrix, and see the steady-state distribution rendered as a Plotly bar chart.
  2. A user can switch to an absorption mode form, enter an absorbing Markov chain, and see absorption probabilities.
  3. A user can switch to an MDP mode form and see the optimal policy and value function.
  4. A user can select "Vasicek" from a model selector in the Interest Rate sub-tab, click Run, and see a Vasicek yield curve rendered as a Plotly chart.
**Plans**: 1 plan

Plans:
- [ ] 05-01-PLAN.md — Markov Chain sub-tab HTML+JS + Vasicek model selector (MARKOV-01 to MARKOV-06, RATE-02, RATE-03)

### Phase 6: Form Streamlining & Smart Defaults
**Goal**: Users can run a full analysis by entering only ticker symbols and clicking one button — all data source configuration is hidden behind a collapsible advanced toggle, allocation supports both % Weight and Value modes with live weight feedback, and the submit button is prominent.
**Depends on**: Phase 5
**Requirements**: FORM-01, FORM-02, FORM-03, FORM-04, FORM-05, FORM-06, FORM-07, FORM-08
**Success Criteria** (what must be TRUE):
  1. A user can enter one or more ticker symbols and click "Run Analysis" without touching any other field — the form submits successfully using yahoo + finviz + google + technical as defaults.
  2. A user can click the "Advanced" toggle to reveal data source checkboxes and API key inputs, configure them, and re-collapse the section without losing the configured values.
  3. A user can switch to Value mode, enter currency amounts per ticker, and see "-> XX.X%" live next to each amount field as other amounts change; the computed weights are used in analysis.
  4. A user can select a currency (USD/SGD/EUR/GBP) in Value mode and see the label update without affecting the weight computation logic.
  5. Leaving all allocation fields blank in either mode submits with equal-weight allocation applied automatically, with no validation error shown to the user.
**Plans**: 2 plans

Plans:
- [ ] 06-01-PLAN.md — Equal-weights hint (Value mode) + collapsed-defaults note (FORM-01, FORM-02, FORM-03, FORM-04, FORM-05, FORM-06, FORM-07)
- [ ] 06-02-PLAN.md — Hero Run Analysis button CSS + full smoke test checkpoint (FORM-08)

### Phase 7: Auto-Run Extended Analysis After Scrape
**Goal**: After the main scrape completes, Regime Detection runs per ticker and Portfolio MDP runs for the portfolio without any user action — results appear inline in the Analytics tab alongside status badges that track each module's progress from running to done or failed.
**Depends on**: Phase 6
**Requirements**: AUTO-01, AUTO-02, AUTO-03, AUTO-04, AUTO-05
**Success Criteria** (what must be TRUE):
  1. After clicking "Run Analysis" for two tickers, both regime detection charts appear in the Analytics sub-tab without the user clicking any additional button; each chart shows bull/bear/neutral regime shading over the 2-year window.
  2. The Analytics tab shows a status badge per auto-run module that transitions from "Running..." to "Done" (or "Failed") without a page reload.
  3. Portfolio MDP output (optimal policy and value function) renders inline in the Analytics sub-tab after scrape; for a single-ticker input the MDP section is gracefully absent (no error, no empty chart).
  4. Auto-run regime charts use the same Plotly helpers already present in stochasticModels.js — no duplicate chart rendering code is introduced.
  5. If a regime detection API call fails for one ticker, the other ticker's chart still renders and the failed ticker shows a "Failed" badge without blocking the rest of the flow.
**Plans**: 2 plans

Plans:
- [ ] 07-01-PLAN.md — Create autoRun.js module: HTML scaffold injection, parallel API calls, Plotly rendering, badge transitions (AUTO-01, AUTO-02, AUTO-03, AUTO-04, AUTO-05)
- [ ] 07-02-PLAN.md — Wire AutoRun.triggerAutoRun into stockScraper.js displayResults() + human verify checkpoint (AUTO-01, AUTO-02, AUTO-03)

### Phase 8: Portfolio Health Summary Card
**Goal**: A Portfolio Health card appears at the top of results once all analyses complete, giving the user an at-a-glance summary of portfolio VaR, Sharpe ratio, and the current regime per ticker — each metric links directly to its detailed section in the Analytics tab.
**Depends on**: Phase 7
**Requirements**: HEALTH-01, HEALTH-02, HEALTH-03
**Success Criteria** (what must be TRUE):
  1. After a multi-ticker analysis completes, the Portfolio Health card is visible above the tab nav and shows VaR (95%), Sharpe ratio, a regime label per ticker (bull/bear/neutral), and the top correlation pair.
  2. Clicking a metric in the health card (e.g., the Sharpe ratio) scrolls or navigates to the corresponding section in the Analytics tab.
  3. For a single-ticker analysis, the health card appears showing only the metrics that are computable (VaR, Sharpe, regime) — correlation and PCA entries are absent, not shown as empty or "N/A".
**Plans**: 2 plans

Plans:
- [ ] 08-01-PLAN.md — Test scaffold + /api/portfolio_sharpe Flask backend route (HEALTH-01)
- [ ] 08-02-PLAN.md — portfolioHealth.js module + wiring into autoRun/stockScraper/index.html + human verify (HEALTH-01, HEALTH-02, HEALTH-03)

### Phase 9: Health Card Deep-Links & Auto-Run Hardening
**Goal**: Health card metric clicks navigate to the specific analytics subsection (not just the tab top); autoRun.js implicit global dependencies on `rlEscapeHTML`/`rlAlert` are hardened so MDP rendering cannot crash silently if rlModels.js load order changes.
**Depends on**: Phase 8
**Requirements**: HEALTH-02
**Gap Closure**: Closes gaps from v2.0 audit — HEALTH-02 shallow navigation, AUTO-05 fragile globals
**Success Criteria** (what must be TRUE):
  1. Clicking the VaR chip in the Portfolio Health card switches to the Analytics tab AND scrolls to the Monte Carlo / VaR section within that tab.
  2. Clicking the Sharpe chip switches to the Analytics tab AND scrolls to the Sharpe / returns section.
  3. If rlModels.js fails to load (simulated by removing its script tag), the regime detection auto-run still completes and only the MDP section shows a graceful error — no uncaught ReferenceError.
**Plans**: 1 plan

Plans:
- [ ] 09-01-PLAN.md — Add anchor IDs to analytics subsections + scrollIntoView in portfolioHealth.js; expose rlEscapeHTML/rlAlert via window.* and add guards in autoRun.js (HEALTH-02, AUTO-05)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 10.1 → 11 → 12 → 13 → 14 → 15 → 16

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Math Correctness | 3/3 | Complete   | 2026-03-03 |
| 2. Backend Completeness | 4/4 | Complete   | 2026-03-05 |
| 3. Frontend Wiring and Visualization | 5/5 | Complete   | 2026-03-07 |
| 4. ML-in-Finance Module | 1/1 | Complete   | 2026-03-08 |
| 5. Stochastic Models UI Completion | 1/1 | Complete   | 2026-03-08 |
| 6. Form Streamlining & Smart Defaults | 2/2 | Complete   | 2026-03-09 |
| 7. Auto-Run Extended Analysis After Scrape | 2/2 | Complete   | 2026-03-10 |
| 8. Portfolio Health Summary Card | 2/2 | Complete   | 2026-03-10 |
| 9. Health Card Deep-Links & Auto-Run Hardening | 1/1 | Complete   | 2026-03-11 |
| 10. Chatbot Integration | 2/2 | Complete | - |
| 10.1. FinancialAnalyst Agent & Chatbot Toggle | 2/2 | Complete | - |
| 11. Responsive Layout & Dashboard Customisation | 0/? | Not started | - |
| 12. Chatbot Context Wiring | 3/3 | Complete | - |
| 13. Financial Health Score | 1/2 | Complete    | 2026-03-22 |
| 14. Earnings Quality | 2/3 | Complete    | 2026-03-22 |
| 15. DCF Valuation | 1/2 | Complete    | 2026-03-26 |
| 16. Peer Comparison | 3/3 | Complete    | 2026-04-05 |
| 17. Bug Fixes — Re-scrape & DCF Badge | 0/1 | Not started | - |

### Phase 10: chatbot-integration
**Goal**: Integrate a chatbot in the FinanceWebScrapper web and having QuantAssisant agent residing in the chatbot
**Requirements**: [CHAT-01]
**Plans**: 2 plans

Plans:
- [x] 10-01-PLAN.md — Integrate QuantAssistant chatbot (backend endpoint + frontend widget) (CHAT-01)
- [ ] 10-02-PLAN.md — Upgrade backend to generate dynamic LLM replies (CHAT-01)


### Phase 10.1: FinancialAnalyst Agent & Chatbot Toggle (INSERTED)

**Goal**: A FinancialAnalyst agent exists alongside QuantAssistant in the chatbot, and users can toggle between the two agents via a UI control in the chat widget — each agent has a distinct persona and response style.
**Depends on**: Phase 10
**Requirements**: CHAT-02, CHAT-03
**Success Criteria** (what must be TRUE):
  1. The chatbot widget contains a toggle or selector that switches between QuantAssistant and FinancialAnalyst agents.
  2. Sending a message while FinancialAnalyst is selected returns a response from the FinancialAnalyst persona (distinct from QuantAssistant).
  3. Switching agents clears or visually separates the chat history so the user knows they are talking to a different agent.
  4. The active agent label is visible in the chat header at all times.
**Plans**: 2 plans

Plans:
- [ ] 10.1-01-PLAN.md — Test scaffold (Wave 0) + backend SYSTEM_PROMPTS dict + agent field dispatch in /api/chat (CHAT-02)
- [ ] 10.1-02-PLAN.md — CSS pill tab styles + chatbot.js agent state/toggle/history swap + human verify (CHAT-03)

### Phase 11: Responsive Layout & Dashboard Customisation
**Goal**: The app is fully usable on mobile and tablet (hamburger nav, stacked charts, fluid chip input) and supports dashboard personalisation via localStorage (saved ticker presets, pinned/reordered result cards, persisted settings).
**Depends on**: Phase 10
**Requirements**: RESP-01, RESP-02, RESP-03, DASH-01, DASH-02, DASH-03
**Success Criteria** (what must be TRUE):
  1. On a 375px-wide viewport, all tab navigation collapses to a hamburger menu and all Plotly charts stack vertically without horizontal scroll.
  2. The chip input and Run Analysis button are full-width and tappable on mobile.
  3. A user can save the current ticker set as a named preset; selecting it from a dropdown restores those tickers.
  4. A user can pin/reorder result cards; the order persists across page reloads via localStorage.
  5. Settings (preferred data source, any toggles) persist in localStorage across sessions.
**Plans**: 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 11 to break down)

### Phase 12: Integrating Chatbot to the Details in Stock Analysis, Stochastic models tabs etc so the chatbot can access the content scrapped

**Goal:** Every chatbot message includes a structured snapshot of current page state (scraped metrics, portfolio analytics, stochastic model outputs) appended to the agent system prompt — both QuantAssistant and FinancialAnalyst give contextually grounded, data-specific answers without any user action.
**Requirements**: CTX-01, CTX-02, CTX-03, CTX-04, CTX-05
**Depends on:** Phase 11
**Plans:** 3/3 plans complete

Plans:
- [ ] 12-01-PLAN.md — Wave 0 test scaffold: extend test_chat_route.py with failing tests for context injection and history wiring (CTX-01, CTX-02, CTX-03)
- [ ] 12-02-PLAN.md — Backend extension: /api/chat reads context + history, appends context to system prompt, includes history in Groq/Ollama payload (CTX-01, CTX-02, CTX-03)
- [ ] 12-03-PLAN.md — Frontend wiring: window.pageContext, buildContextSnapshot(), sendMessage() extension, context indicator UI, stochastic result hooks (CTX-04, CTX-05)

---

## v2.1 Milestone — Deeper Stock Analysis (Phases 13–16)

**Design decisions encoded here:**
- All four modules render into `div.deep-analysis-group` appended to each ticker card, below the existing Sentiment group
- Phase 13 creates the `div.deep-analysis-group` container; Phases 14–16 append into it
- Health (FHLTH), Quality (QUAL), and DCF modules fire in parallel after the primary scrape completes; Peers (PEER) fires after those three complete
- FHLTH IDs are used (not HEALTH, which is taken by v2.0 Portfolio Health Card)
- Peers is the only phase introducing a new external network call; all other phases derive from already-scraped data

### Phase 13: Financial Health Score
**Goal**: Each ticker card displays a composite financial health grade (A–F) derived from already-scraped balance sheet and profitability fields — no new network calls, computed purely from data available after the primary scrape.
**Depends on**: Phase 12
**Requirements**: FHLTH-01, FHLTH-02, FHLTH-03, FHLTH-04
**Success Criteria** (what must be TRUE):
  1. After scraping any ticker, the ticker card shows a financial health grade badge (A, B, C, D, or F) in the new "Deep Analysis" section at the bottom of the card.
  2. Expanding the grade badge reveals four sub-scores (liquidity, leverage, profitability, growth) with their individual values displayed numerically.
  3. A one-sentence explanation summarising the dominant positive and negative factors appears beneath the grade (e.g., "Strong ROE offset by high debt/equity").
  4. When one or more component data fields are absent from the scraped payload, the grade still renders with available sub-scores and a visible warning flag indicating which component is missing.
  5. The `div.deep-analysis-group` container is injected into every ticker card by `displayManager.js` so that Phases 14–16 can append their sections without modifying card HTML again.
**Plans**: 2 plans

Plans:
- [ ] 13-01-PLAN.md — healthScore.js module + displayManager/stockScraper/index.html wiring (FHLTH-01, FHLTH-02, FHLTH-03, FHLTH-04)
- [ ] 13-02-PLAN.md — Human verify checkpoint: browser end-to-end checks (FHLTH-01, FHLTH-02, FHLTH-03, FHLTH-04)

### Phase 14: Earnings Quality
**Goal**: Each ticker card displays an earnings quality label (High / Medium / Low) alongside three supporting metrics — accruals ratio, cash conversion ratio, and an earnings consistency flag — all derived from scraped OCF and EPS data without any new network calls.
**Depends on**: Phase 13 (deep-analysis-group container)
**Requirements**: QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05
**Success Criteria** (what must be TRUE):
  1. After scraping a ticker, the Deep Analysis section shows an earnings quality label of "High", "Medium", or "Low" with a colour-coded indicator.
  2. The accruals ratio value (Net Income minus OCF divided by Total Assets) is displayed as a numeric figure with two decimal places.
  3. The cash conversion ratio value (OCF divided by Net Income) is displayed as a numeric figure with two decimal places.
  4. An earnings consistency flag of "Consistent" or "Volatile" appears based on EPS growth stability, with a brief tooltip or label explaining the criterion.
  5. When OCF or Net Income data is absent from the scraped payload, the entire quality section renders "Insufficient Data" in place of the label and metrics — no JavaScript error is thrown.
**Plans**: 3 plans

Plans:
- [ ] 14-01-PLAN.md — Patch yahoo_scraper.py to expose Net Income and Total Assets fields; pytest scaffold (QUAL-02, QUAL-03)
- [ ] 14-02-PLAN.md — earningsQuality.js module + displayManager/stockScraper/index.html wiring (QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05)
- [ ] 14-03-PLAN.md — Human verify checkpoint: browser end-to-end checks (QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05)

### Phase 15: DCF Valuation
**Goal**: Each ticker card displays an FCF-based intrinsic value estimate (price per share) alongside the current price premium or discount, with user-overridable WACC and growth rate inputs that recalculate the estimate locally without triggering a new scrape.
**Depends on**: Phase 13 (deep-analysis-group container)
**Requirements**: DCF-01, DCF-02, DCF-03, DCF-04, DCF-05
**Success Criteria** (what must be TRUE):
  1. After scraping a ticker with available Alpha Vantage FCF data, the Deep Analysis section shows an intrinsic value estimate as a dollar figure per share.
  2. The card displays whether the current market price is at a premium or discount vs. the DCF estimate, expressed as a signed percentage (e.g., "+23% premium" or "-11% discount").
  3. The three key DCF assumptions (FCF growth rate, terminal growth rate, WACC) are visible alongside the estimate so a user can assess the model's inputs at a glance.
  4. Editing the WACC or growth rate input fields and clicking "Recalculate" updates the intrinsic value and premium/discount percentage without triggering a new scrape or page reload.
  5. When Alpha Vantage FCF data is absent or zero, the DCF section displays "DCF unavailable — FCF data missing" and suppresses all numeric outputs.
**Plans**: 2 plans

Plans:
- [ ] 15-01-PLAN.md — dcfValuation.js module + displayManager/stockScraper/index.html wiring (DCF-01, DCF-02, DCF-03, DCF-04, DCF-05)
- [ ] 15-02-PLAN.md — Human verify checkpoint: browser end-to-end checks (DCF-01, DCF-02, DCF-03, DCF-04, DCF-05)

### Phase 16: Peer Comparison
**Goal**: Each ticker card displays the ticker's P/E, P/B, ROE, and operating margin as percentile ranks against 5–10 sector peers fetched from Finviz, with a toggle to reveal the raw peer data table — peers are cached in-memory for 30 minutes to avoid redundant network calls.
**Depends on**: Phase 13 (deep-analysis-group container), Phase 14, Phase 15 (all three fire before peers)
**Requirements**: PEER-01, PEER-02, PEER-03, PEER-04, PEER-05
**Success Criteria** (what must be TRUE):
  1. After scraping a ticker, the Deep Analysis section shows four percentile rank values (P/E, P/B, ROE, operating margin) expressed as "Xth percentile" against the sector peer group.
  2. The peer group label (e.g., "Technology — comparable group: AAPL, MSFT, GOOGL ...") is visible so the user knows which companies were used as benchmarks.
  3. Each of the four metrics shows an above-median or below-median indicator (e.g., a coloured arrow or badge) so the user can assess relative positioning at a glance.
  4. A "Show peers" toggle reveals a table of raw peer data (ticker, P/E, P/B, ROE, operating margin) and hides it again on second click.
  5. When the Finviz peer fetch fails, times out, or returns fewer than two peers, the entire peer section renders "Peer data unavailable" and suppresses percentile rows — no unhandled exception surfaces to the user.
**Plans**: 3 plans

Plans:
- [ ] 16-01-PLAN.md — Backend: extend FinvizScraper.get_peer_data + /api/peers route with sector TTL cache + pytest scaffold (PEER-05)
- [ ] 16-02-PLAN.md — Frontend: peerComparison.js async module + displayManager/index.html wiring (PEER-01, PEER-02, PEER-03, PEER-04, PEER-05)
- [ ] 16-03-PLAN.md — Human verify checkpoint: browser end-to-end checks (PEER-01 through PEER-05)

### Phase 17: Bug Fixes — Re-scrape & DCF Badge
**Goal**: Peer comparison section renders correctly on re-scrape of the same ticker; DCF recalculate shows exactly one premium/discount badge; all 19 v2.1 requirements marked Complete in documentation.
**Depends on**: Phase 16
**Requirements**: PEER-01, PEER-02, PEER-03, PEER-04, PEER-05, DCF-02, DCF-04
**Gap Closure**: Closes BREAK-01 and BREAK-02 from v2.1 audit
**Success Criteria** (what must be TRUE):
  1. Scraping the same ticker twice in one session shows the peer comparison section both times — no silent skip on second scrape.
  2. Clicking Recalculate in the DCF section shows exactly one premium/discount badge (not two stale + fresh side-by-side).
  3. All 19 v2.1 requirements in REQUIREMENTS.md are marked `[x] Complete`.
**Plans**: 1 plan

Plans:
- [ ] 17-01-PLAN.md — Fix BREAK-01 (clearSession in stockScraper.js) + BREAK-02 (single DCF badge in dcfValuation.js) + REQUIREMENTS.md docs update (PEER-01 through PEER-05, DCF-02, DCF-04)
