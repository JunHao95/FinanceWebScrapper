# Phase 4: ML-in-Finance Module - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning
**Source:** PRD Express Path (~/.claude/plans/soft-humming-gadget.md)

<domain>
## Phase Boundary

This phase adds a new **"Reinforcement Learning"** main tab to the MFE portfolio showcase Flask SPA. It delivers 4 interactive sub-tab demos (L1–L4) backed by Python RL algorithms and rendered with Plotly charts. The work is scoped to RL only (not OLS/RF/PCA/ARIMA/GARCH from the roadmap requirements) — the PRD defines RL as the deliverable for this implementation.

Files created: `src/analytics/rl_models.py`, `static/js/rlModels.js`
Files modified: `webapp.py`, `templates/index.html`, `static/js/main.js`

</domain>

<decisions>
## Implementation Decisions

### Tab Structure
- New main tab labeled **"Reinforcement Learning"** added to nav bar after Stochastic Models
- 4 sub-tabs: L1 – Investment MDP, L2 – Gridworld, L3 – Portfolio Rotation (PI), L4 – Portfolio Rotation (QL)
- Same sub-tab HTML pattern as existing Stochastic Models tab

### Backend: `src/analytics/rl_models.py` (new file)

**L1 – `investment_mdp_policy_iteration(gamma=0.95)`**
- States: `['Bull','Bear','Crash']`, Actions: `['Buy','Hold','Sell']`
- Transitions + rewards hardcoded from Notion L1 exactly
- Uses `(I - γP_π)V = r_π` linear solve via `numpy.linalg.solve`
- Policy improvement: `argmax Q(s,a)`
- Expected: policy `['Buy','Sell','Sell']`, `v_star ≈ [36.98, 35.68, 37.99]` in 2 iterations
- Returns: `optimal_policy`, `v_star`, `q_matrix`, `iterations`

**L2 – `gridworld_policy_iteration(use_wind=False, gamma=0.95)`**
- 4×4 grid, terminal states: cell 1 (top-left) and cell 16 (bottom-right)
- Deterministic: step_cost=−1, bounce at walls
- Windy: `wind_col_p=[0.2,0.4,0.5,0.2]`, wind pushes LEFT with p_w per column
- Use iterative Bellman backup (not linear solve)
- Expected convergence: 4 iterations for both variants
- Returns: 16-element policy list, V grid (4×4), iterations

**L3 – `portfolio_rotation_policy_iteration(train_end, test_start, gamma, cost_bps)`**
- Fetch SPY/IEF/SHY monthly via `yfinance.download` from 2004-01-01
- 12 states: `eq_mom(2) × bond_mom(2) × vol_regime(3)`
- 5 actions: equity/bond weight pairs `[(1,0),(0.75,0.25),(0.5,0.5),(0.25,0.75),(0,1)]`
- Rewards: weighted monthly portfolio return minus transaction cost
- **No data leakage**: vol terciles computed on train mask only; signals lagged 1 month with `.shift(1)`
- Defaults: `train_end='2016-12-31'`, `test_start='2017-01-01'`, `gamma=0.99`, `cost_bps=10`
- Returns: `optimal_policy_table`, `test_dates`, `rl_cumret`, `benchmark_cumret` (60/40), `perf_metrics`

**L4 – `portfolio_rotation_qlearning(alpha, epochs, eps_start, eps_end, optimistic, gamma, cost_bps)`**
- Same 12-state, 5-action setup as L3
- Model-free ε-greedy TD learning
- Train 2004–2013, test 2018+ (val phase uses fixed best params from Notion)
- Defaults: `alpha=0.10`, `epochs=200`, `eps_start=0.15`, `eps_end=0.01`, `optimistic=0.005`
- Returns: `q_table` (12×5), `greedy_policy`, `test_dates`, `rl_cumret`, `benchmark_cumret`, `perf_metrics`

