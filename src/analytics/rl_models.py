"""
Reinforcement Learning Models Module

Four backend functions for the M6 RL curriculum:
  L1: Investment MDP — Bull/Bear/Crash policy iteration
  L2: Gridworld — 4x4 grid with optional wind, policy iteration
  L3: Portfolio Rotation (Policy Iteration) — SPY/IEF/SHY monthly MDP
  L4: Portfolio Rotation (Q-Learning) — model-free TD learning

All functions return plain Python dicts (numpy converted to lists).
"""

import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# L1: Investment MDP — Bull / Bear / Crash
# ---------------------------------------------------------------------------

def investment_mdp_policy_iteration(gamma: float = 0.95) -> dict:
    """
    Policy iteration on the 3-state Investment MDP.

    States  : ['Bull', 'Bear', 'Crash']
    Actions : ['Buy',  'Hold', 'Sell']

    Transitions P[s, a, s'] and rewards R[s, a] are hardcoded from the
    Notion L1 curriculum.  Expected outcome (γ=0.95):
        optimal_policy = ['Buy', 'Sell', 'Sell']
        v_star         ≈ [36.98, 35.68, 37.99]

    Returns
    -------
    dict with keys: states, actions, optimal_policy, v_star,
                    q_matrix (3×3), iterations
    """
    states  = ['Bull', 'Bear', 'Crash']
    actions = ['Buy',  'Hold', 'Sell']
    nS, nA  = 3, 3

    # Transition probabilities P[s, a, s']
    P = np.array([
        # a=Buy              a=Hold             a=Sell
        [[0.70, 0.20, 0.10], [0.60, 0.30, 0.10], [0.50, 0.40, 0.10]],  # s=Bull
        [[0.30, 0.50, 0.20], [0.40, 0.40, 0.20], [0.50, 0.40, 0.10]],  # s=Bear
        [[0.20, 0.40, 0.40], [0.20, 0.30, 0.50], [0.30, 0.50, 0.20]],  # s=Crash
    ])  # shape (3, 3, 3)

    # Immediate rewards R[s, a]
    R = np.array([
        [ 2.0,  1.5,  0.5],   # Bull
        [-1.0,  0.5,  1.0],   # Bear
        [-2.0, -0.5,  3.0],   # Crash
    ])

    def policy_eval(policy):
        """Exact Bellman solve: (I - γ P_π) V = r_π"""
        P_pi = np.array([P[s, policy[s]] for s in range(nS)])  # (nS, nS)
        r_pi = np.array([R[s, policy[s]] for s in range(nS)])  # (nS,)
        A    = np.eye(nS) - gamma * P_pi
        return np.linalg.solve(A, r_pi)

    # Initialise: all Buy (action 0)
    policy    = np.zeros(nS, dtype=int)
    V         = np.zeros(nS)
    iterations = 0

    while True:
        V = policy_eval(policy)
        # Q(s, a) = R(s,a) + γ Σ_{s'} P(s,a,s') V(s')
        Q = R + gamma * (P @ V)           # (nS, nA)
        new_policy = np.argmax(Q, axis=1)
        iterations += 1
        if np.all(new_policy == policy):
            break
        policy = new_policy

    return {
        'states':          states,
        'actions':         actions,
        'optimal_policy':  [actions[a] for a in policy],
        'v_star':          V.tolist(),
        'q_matrix':        Q.tolist(),   # shape (3, 3) — rows=states, cols=actions
        'iterations':      int(iterations),
    }


# ---------------------------------------------------------------------------
# L2: Gridworld 4×4
# ---------------------------------------------------------------------------

