"""
Analysis module for evaluation framework.

Handles:
- Consensus vs contrarian analysis (AI vs human ratings)
- Regime/year breakdowns
- Cross-sectional analysis (by sector, size, etc.)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from .config import RATING_TO_SCORE, HOLDOUT_START_DATE
from .backtest import compute_ic_series, compute_ic_statistics


def human_rating_to_score(rating: str) -> float:
    """
    Convert human IBES rating to numeric score.
    
    Uses same scale as AI ratings: -2 (Sell) to +2 (StrongBuy)
    
    Args:
        rating: Human rating from IBES (etext, itext, etc.)
        
    Returns:
        Numeric score from -2 to +2
    """
    if pd.isna(rating):
        return 0.0
    
    rating_str = str(rating).strip().upper()
    
    # Direct lookup
    for key, value in RATING_TO_SCORE.items():
        if key.upper() == rating_str:
            return value
    
    # Try partial matches
    if "STRONG" in rating_str and "BUY" in rating_str:
        return 2.0
    elif "BUY" in rating_str:
        return 1.0
    elif "HOLD" in rating_str:
        return 0.0
    elif "UNDER" in rating_str or "UNDERPERFORM" in rating_str:
        return -1.0
    elif "SELL" in rating_str:
        return -2.0
    
    return 0.0


def classify_consensus_contrarian(
    ai_score: float,
    human_score: float,
) -> str:
    """
    Classify a (ticker, date) into consensus/contrarian buckets.
    
    Args:
        ai_score: AI base score (-2 to +2)
        human_score: Human base score (-2 to +2)
        
    Returns:
        One of: "Agreement", "AI_More_Bullish", "AI_More_Bearish"
    """
    if pd.isna(ai_score) or pd.isna(human_score):
        return "Unknown"
    
    # Same sign = agreement
    if (ai_score * human_score) >= 0:
        return "Agreement"
    
    # Different signs
    if ai_score > human_score:
        return "AI_More_Bullish"
    else:
        return "AI_More_Bearish"


def analyze_consensus_contrarian(
    universe: pd.DataFrame,
    return_col: str = None,
    horizon: int = 21,
) -> pd.DataFrame:
    """
    Analyze performance by consensus vs contrarian buckets.
    
    For each bucket (Agreement, AI_More_Bullish, AI_More_Bearish):
    - Average forward return
    - Count of examples
    - IC within that bucket
    
    Args:
        universe: DataFrame with AI signals and human ratings
        return_col: Column name for forward return
        horizon: Forward return horizon
        
    Returns:
        DataFrame with columns: bucket, avg_return, count, ic_mean, ic_t_stat
    """
    if return_col is None:
        return_col = f"forward_return_{horizon}d"
    
    # Add human score
    universe = universe.copy()
    universe["human_score"] = universe["human_rating"].apply(human_rating_to_score)
    
    # Add AI base score if not present
    if "ai_base_score" not in universe.columns:
        from .signal import rating_to_base_score
        universe["ai_base_score"] = universe["ai_rating"].apply(
            lambda x: rating_to_base_score(x) if pd.notna(x) else np.nan
        )
    
    # Classify each row
    universe["bucket"] = universe.apply(
        lambda row: classify_consensus_contrarian(
            row.get("ai_base_score", np.nan),
            row.get("human_score", np.nan),
        ),
        axis=1,
    )
    
    # Analyze by bucket - ALWAYS return all three buckets with consistent schema
    results = []
    
    for bucket in ["Agreement", "AI_More_Bullish", "AI_More_Bearish"]:
        bucket_data = universe[universe["bucket"] == bucket].copy()
        
        if len(bucket_data) == 0:
            # Empty bucket - still include with None values
            results.append({
                "bucket": bucket,
                "avg_return": None,
                "count": 0,
                "ic_mean": None,
                "t_stat": None,
                "hit_ratio": None,
            })
            continue
        
        # Average return
        valid_returns = bucket_data[return_col].dropna() if return_col in bucket_data.columns else pd.Series(dtype=float)
        avg_return = valid_returns.mean() if len(valid_returns) > 0 else None
        
        # IC within bucket
        ic_series = compute_ic_series(
            universe=bucket_data,
            signal_col="ai_signal",
            return_col=return_col,
            horizon=horizon,
        )
        
        ic_stats = compute_ic_statistics(ic_series)
        
        results.append({
            "bucket": bucket,
            "avg_return": avg_return,
            "count": len(bucket_data),
            "ic_mean": ic_stats.get("mean_ic"),
            "t_stat": ic_stats.get("t_stat"),  # Use "t_stat" consistently
            "hit_ratio": ic_stats.get("hit_ratio"),
        })
    
    # Always return DataFrame with consistent schema, even if empty
    df = pd.DataFrame(results)
    
    # Ensure all expected columns exist
    expected_columns = ["bucket", "avg_return", "count", "ic_mean", "t_stat", "hit_ratio"]
    for col in expected_columns:
        if col not in df.columns:
            df[col] = None
    
    return df


def analyze_by_year(
    universe: pd.DataFrame,
    signal_col: str = "ai_signal",
    return_col: str = None,
    horizon: int = 21,
) -> pd.DataFrame:
    """
    Analyze IC and performance by calendar year.
    
    Args:
        universe: DataFrame with signals and returns
        signal_col: Column name for AI signal
        return_col: Column name for forward return
        horizon: Forward return horizon
        
    Returns:
        DataFrame with columns: year, mean_ic, t_stat, hit_ratio, n_obs
    """
    if return_col is None:
        return_col = f"forward_return_{horizon}d"
    
    if "year" not in universe.columns:
        universe = universe.copy()
        universe["year"] = universe["as_of_date"].dt.year
    
    results = []
    
    for year in sorted(universe["year"].unique()):
        year_data = universe[universe["year"] == year].copy()
        
        if len(year_data) == 0:
            continue
        
        ic_series = compute_ic_series(
            universe=year_data,
            signal_col=signal_col,
            return_col=return_col,
            horizon=horizon,
        )
        
        ic_stats = compute_ic_statistics(ic_series)
        ic_stats["year"] = year
        
        results.append(ic_stats)
    
    return pd.DataFrame(results)


def analyze_by_regime(
    universe: pd.DataFrame,
    signal_col: str = "ai_signal",
    return_col: str = None,
    horizon: int = 21,
) -> pd.DataFrame:
    """
    Analyze IC and performance by time regime.
    
    Regimes:
    - Pre-2015: Early period
    - 2015-2019: Mid period
    - 2020-2022: COVID period
    - 2023+: Holdout (post-training)
    
    Args:
        universe: DataFrame with signals and returns
        signal_col: Column name for AI signal
        return_col: Column name for forward return
        horizon: Forward return horizon
        
    Returns:
        DataFrame with columns: regime, mean_ic, t_stat, hit_ratio, n_obs
    """
    if return_col is None:
        return_col = f"forward_return_{horizon}d"
    
    universe = universe.copy()
    
    def assign_regime(date):
        if date < datetime(2015, 1, 1):
            return "Pre-2015"
        elif date < datetime(2020, 1, 1):
            return "2015-2019"
        elif date < datetime(2023, 1, 1):
            return "2020-2022"
        else:
            return "2023+ (Holdout)"
    
    universe["regime"] = universe["as_of_date"].apply(assign_regime)
    
    results = []
    
    for regime in ["Pre-2015", "2015-2019", "2020-2022", "2023+ (Holdout)"]:
        regime_data = universe[universe["regime"] == regime].copy()
        
        if len(regime_data) == 0:
            continue
        
        ic_series = compute_ic_series(
            universe=regime_data,
            signal_col=signal_col,
            return_col=return_col,
            horizon=horizon,
        )
        
        ic_stats = compute_ic_statistics(ic_series)
        ic_stats["regime"] = regime
        
        results.append(ic_stats)
    
    return pd.DataFrame(results)


def analyze_by_sector(
    universe: pd.DataFrame,
    signal_col: str = "ai_signal",
    return_col: str = None,
    horizon: int = 21,
) -> pd.DataFrame:
    """
    Analyze IC by sector (if sector data is available).
    
    Args:
        universe: DataFrame with signals and returns
        signal_col: Column name for AI signal
        return_col: Column name for forward return
        horizon: Forward return horizon
        
    Returns:
        DataFrame with columns: sector, mean_ic, t_stat, hit_ratio, n_obs
        (Empty DataFrame if no sector data)
    """
    if return_col is None:
        return_col = f"forward_return_{horizon}d"
    
    if "sector" not in universe.columns:
        return pd.DataFrame()  # No sector data available
    
    universe = universe.copy()
    universe = universe[universe["sector"].notna()].copy()
    
    if len(universe) == 0:
        return pd.DataFrame()
    
    results = []
    
    for sector in sorted(universe["sector"].unique()):
        sector_data = universe[universe["sector"] == sector].copy()
        
        if len(sector_data) == 0:
            continue
        
        ic_series = compute_ic_series(
            universe=sector_data,
            signal_col=signal_col,
            return_col=return_col,
            horizon=horizon,
        )
        
        ic_stats = compute_ic_statistics(ic_series)
        ic_stats["sector"] = sector
        
        results.append(ic_stats)
    
    return pd.DataFrame(results)


def separate_holdout_period(
    universe: pd.DataFrame,
    holdout_start: datetime = None,
) -> Dict[str, pd.DataFrame]:
    """
    Separate universe into backtest and holdout periods.
    
    The holdout period (typically 2023+) represents post-training data
    where the LLM may have been trained on similar data, so results
    should be interpreted with caution.
    
    Args:
        universe: Full evaluation universe
        holdout_start: Start of holdout period (default: config default)
        
    Returns:
        Dictionary with keys: "backtest", "holdout"
    """
    if holdout_start is None:
        holdout_start = HOLDOUT_START_DATE
    
    backtest = universe[universe["as_of_date"] < pd.Timestamp(holdout_start)].copy()
    holdout = universe[universe["as_of_date"] >= pd.Timestamp(holdout_start)].copy()
    
    return {
        "backtest": backtest,
        "holdout": holdout,
    }