### API Routes: `webapp.py` (4 new routes)
- Lazy-import helper `get_rl_models()` to avoid top-level import cost
- Routes: `/api/rl_investment_mdp`, `/api/rl_gridworld`, `/api/rl_portfolio_rotation_pi`, `/api/rl_portfolio_rotation_ql`
- All POST, all use `convert_numpy_types()` (already defined in webapp.py) on responses
- Add after existing stochastic model routes (~line 1800)

### Frontend: `static/js/rlModels.js` (new file)
- 4 async functions: `runInvestmentMDP()`, `runGridworld()`, `runPortfolioRotationPI()`, `runPortfolioRotationQL()`
- Follow existing `runXxx()` pattern from `stochasticModels.js` (read inputs → spinner → POST → render)
- Reuse `renderAlert` pattern for loading/error states

### Chart Types (Plotly)
- **L1**: Bar chart (V* by state) + heatmap (Q-values: states × actions) + text cards for policy
- **L2**: Heatmap with unicode arrow annotations (↑→↓←) for policy grid; second heatmap for V* values; `go.Heatmap` with `text` and `texttemplate`
- **L3/L4**: Line chart (RL cumret vs 60/40 benchmark) + summary metrics table (CAGR, Vol, Sharpe)
- **L4 additional**: Plotly heatmap of 12×5 Q-table with annotated values

### HTML: `templates/index.html`
- Add `<button class="main-tab-btn" onclick="switchMainTab('rlTab')">Reinforcement Learning</button>` to main nav
- Add `<div id="rlTab">` with 4 sub-tabs
- L1 inputs: gamma slider (0.5–0.99, default 0.95)
- L2 inputs: wind toggle checkbox, gamma slider
- L3 inputs: train_end date, test_start date, gamma, cost_bps
- L4 inputs: alpha, epochs, eps_start, eps_end, optimistic
- Add `<script src="/static/js/rlModels.js"></script>`

### Tab Registration: `static/js/main.js`
- Register `rlTab` in the tab switching function (same pattern as existing main tabs)

### Technical Constraints (Locked)
- `yfinance.download` is already a dependency (used in `src/scrapers/yahoo_scraper.py`)
- `convert_numpy_types` already defined in `webapp.py` — reuse as-is, no duplication
- Implementation order: backend → routes → JS → HTML → main.js

### Claude's Discretion
- Exact HTML structure / CSS classes for RL sub-tabs (follow existing Stochastic Models patterns)
- Error handling for yfinance network failures
- Spinner/loading state implementation details
- Plotly color schemes and layout options

</decisions>

<specifics>
## Specific Ideas

**L1 Validation values (from Notion):**
- `optimal_policy = ['Buy', 'Sell', 'Sell']`
- `v_star ≈ [36.98, 35.68, 37.99]`
- Convergence in 2 iterations

**L2 Validation:**
- 4 iterations for both deterministic and windy variants
- Terminal cells (index 0 and 15) should show 'T' in policy output

**yfinance call:**
```python
yf.download(['SPY','IEF','SHY'], start='2004-01-01', period='max', interval='1mo')
```

**Gridworld arrows:** Unicode characters ↑→↓← for the 4 cardinal directions

**API verification commands:**
```bash
curl -X POST /api/rl_investment_mdp -d '{"gamma":0.95}' → optimal_policy: ["Buy","Sell","Sell"]
curl -X POST /api/rl_gridworld -d '{"use_wind":false}' → 16-element policy list
curl -X POST /api/rl_portfolio_rotation_pi → rl_cumret + benchmark_cumret arrays
curl -X POST /api/rl_portfolio_rotation_ql -d '{"alpha":0.1,"epochs":200}' → q_table (12×5)
```

</specifics>

<deferred>
## Deferred Ideas

- OLS factor regression, Random Forest, PCA, ARIMA, GARCH models (roadmap ML-01–ML-09 scope beyond RL) — out of scope for this PRD implementation
- Validation/backtest split UI controls (val phase uses fixed params from Notion)

</deferred>

---

*Phase: 04-ml-in-finance-module*
*Context gathered: 2026-03-08 via PRD Express Path*