def gridworld_policy_iteration(use_wind: bool = False, gamma: float = 0.95) -> dict:
    """
    Policy iteration on a 4×4 gridworld.

    Layout (row-major, 0-indexed):
        [ 0  1  2  3]
        [ 4  5  6  7]
        [ 8  9 10 11]
        [12 13 14 15]

    Terminal states : cell 0 (top-left) and cell 15 (bottom-right).
    Step cost       : -1 for every non-terminal transition.
    Actions         : 0=UP, 1=RIGHT, 2=DOWN, 3=LEFT.
    Walls           : agent bounces (stays in place).

    Windy variant   : wind_col_p = [0.2, 0.4, 0.5, 0.2]
                      In column j, with probability wind_col_p[j] the
                      effective move is LEFT instead of the intended action.

    Returns
    -------
    dict with keys: policy (16-element list of '↑','→','↓','←','T'),
                    v_grid (4×4 list), iterations
    """
    nS   = 16
    nA   = 4
    TERM = {0, 15}

    wind_col_p = np.array([0.2, 0.4, 0.5, 0.2])

    # Arrow labels for actions 0–3
    arrow = ['↑', '→', '↓', '←']

    def _move(s, a):
        """Return next state after action a from state s (with wall bounce)."""
        row, col = divmod(s, 4)
        if   a == 0: row2, col2 = row - 1, col   # UP
        elif a == 1: row2, col2 = row,     col + 1  # RIGHT
        elif a == 2: row2, col2 = row + 1, col   # DOWN
        else:        row2, col2 = row,     col - 1  # LEFT

        if row2 < 0 or row2 > 3 or col2 < 0 or col2 > 3:
            row2, col2 = row, col   # bounce
        return row2 * 4 + col2

    def _left_of(s):
        """State to the left of s (bounce at wall)."""
        row, col = divmod(s, 4)
        col2 = max(col - 1, 0)
        return row * 4 + col2

    # Build transition tensors T[s, a, s'] and reward matrix R[s, a]
    T = np.zeros((nS, nA, nS))
    R = np.full((nS, nA), -1.0)   # default step cost

    for s in range(nS):
        if s in TERM:
            T[s, :, s] = 1.0          # terminal: stay
            R[s, :] = 0.0             # no reward at terminal
            continue

        row, col = divmod(s, 4)

        for a in range(nA):
            s_int = _move(s, a)
            if use_wind:
                pw = wind_col_p[col]
                s_wind = _left_of(s)     # wind pushes LEFT from current cell
                if s_int == s_wind:
                    # Both paths lead to same state
                    T[s, a, s_int] = 1.0
                else:
                    T[s, a, s_int] += (1 - pw)
                    T[s, a, s_wind] += pw
            else:
                T[s, a, s_int] = 1.0

    # Iterative Bellman backup (policy iteration)
    policy     = np.zeros(nS, dtype=int)   # initialise all UP
    V          = np.zeros(nS)
    iterations = 0
    tol        = 1e-8

    while True:
        # Policy evaluation — iterate to convergence
        while True:
            delta = 0.0
            V_new = np.zeros(nS)
            for s in range(nS):
                if s in TERM:
                    continue
                a    = policy[s]
                V_new[s] = R[s, a] + gamma * T[s, a] @ V
                delta = max(delta, abs(V_new[s] - V[s]))
            V = V_new
            if delta < tol:
                break

        # Policy improvement
        Q          = R + gamma * (T @ V)   # (nS, nA)
        new_policy = np.argmax(Q, axis=1)
        iterations += 1

        if np.all(new_policy == policy):
            break
        policy = new_policy

    # Build output
    policy_labels = []
    for s in range(nS):
        if s in TERM:
            policy_labels.append('T')
        else:
            policy_labels.append(arrow[policy[s]])

    v_grid = V.reshape(4, 4).tolist()

    return {
        'policy':     policy_labels,
        'v_grid':     v_grid,
        'iterations': int(iterations),
    }


# ---------------------------------------------------------------------------
# Helpers shared by L3 and L4
# ---------------------------------------------------------------------------

def _fetch_monthly_prices(start: str = '2004-01-01'):
    """Download monthly Adj Close for SPY, IEF, SHY via yfinance."""
    import yfinance as yf
    import pandas as pd

    # Use individual Ticker objects to avoid shared-session contamination when
    # multiple concurrent downloads are running (e.g. regime detection + MDP).
    series = {}
    for t in ('SPY', 'IEF', 'SHY'):
        hist = yf.Ticker(t).history(start=start, interval='1mo', auto_adjust=True)
        if hist.empty:
            raise ValueError(f"yfinance returned no data for {t}")
        series[t] = hist['Close']

    prices = pd.DataFrame(series)
    prices.index = prices.index.tz_localize(None)  # strip tz for consistent merging

    prices.dropna(how='all', inplace=True)
    return prices


