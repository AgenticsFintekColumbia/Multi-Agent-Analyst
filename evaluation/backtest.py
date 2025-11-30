"""
Backtesting module for evaluation framework.

Handles:
- Information Coefficient (IC) computation with Newey-West adjustment
- Portfolio construction (long/short quantile-based)
- Transaction cost modeling (turnover-based)
- Performance metrics (CAGR, Sharpe, drawdown, etc.)
- Decay analysis across multiple horizons
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple

from .config import (
    DEFAULT_HORIZONS,
    PRIMARY_HORIZON,
    DEFAULT_QUANTILE_SIZE,
    DEFAULT_MAX_POSITION_WEIGHT,
    DEFAULT_COST_PER_SIDE_BPS,
    EXECUTION_DELAY_DAYS,
    DEFAULT_NW_LAGS,
)


def compute_ic_series(
    universe: pd.DataFrame,
    signal_col: str = "ai_signal",
    return_col: str = None,
    horizon: int = None,
) -> pd.Series:
    """
    Compute time series of Information Coefficients (ICs).
    
    For each as_of_date, computes the cross-sectional correlation
    between the AI signal and forward returns.
    
    Args:
        universe: DataFrame with signals and returns
        signal_col: Column name for AI signal
        return_col: Column name for forward return (if None, uses primary horizon)
        horizon: Forward return horizon (if None, uses primary)
        
    Returns:
        Series with index = as_of_date, values = IC (correlation)
    """
    if horizon is None:
        horizon = PRIMARY_HORIZON
    if return_col is None:
        return_col = f"forward_return_{horizon}d"
    
    # Group by as_of_date and compute correlation
    ic_values = []
    ic_dates = []
    
    for date, group in universe.groupby("as_of_date"):
        # Filter to valid signals and returns
        valid = group[
            group[signal_col].notna() &
            group[return_col].notna()
        ]
        
        if len(valid) < 2:  # Need at least 2 observations for correlation
            continue
        
        # Compute cross-sectional correlation
        ic = valid[signal_col].corr(valid[return_col])
        
        if not np.isnan(ic):
            ic_values.append(ic)
            ic_dates.append(date)
    
    return pd.Series(ic_values, index=ic_dates, name="IC").sort_index()


def compute_ic_statistics(
    ic_series: pd.Series,
    nw_lags: int = None,
) -> Dict[str, float]:
    """
    Compute IC statistics including Newey-West adjusted t-statistic.
    
    Accounts for autocorrelation in IC over time using Newey-West adjustment.
    
    Args:
        ic_series: Time series of ICs
        nw_lags: Number of lags for Newey-West (default: config default)
        
    Returns:
        Dictionary with:
        - mean_ic: Mean IC
        - std_ic: Standard deviation of IC
        - t_stat: Newey-West adjusted t-statistic
        - hit_ratio: Proportion of dates where IC > 0
        - n_observations: Number of dates
    """
    if nw_lags is None:
        nw_lags = DEFAULT_NW_LAGS
    
    if len(ic_series) == 0:
        # Return dict with None values for missing data (empty input)
        return {
            "mean_ic": None,
            "std_ic": None,
            "t_stat": None,
            "hit_ratio": None,
            "n_observations": 0,
        }
    
    mean_ic = ic_series.mean()
    std_ic = ic_series.std()
    
    # Newey-West adjusted t-statistic
    # Note: statsmodels expects a regression context, so we compute manually
    # For a simple mean, NW t-stat = mean / (NW-adjusted std error)
    n = len(ic_series)
    
    if n <= nw_lags + 1:
        # Not enough observations for NW adjustment
        t_stat = mean_ic / (std_ic / np.sqrt(n)) if std_ic > 0 else np.nan
    else:
        # Compute Newey-West standard error
        # Simplified: use autocorrelation-adjusted variance
        residuals = ic_series - mean_ic
        variance = np.var(residuals)
        
        # Add autocorrelation terms
        for lag in range(1, min(nw_lags + 1, n)):
            autocov = np.mean(residuals[:-lag] * residuals[lag:])
            # Bartlett kernel weight
            weight = 1 - (lag / (nw_lags + 1))
            variance += 2 * weight * autocov
        
        nw_se = np.sqrt(variance / n)
        t_stat = mean_ic / nw_se if nw_se > 0 else np.nan
    
    hit_ratio = (ic_series > 0).sum() / len(ic_series)
    
    return {
        "mean_ic": mean_ic,
        "std_ic": std_ic,
        "t_stat": t_stat,
        "hit_ratio": hit_ratio,
        "n_observations": n,
    }


def compute_decay_analysis(
    universe: pd.DataFrame,
    signal_col: str = "ai_signal",
    horizons: List[int] = None,
) -> pd.DataFrame:
    """
    Compute IC statistics for multiple forward horizons (decay analysis).
    
    Shows how signal strength decays over time.
    
    Args:
        universe: DataFrame with signals and returns
        signal_col: Column name for AI signal
        horizons: List of horizons to analyze (default: config default)
        
    Returns:
        DataFrame with columns: horizon, mean_ic, std_ic, t_stat, hit_ratio, n_obs
    """
    if horizons is None:
        horizons = DEFAULT_HORIZONS
    
    results = []
    
    for horizon in horizons:
        return_col = f"forward_return_{horizon}d"
        
        if return_col not in universe.columns:
            continue
        
        ic_series = compute_ic_series(
            universe=universe,
            signal_col=signal_col,
            return_col=return_col,
            horizon=horizon,
        )
        
        stats = compute_ic_statistics(ic_series)
        stats["horizon"] = horizon
        
        results.append(stats)
    
    return pd.DataFrame(results)


def construct_portfolio(
    universe: pd.DataFrame,
    as_of_date: pd.Timestamp,
    signal_col: str = "ai_signal",
    quantile_size: float = None,
    max_position_weight: float = None,
) -> pd.Series:
    """
    Construct portfolio weights for a given date.
    
    Strategy:
    - Rank all names by AI signal
    - Long top quantile, short bottom quantile
    - Equal-weight within each side
    - Enforce max position weight (diversification constraint)
    
    Args:
        universe: DataFrame with signals
        as_of_date: Date to construct portfolio for
        signal_col: Column name for AI signal
        quantile_size: Size of top/bottom quantiles (default: config default)
        max_position_weight: Max weight per name (default: config default)
        
    Returns:
        Series with index = ticker/cusip, values = portfolio weights
        (positive = long, negative = short, sum = 0 for dollar-neutral)
    """
    if quantile_size is None:
        quantile_size = DEFAULT_QUANTILE_SIZE
    if max_position_weight is None:
        max_position_weight = DEFAULT_MAX_POSITION_WEIGHT
    
    # Filter to this date
    date_data = universe[universe["as_of_date"] == as_of_date].copy()
    
    # Filter to valid signals
    date_data = date_data[date_data[signal_col].notna()].copy()
    
    if len(date_data) < 2:
        return pd.Series(dtype=float)
    
    # Rank by signal
    date_data = date_data.sort_values(signal_col, ascending=False)
    
    n = len(date_data)
    n_long = max(1, int(n * quantile_size))
    n_short = max(1, int(n * quantile_size))
    
    # Long top quantile
    long_names = date_data.head(n_long)
    # Short bottom quantile
    short_names = date_data.tail(n_short)
    
    # Equal-weight within each side
    long_weight = 1.0 / n_long
    short_weight = -1.0 / n_short  # Negative for short
    
    # Apply max position weight constraint
    long_weight = min(long_weight, max_position_weight)
    short_weight = max(short_weight, -max_position_weight)  # Negative, so max = less negative
    
    # Scale to maintain dollar-neutrality
    total_long = long_weight * n_long
    total_short = abs(short_weight) * n_short
    
    if total_long > 0 and total_short > 0:
        # Scale both sides to have equal absolute value
        scale = min(1.0, max_position_weight / long_weight, max_position_weight / abs(short_weight))
        long_weight *= scale
        short_weight *= scale
    
    # Build weight series
    weights = pd.Series(dtype=float)
    
    for idx, row in long_names.iterrows():
        identifier = row.get("ticker") or row.get("cusip")
        weights[identifier] = long_weight
    
    for idx, row in short_names.iterrows():
        identifier = row.get("ticker") or row.get("cusip")
        weights[identifier] = short_weight
    
    return weights


def compute_turnover(
    weights_prev: pd.Series,
    weights_curr: pd.Series,
) -> float:
    """
    Compute one-way turnover between two portfolio weight vectors.
    
    Turnover = sum of absolute weight changes / 2
    (Divided by 2 because each dollar traded appears twice: once as a buy, once as a sell)
    
    Args:
        weights_prev: Previous period weights
        weights_curr: Current period weights
        
    Returns:
        One-way turnover (0 to 1+)
    """
    # Align indices (union of both)
    all_names = set(weights_prev.index) | set(weights_curr.index)
    
    weights_prev_aligned = pd.Series(0.0, index=list(all_names))
    weights_prev_aligned.loc[weights_prev.index] = weights_prev
    
    weights_curr_aligned = pd.Series(0.0, index=list(all_names))
    weights_curr_aligned.loc[weights_curr.index] = weights_curr
    
    # Compute absolute changes
    weight_changes = (weights_curr_aligned - weights_prev_aligned).abs()
    
    # One-way turnover = sum of absolute changes / 2
    turnover = weight_changes.sum() / 2.0
    
    return turnover


def run_portfolio_backtest(
    universe: pd.DataFrame,
    signal_col: str = "ai_signal",
    return_col: str = None,
    horizon: int = None,
    quantile_size: float = None,
    max_position_weight: float = None,
    cost_per_side_bps: float = None,
) -> pd.DataFrame:
    """
    Run full portfolio backtest with transaction costs.
    
    Strategy:
    - Rebalance on each as_of_date
    - Execute at next day's open (EXECUTION_DELAY_DAYS = 1)
    - Measure returns over forward horizon
    - Apply transaction costs based on turnover
    
    Args:
        universe: DataFrame with signals and returns
        signal_col: Column name for AI signal
        return_col: Column name for forward return (if None, uses primary horizon)
        horizon: Forward return horizon (if None, uses primary)
        quantile_size: Size of top/bottom quantiles
        max_position_weight: Max weight per name
        cost_per_side_bps: Transaction cost in bps per side
        
    Returns:
        DataFrame with columns:
        - as_of_date: Rebalancing date
        - portfolio_return: Gross portfolio return
        - turnover: One-way turnover
        - transaction_cost: Cost in return terms
        - net_return: Portfolio return after costs
        - cumulative_return: Cumulative net return
    """
    if horizon is None:
        horizon = PRIMARY_HORIZON
    if return_col is None:
        return_col = f"forward_return_{horizon}d"
    if cost_per_side_bps is None:
        cost_per_side_bps = DEFAULT_COST_PER_SIDE_BPS
    
    # Get unique dates (sorted)
    dates = sorted(universe["as_of_date"].unique())
    
    results = []
    prev_weights = pd.Series(dtype=float)
    cumulative_return = 1.0
    
    for i, date in enumerate(dates):
        # Construct portfolio for this date
        weights = construct_portfolio(
            universe=universe,
            as_of_date=date,
            signal_col=signal_col,
            quantile_size=quantile_size,
            max_position_weight=max_position_weight,
        )
        
        if len(weights) == 0:
            continue
        
        # Compute turnover
        if len(prev_weights) > 0:
            turnover = compute_turnover(prev_weights, weights)
        else:
            turnover = 1.0  # First period: full turnover
        
        # Compute portfolio return
        # Get returns for names in portfolio
        date_data = universe[universe["as_of_date"] == date].copy()
        
        portfolio_return = 0.0
        valid_positions = 0
        
        for identifier, weight in weights.items():
            # Find return for this identifier
            if "ticker" in date_data.columns:
                name_data = date_data[date_data["ticker"] == identifier]
            else:
                name_data = date_data[date_data["cusip"] == identifier]
            
            if len(name_data) > 0 and return_col in name_data.columns:
                forward_return = name_data[return_col].iloc[0]
                if pd.notna(forward_return):
                    portfolio_return += weight * forward_return
                    valid_positions += 1
        
        # If no valid positions, skip
        if valid_positions == 0:
            continue
        
        # Transaction cost = turnover × cost_per_side × 2 (buy + sell)
        cost_bps = turnover * cost_per_side_bps * 2
        transaction_cost = cost_bps / 10000.0  # Convert bps to decimal
        
        # Net return = gross return - transaction cost
        net_return = portfolio_return - transaction_cost
        
        # Update cumulative return
        cumulative_return *= (1 + net_return)
        
        results.append({
            "as_of_date": date,
            "portfolio_return": portfolio_return,
            "turnover": turnover,
            "transaction_cost": transaction_cost,
            "net_return": net_return,
            "cumulative_return": cumulative_return,
        })
        
        prev_weights = weights.copy()
    
    return pd.DataFrame(results)


def compute_performance_metrics(
    return_series: pd.Series,
    periods_per_year: int = 252,
) -> Dict[str, float]:
    """
    Compute performance metrics from return series.
    
    Args:
        return_series: Time series of portfolio returns
        periods_per_year: Number of periods per year (252 for daily)
        
    Returns:
        Dictionary with:
        - cagr: Compound Annual Growth Rate
        - volatility: Annualized volatility
        - sharpe: Sharpe ratio (assuming rf = 0)
        - max_drawdown: Maximum drawdown
        - calmar: Calmar ratio (CAGR / |max_drawdown|)
    """
    if len(return_series) == 0:
        # Return dict with None values for missing data (empty input)
        return {
            "cagr": None,
            "volatility": None,
            "sharpe": None,
            "max_drawdown": None,
            "calmar": None,
        }
    
    # Compute cumulative returns
    cumulative = (1 + return_series).cumprod()
    
    # CAGR
    n_periods = len(return_series)
    years = n_periods / periods_per_year
    if years > 0 and cumulative.iloc[-1] > 0:
        cagr = (cumulative.iloc[-1] ** (1 / years)) - 1
    else:
        cagr = np.nan
    
    # Annualized volatility
    volatility = return_series.std() * np.sqrt(periods_per_year)
    
    # Sharpe ratio (assuming risk-free rate = 0)
    if volatility > 0:
        sharpe = (return_series.mean() * periods_per_year) / volatility
    else:
        sharpe = np.nan
    
    # Maximum drawdown
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Calmar ratio
    if abs(max_drawdown) > 0:
        calmar = cagr / abs(max_drawdown)
    else:
        calmar = np.nan
    
    return {
        "cagr": cagr,
        "volatility": volatility,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "calmar": calmar,
    }