def _build_states_and_rewards(prices, train_mask, cost_bps: int = 10):
    """
    Build state sequence and reward matrix for the 12-state MDP.

    States  : eq_mom(2) × bond_mom(2) × vol_regime(3) → index 0–11
    Actions : 5 equity/bond weight pairs
    Signals are lagged 1 month to prevent look-ahead bias.
    Vol terciles computed on training data only.

    Returns
    -------
    state_seq     : (T,) int array of state indices
    rew_seq       : (T, 5) float array of per-action monthly returns
    dates         : DatetimeIndex aligned with state_seq
    action_weights: list of (eq_wt, bond_wt) tuples
    cost          : float transaction cost per trade
    """
    import pandas as pd

    rets = prices.pct_change().dropna()

    # Rolling 12-month std of SPY for vol regime (annualised)
    vol_spy = rets['SPY'].rolling(12).std() * np.sqrt(12)

    # 12-month momentum (price return over 12 months)
    mom_spy = prices['SPY'].pct_change(12)
    mom_ief = prices['IEF'].pct_change(12)

    # Build signals DataFrame on the prices index, then lag 1 month
    signals_df = pd.DataFrame(
        {'mom_spy': mom_spy, 'mom_ief': mom_ief, 'vol': vol_spy},
        index=prices.index,
    ).shift(1)  # 1-month lag to prevent look-ahead

    # Align signals with returns (rets index is prices index shifted by 1 row)
    signals_df = signals_df.loc[rets.index].dropna()

    # Compute vol tercile thresholds on training data only
    train_vol = signals_df.loc[train_mask(signals_df.index), 'vol'].dropna()
    q33, q66  = np.nanpercentile(train_vol.values, [33.33, 66.67])

    def vol_regime(v):
        if v <= q33:   return 0
        elif v <= q66: return 1
        else:          return 2

    # State encoding: eq_mom(2) × bond_mom(2) × vol_regime(3)
    common_idx   = signals_df.index
    rets_aligned = rets.loc[common_idx]

    eq_mom_bin   = (signals_df['mom_spy'] > 0).astype(int)
    bond_mom_bin = (signals_df['mom_ief'] > 0).astype(int)
    vol_bin      = signals_df['vol'].apply(vol_regime)

    state_seq = (eq_mom_bin * 6 + bond_mom_bin * 3 + vol_bin).values.astype(int)

    # Actions: (equity_wt, bond_wt) for SPY and IEF
    action_weights = [
        (1.00, 0.00),
        (0.75, 0.25),
        (0.50, 0.50),
        (0.25, 0.75),
        (0.00, 1.00),
    ]
    cost = cost_bps * 1e-4

    spy_rets = rets_aligned['SPY'].values
    ief_rets = rets_aligned['IEF'].values
    rew_seq  = np.column_stack([
        ew * spy_rets + bw * ief_rets for ew, bw in action_weights
    ])  # shape (T, 5)

    return state_seq, rew_seq, common_idx, action_weights, cost


def _backtest(state_seq, rew_seq, action_weights, policy, cost, test_mask, dates,
              bench_ew=0.60, bench_bw=0.40):
    """
    Backtest a policy over the test period.

    Returns cumulative returns for RL strategy and 60/40 benchmark.
    """
    test_idx   = test_mask(dates)
    s_test     = state_seq[test_idx]
    r_test     = rew_seq[test_idx]

    prev_action = None
    rl_monthly  = []

    for t in range(len(s_test)):
        a   = int(policy[s_test[t]])
        ret = r_test[t, a]
        if prev_action is not None and prev_action != a:
            ret -= cost
        rl_monthly.append(ret)
        prev_action = a

    bench_monthly = bench_ew * r_test[:, 0] + bench_bw * r_test[:, 1]

    rl_cum    = (1 + np.array(rl_monthly)).cumprod() - 1
    bench_cum = (1 + bench_monthly).cumprod() - 1

    test_dates = [d.strftime('%Y-%m') for d in dates[test_idx]]

    # Performance metrics
    n_years = len(rl_monthly) / 12 or 1
    rl_ann  = (1 + rl_cum[-1]) ** (1 / n_years) - 1
    bm_ann  = (1 + bench_cum[-1]) ** (1 / n_years) - 1

    rl_vol  = np.std(rl_monthly, ddof=1) * np.sqrt(12)
    bm_vol  = np.std(bench_monthly, ddof=1) * np.sqrt(12)

    rl_sr   = rl_ann / rl_vol  if rl_vol  > 0 else 0.0
    bm_sr   = bm_ann / bm_vol  if bm_vol  > 0 else 0.0

    return {
        'test_dates':      test_dates,
        'rl_cumret':       rl_cum.tolist(),
        'benchmark_cumret': bench_cum.tolist(),
        'perf_metrics': {
            'rl_cagr':        round(rl_ann, 4),
            'rl_vol':         round(rl_vol, 4),
            'rl_sharpe':      round(rl_sr, 4),
            'bench_cagr':     round(bm_ann, 4),
            'bench_vol':      round(bm_vol, 4),
            'bench_sharpe':   round(bm_sr, 4),
        }
    }


# ---------------------------------------------------------------------------
# L3: Portfolio Rotation — Policy Iteration
# ---------------------------------------------------------------------------

def portfolio_rotation_policy_iteration(
    train_end:  str   = '2016-12-31',
    test_start: str   = '2017-01-01',
    gamma:      float = 0.99,
    cost_bps:   int   = 10,
) -> dict:
    """
    12-state MDP with policy iteration on SPY/IEF/SHY monthly data.

    Training  : 2004-01-01 → train_end
    Testing   : test_start → latest available

    Returns
    -------
    dict with keys: optimal_policy_table, test_dates,
                    rl_cumret, benchmark_cumret, perf_metrics
    """
    import pandas as pd

    prices = _fetch_monthly_prices()

    train_mask = lambda idx: idx <= pd.Timestamp(train_end)
    test_mask  = lambda idx: idx >= pd.Timestamp(test_start)

    state_seq, rew_seq, dates, action_weights, cost = _build_states_and_rewards(
        prices, train_mask, cost_bps
    )

    train_idx = train_mask(dates)
    s_train   = state_seq[train_idx]
    r_train   = rew_seq[train_idx]

    nS, nA = 12, 5

    # Empirical transition counts
    P_count = np.zeros((nS, nA, nS))
    R_sum   = np.zeros((nS, nA))
    R_cnt   = np.zeros((nS, nA))

    for t in range(len(s_train) - 1):
        s  = s_train[t]
        s2 = s_train[t + 1]
        for a in range(nA):
            P_count[s, a, s2] += 1
            R_sum[s, a]        += r_train[t, a]
            R_cnt[s, a]        += 1

    # Normalise transition probabilities
    row_sums = P_count.sum(axis=2, keepdims=True)
    row_sums = np.where(row_sums == 0, 1, row_sums)
    P_est    = P_count / row_sums

    R_est    = np.where(R_cnt > 0, R_sum / R_cnt, 0.0)

    # Policy iteration
    def policy_eval(policy):
        P_pi = np.array([P_est[s, policy[s]] for s in range(nS)])
        r_pi = np.array([R_est[s, policy[s]] for s in range(nS)])
        A    = np.eye(nS) - gamma * P_pi
        try:
            return np.linalg.solve(A, r_pi)
        except np.linalg.LinAlgError:
            return np.linalg.lstsq(A, r_pi, rcond=None)[0]

    policy     = np.zeros(nS, dtype=int)
    iterations = 0

    while True:
        V          = policy_eval(policy)
        Q          = R_est + gamma * (P_est @ V)   # (nS, nA)
        new_policy = np.argmax(Q, axis=1)
        iterations += 1
        if np.all(new_policy == policy):
            break
        policy = new_policy

    state_names = []
    for em in ['+', '-']:
        for bm in ['+', '-']:
            for vr in ['Low Vol', 'Mid Vol', 'High Vol']:
                state_names.append(f"EqMom{em} BndMom{bm} {vr}")

    action_names = ['100/0', '75/25', '50/50', '25/75', '0/100']
    optimal_policy_table = {
        state_names[s]: action_names[int(policy[s])] for s in range(nS)
    }

    bt = _backtest(state_seq, rew_seq, action_weights, policy, cost, test_mask, dates)

    return {
        'optimal_policy_table': optimal_policy_table,
        'iterations':           int(iterations),
        **bt,
    }


# ---------------------------------------------------------------------------
# L4: Portfolio Rotation — Q-Learning
# ---------------------------------------------------------------------------

def portfolio_rotation_qlearning(
    alpha:      float = 0.10,
    epochs:     int   = 200,
    eps_start:  float = 0.15,
    eps_end:    float = 0.01,
    optimistic: float = 0.005,
    gamma:      float = 0.99,
    cost_bps:   int   = 10,
) -> dict:
    """
    Model-free ε-greedy Q-learning on the 12-state portfolio MDP.

    Training  : 2004-01-01 → 2017-12-31
    Testing   : 2018-01-01 → latest available

    Returns
    -------
    dict with keys: q_table (12×5), greedy_policy,
                    test_dates, rl_cumret, benchmark_cumret, perf_metrics
    """
    import pandas as pd

    prices = _fetch_monthly_prices()

    train_end   = '2017-12-31'
    test_start  = '2018-01-01'

    train_mask = lambda idx: idx <= pd.Timestamp(train_end)
    test_mask  = lambda idx: idx >= pd.Timestamp(test_start)

    state_seq, rew_seq, dates, action_weights, cost = _build_states_and_rewards(
        prices, train_mask, cost_bps
    )

    train_idx = train_mask(dates)
    s_train   = state_seq[train_idx]
    r_train   = rew_seq[train_idx]
    T_train   = len(s_train)

    nS, nA = 12, 5

    # Optimistic Q-table initialisation
    Q = np.full((nS, nA), optimistic)

    rng = np.random.default_rng(42)

    for epoch in range(epochs):
        eps = eps_start + (eps_end - eps_start) * epoch / max(epochs - 1, 1)

        for t in range(T_train - 1):
            s  = s_train[t]
            s2 = s_train[t + 1]

            # ε-greedy action selection
            if rng.random() < eps:
                a = rng.integers(nA)
            else:
                a = int(np.argmax(Q[s]))

            r  = r_train[t, a]
            td = r + gamma * np.max(Q[s2]) - Q[s, a]
            Q[s, a] += alpha * td

    greedy_policy = np.argmax(Q, axis=1)

    action_names = ['100/0', '75/25', '50/50', '25/75', '0/100']
    state_names  = []
    for em in ['+', '-']:
        for bm in ['+', '-']:
            for vr in ['Low Vol', 'Mid Vol', 'High Vol']:
                state_names.append(f"EqMom{em} BndMom{bm} {vr}")

    greedy_policy_table = {
        state_names[s]: action_names[int(greedy_policy[s])] for s in range(nS)
    }

    bt = _backtest(state_seq, rew_seq, action_weights, greedy_policy, cost,
                   test_mask, dates)

    return {
        'q_table':           Q.tolist(),
        'greedy_policy':     greedy_policy_table,
        'action_names':      action_names,
        'state_names':       state_names,
        **bt,
    }


# ---------------------------------------------------------------------------
# User-configurable Portfolio MDP (Stochastic Models tab)
# ---------------------------------------------------------------------------

def portfolio_mdp_user_stocks(
    equity_ticker: str = 'SPY',
    bond_ticker:   str = 'IEF',
    start_date:    str = '2010-01-01',
    train_end:     str = '2020-12-31',
    test_start:    str = '2021-01-01',
    gamma:         float = 0.99,
    cost_bps:      int   = 10,
) -> dict:
    """
    Policy-iteration MDP on any user-supplied equity + bond ticker pair.

    State space  : eq_momentum(2) × bond_momentum(2) × vol_regime(3) = 12 states
    Actions      : 5 equity/bond weight allocations (100/0 → 0/100)
    Signals      : 12-month price momentum and rolling vol, lagged 1 month
    Vol thresholds: terciles computed on training data only (no look-ahead)
    Benchmark    : equal-weight 50/50 between the two tickers

    Returns
    -------
    dict with: optimal_policy, v_star, q_matrix, test_dates,
               rl_cumret, benchmark_cumret, perf_metrics, iterations
    """
    import pandas as pd
    import yfinance as yf

    eq = equity_ticker.strip().upper()
    bd = bond_ticker.strip().upper()

    if eq == bd:
        raise ValueError("Equity and bond tickers must be different.")

    # ── fetch data ────────────────────────────────────────────────────────────
    # Use individual Ticker objects to avoid shared-session contamination when
    # concurrent downloads (regime detection) are running simultaneously.
    import pandas as pd
    series = {}
    for t in (eq, bd):
        hist = yf.Ticker(t).history(start=start_date, interval='1mo', auto_adjust=True)
        if hist.empty:
            raise ValueError(f"No data returned for {t}. Check ticker symbol.")
        series[t] = hist['Close']

    prices = pd.DataFrame(series)
    prices.index = prices.index.tz_localize(None)  # strip tz for consistent merging

    prices.dropna(subset=[eq, bd], inplace=True)
    if len(prices) < 24:
        raise ValueError("Not enough monthly data (need ≥ 24 months).")

    rets = prices.pct_change().dropna()

    # ── signals (lagged 1 month to prevent look-ahead) ───────────────────────
    vol_eq  = rets[eq].rolling(12).std() * np.sqrt(12)
    mom_eq  = prices[eq].pct_change(12)
    mom_bd  = prices[bd].pct_change(12)

    signals_df = pd.DataFrame(
        {'mom_eq': mom_eq, 'mom_bd': mom_bd, 'vol': vol_eq},
        index=prices.index,
    ).shift(1).loc[rets.index].dropna()

    train_mask = lambda idx: idx <= pd.Timestamp(train_end)
    test_mask  = lambda idx: idx >= pd.Timestamp(test_start)

    # ── vol terciles on training data only ───────────────────────────────────
    train_vol = signals_df.loc[train_mask(signals_df.index), 'vol'].dropna()
    if len(train_vol) < 6:
        raise ValueError("Training window too short for vol tercile estimation.")
    q33, q66 = np.nanpercentile(train_vol.values, [33.33, 66.67])

    def vol_regime(v):
        if v <= q33:   return 0
        elif v <= q66: return 1
        return 2

    # ── state sequence ────────────────────────────────────────────────────────
    common_idx   = signals_df.index
    rets_aligned = rets.loc[common_idx]

    eq_mom_bin   = (signals_df['mom_eq'] > 0).astype(int)
    bond_mom_bin = (signals_df['mom_bd'] > 0).astype(int)
    vol_bin      = signals_df['vol'].apply(vol_regime)

    state_seq = (eq_mom_bin * 6 + bond_mom_bin * 3 + vol_bin).values.astype(int)

    # ── reward matrix ─────────────────────────────────────────────────────────
    action_weights = [
        (1.00, 0.00), (0.75, 0.25), (0.50, 0.50), (0.25, 0.75), (0.00, 1.00)
    ]
    cost = cost_bps * 1e-4

    eq_rets = rets_aligned[eq].values
    bd_rets = rets_aligned[bd].values
    rew_seq = np.column_stack([ew * eq_rets + bw * bd_rets for ew, bw in action_weights])

    # ── empirical MDP from training data ─────────────────────────────────────
    nS, nA = 12, 5
    s_train = state_seq[train_mask(common_idx)]
    r_train = rew_seq[train_mask(common_idx)]

    P_count = np.zeros((nS, nA, nS))
    R_sum   = np.zeros((nS, nA))
    R_cnt   = np.zeros((nS, nA))

    for t in range(len(s_train) - 1):
        s, s2 = s_train[t], s_train[t + 1]
        for a in range(nA):
            P_count[s, a, s2] += 1
            R_sum[s, a]        += r_train[t, a]
            R_cnt[s, a]        += 1

    row_sums = P_count.sum(axis=2, keepdims=True)
    P_est    = P_count / np.where(row_sums == 0, 1, row_sums)
    R_est    = np.divide(R_sum, R_cnt, out=np.zeros_like(R_sum), where=R_cnt > 0)

    # ── policy iteration ──────────────────────────────────────────────────────
    def policy_eval(pol):
        P_pi = np.array([P_est[s, pol[s]] for s in range(nS)])
        r_pi = np.array([R_est[s, pol[s]] for s in range(nS)])
        A = np.eye(nS) - gamma * P_pi
        try:
            return np.linalg.solve(A, r_pi)
        except np.linalg.LinAlgError:
            return np.linalg.lstsq(A, r_pi, rcond=None)[0]

    policy     = np.zeros(nS, dtype=int)
    iterations = 0
    V          = np.zeros(nS)
    Q          = np.zeros((nS, nA))

    while True:
        V          = policy_eval(policy)
        Q          = R_est + gamma * (P_est @ V)
        new_policy = np.argmax(Q, axis=1)
        iterations += 1
        if np.all(new_policy == policy):
            break
        policy = new_policy

    # ── backtest ──────────────────────────────────────────────────────────────
    test_idx   = test_mask(common_idx)
    s_test     = state_seq[test_idx]
    r_test     = rew_seq[test_idx]
    test_dates = [d.strftime('%Y-%m') for d in common_idx[test_idx]]

    prev_action = None
    rl_monthly  = []
    for t in range(len(s_test)):
        a   = int(policy[s_test[t]])
        ret = r_test[t, a]
        if prev_action is not None and prev_action != a:
            ret -= cost
        rl_monthly.append(ret)
        prev_action = a

    bench_monthly = 0.5 * r_test[:, 0] + 0.5 * r_test[:, -1]   # 50/50
    rl_cum        = (1 + np.array(rl_monthly)).cumprod() - 1
    bench_cum     = (1 + bench_monthly).cumprod() - 1

    n_years = max(len(rl_monthly) / 12, 0.1)
    rl_ann  = (1 + rl_cum[-1]) ** (1 / n_years) - 1
    bm_ann  = (1 + bench_cum[-1]) ** (1 / n_years) - 1
    rl_vol  = np.std(rl_monthly, ddof=1) * np.sqrt(12)
    bm_vol  = np.std(bench_monthly, ddof=1) * np.sqrt(12)

    # ── state / action labels ─────────────────────────────────────────────────
    action_names = ['100/0', '75/25', '50/50', '25/75', '0/100']
    state_names  = [
        f"{eq} Mom{'↑' if em else '↓'} {bd} Mom{'↑' if bm else '↓'} Vol:{vr}"
        for em in [1, 0] for bm in [1, 0]
        for vr in ['Low', 'Mid', 'High']
    ]
    policy_table = {state_names[s]: action_names[int(policy[s])] for s in range(nS)}

    # State visit counts in test period (for transparency)
    state_counts = {state_names[s]: int(np.sum(s_test == s)) for s in range(nS)}

    return {
        'equity_ticker':    eq,
        'bond_ticker':      bd,
        'optimal_policy':   policy_table,
        'state_names':      state_names,
        'action_names':     action_names,
        'v_star':           V.tolist(),
        'q_matrix':         Q.tolist(),
        'state_counts':     state_counts,
        'iterations':       int(iterations),
        'test_dates':       test_dates,
        'rl_cumret':        rl_cum.tolist(),
        'benchmark_cumret': bench_cum.tolist(),
        'perf_metrics': {
            'rl_cagr':      round(float(rl_ann),  4),
            'rl_vol':       round(float(rl_vol),  4),
            'rl_sharpe':    round(float(rl_ann / rl_vol) if rl_vol > 0 else 0, 4),
            'bench_cagr':   round(float(bm_ann),  4),
            'bench_vol':    round(float(bm_vol),  4),
            'bench_sharpe': round(float(bm_ann / bm_vol) if bm_vol > 0 else 0, 4),
            'benchmark_label': f'50/50 {eq}/{bd}',
        },
    }
