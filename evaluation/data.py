"""
Data module for evaluation framework.

Handles:
- Loading and normalizing datasets
- Building evaluation universe
- Computing forward returns with proper look-ahead protection
- Stratified sampling
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime, timedelta

from .config import (
    DEFAULT_DATA_DIR,
    DEFAULT_HORIZONS,
    DEFAULT_START_DATE,
    DEFAULT_END_DATE,
    DEFAULT_MAX_SAMPLES,
    DEFAULT_STRATIFY_BY,
)


def load_datasets(data_dir: Path = DEFAULT_DATA_DIR) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load IBES, FUND, and NEWS datasets from .feather files.
    
    Normalizes:
    - Dates to timezone-naive datetime
    - CUSIPs to uppercase, stripped
    
    Args:
        data_dir: Path to data directory
        
    Returns:
        Tuple of (ibes_df, fund_df, news_df)
    """
    data_path = Path(data_dir)
    
    print("Loading IBES data...")
    ibes = pd.read_feather(data_path / "ibes_dj30_stock_rec_2008_24.feather")
    
    print("Loading FUND data...")
    fund = pd.read_feather(data_path / "fund_tech_dj30_stocks_2008_24.feather")
    
    print("Loading NEWS data...")
    news = pd.read_feather(data_path / "ciq_dj30_stock_news_2008_24.feather")
    
    # Convert dates to datetime, timezone-naive
    print("Converting date columns...")
    ibes["anndats"] = pd.to_datetime(ibes["anndats"], errors="coerce").dt.tz_localize(None)
    ibes["actdats"] = pd.to_datetime(ibes["actdats"], errors="coerce").dt.tz_localize(None)
    
    fund["date"] = pd.to_datetime(fund["date"], errors="coerce").dt.tz_localize(None)
    
    news["announcedate"] = pd.to_datetime(news["announcedate"], errors="coerce").dt.tz_localize(None)
    
    # Normalize CUSIPs: uppercase, stripped
    ibes["cusip"] = ibes["cusip"].astype(str).str.strip().str.upper()
    fund["cusip"] = fund["cusip"].astype(str).str.strip().str.upper()
    news["cusip"] = news["cusip"].astype(str).str.strip().str.upper()
    
    # Normalize tickers if present
    if "ticker" in ibes.columns:
        ibes["ticker"] = ibes["ticker"].astype(str).str.strip().str.upper()
    if "ticker" in fund.columns:
        fund["ticker"] = fund["ticker"].astype(str).str.strip().str.upper()
    if "ticker" in news.columns:
        news["ticker"] = news["ticker"].astype(str).str.strip().str.upper()
    
    print(f"✓ Loaded {len(ibes)} IBES recommendations")
    print(f"✓ Loaded {len(fund)} FUND rows")
    print(f"✓ Loaded {len(news)} NEWS items")
    
    return ibes, fund, news


def compute_forward_returns(
    fund_df: pd.DataFrame,
    as_of_date: pd.Timestamp,
    horizons: List[int],
    cusip: str,
    use_adjusted_price: bool = True,
) -> pd.Series:
    """
    Compute forward returns for a given (cusip, as_of_date) across multiple horizons.
    
    IMPORTANT: This function uses ONLY data available as of as_of_date.
    Forward returns are computed from the next available trading day after as_of_date
    to the target date (as_of_date + horizon in calendar days).
    
    If the target date is not a trading day, uses the next available trading day.
    If there is no future trading date (delisting/acquisition), returns NaN.
    
    Args:
        fund_df: FUND DataFrame with price data
        as_of_date: Date to compute returns from (decision date)
        horizons: List of forward horizons in calendar days
        cusip: CUSIP identifier
        use_adjusted_price: If True, use price_adjusted; else use price
        
    Returns:
        Series with index = horizons, values = forward returns (or NaN if unavailable)
        
    Note:
        Returns are PRICE RETURNS only (not total returns including dividends).
        This is explicit in the implementation - we use price_adjusted if available,
        which accounts for splits but not dividends.
    """
    # Filter to this company's data
    company_data = fund_df[fund_df["cusip"] == cusip].copy()
    
    if len(company_data) == 0:
        return pd.Series(index=horizons, dtype=float)
    
    # Sort by date
    company_data = company_data.sort_values("date")
    
    # Find the price on or before as_of_date (most recent available)
    historical_data = company_data[company_data["date"] <= as_of_date]
    
    if len(historical_data) == 0:
        return pd.Series(index=horizons, dtype=float)
    
    # Get the price on the decision date (or most recent before it)
    base_row = historical_data.iloc[-1]
    base_date = base_row["date"]
    
    # Use adjusted price if available and requested, else regular price
    price_col = "price_adjusted" if (use_adjusted_price and "price_adjusted" in company_data.columns) else "price"
    
    if price_col not in base_row.index or pd.isna(base_row[price_col]) or base_row[price_col] <= 0:
        return pd.Series(index=horizons, dtype=float)
    
    base_price = base_row[price_col]
    
    # Compute returns for each horizon
    returns = {}
    
    for horizon in horizons:
        # Target date = as_of_date + horizon (calendar days)
        target_date = as_of_date + timedelta(days=horizon)
        
        # Find the next available trading day >= target_date for this company
        future_data = company_data[company_data["date"] > base_date]
        
        if len(future_data) == 0:
            returns[horizon] = np.nan
            continue
        
        # Find the first trading day >= target_date
        target_data = future_data[future_data["date"] >= target_date]
        
        if len(target_data) == 0:
            # No trading day >= target_date (delisting/acquisition)
            returns[horizon] = np.nan
            continue
        
        target_row = target_data.iloc[0]
        target_price = target_row[price_col]
        
        if pd.isna(target_price) or target_price <= 0:
            returns[horizon] = np.nan
            continue
        
        # Compute return: (target_price - base_price) / base_price
        forward_return = (target_price - base_price) / base_price
        returns[horizon] = forward_return
    
    return pd.Series(returns)


def build_evaluation_universe(
    ibes_df: pd.DataFrame,
    fund_df: pd.DataFrame,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    horizons: List[int] = None,
    primary_horizon: int = 21,
    use_adjusted_price: bool = True,
) -> pd.DataFrame:
    """
    Build the evaluation universe: one row per (ticker, as_of_date).
    
    Requirements:
    - Must have IBES human rating on that date
    - Must have price data on that date
    - Must have forward returns for at least the primary horizon
    
    Args:
        ibes_df: IBES DataFrame with analyst recommendations
        fund_df: FUND DataFrame with price data
        start_date: Start of evaluation period (default: config default)
        end_date: End of evaluation period (default: config default)
        horizons: List of forward return horizons (default: config default)
        primary_horizon: Primary horizon for filtering (must have this return)
        use_adjusted_price: Whether to use adjusted prices for returns
        
    Returns:
        DataFrame with columns:
        - ticker (or cusip if ticker not available)
        - cusip
        - as_of_date (from IBES anndats)
        - human_rating (from IBES etext or itext)
        - forward_return_5d, forward_return_10d, etc. (one per horizon)
        - Any metadata from IBES (sector, market_cap, etc. if available)
    """
    if start_date is None:
        start_date = DEFAULT_START_DATE
    if end_date is None:
        end_date = DEFAULT_END_DATE
    if horizons is None:
        horizons = DEFAULT_HORIZONS
    
    print(f"\nBuilding evaluation universe...")
    print(f"  Date range: {start_date.date()} to {end_date.date()}")
    print(f"  Horizons: {horizons} days")
    
    # Filter IBES to date range
    ibes_filtered = ibes_df[
        (ibes_df["anndats"] >= pd.Timestamp(start_date)) &
        (ibes_df["anndats"] <= pd.Timestamp(end_date)) &
        (pd.notna(ibes_df["anndats"]))
    ].copy()
    
    print(f"  Found {len(ibes_filtered)} IBES recommendations in date range")
    
    # Extract key fields
    universe_rows = []
    
    for idx, rec in ibes_filtered.iterrows():
        cusip = rec.get("cusip")
        as_of_date = rec.get("anndats")
        human_rating = rec.get("etext") or rec.get("itext") or rec.get("ereccd") or rec.get("ireccd")
        ticker = rec.get("ticker", cusip)  # Fallback to CUSIP if no ticker
        
        if pd.isna(cusip) or pd.isna(as_of_date):
            continue
        
        # Check if we have price data on or before this date
        company_fund = fund_df[
            (fund_df["cusip"] == cusip) &
            (fund_df["date"] <= as_of_date)
        ]
        
        if len(company_fund) == 0:
            continue
        
        # Compute forward returns
        forward_returns = compute_forward_returns(
            fund_df=fund_df,
            as_of_date=as_of_date,
            horizons=horizons,
            cusip=cusip,
            use_adjusted_price=use_adjusted_price,
        )
        
        # Must have primary horizon return (not NaN)
        if pd.isna(forward_returns.get(primary_horizon, np.nan)):
            continue
        
        # Build row
        row = {
            "ticker": ticker,
            "cusip": cusip,
            "as_of_date": as_of_date,
            "human_rating": human_rating,
        }
        
        # Add forward returns
        for horizon in horizons:
            row[f"forward_return_{horizon}d"] = forward_returns.get(horizon, np.nan)
        
        # Add any metadata from IBES
        for col in ["cname", "analyst", "sector", "market_cap"]:
            if col in rec.index:
                row[col] = rec[col]
        
        universe_rows.append(row)
    
    universe = pd.DataFrame(universe_rows)
    
    if len(universe) == 0:
        print("  ⚠ No valid evaluation points found")
        return universe
    
    # Add year column for stratification
    universe["year"] = universe["as_of_date"].dt.year
    
    print(f"  ✓ Built universe with {len(universe)} evaluation points")
    print(f"    Unique tickers: {universe['ticker'].nunique()}")
    print(f"    Date range: {universe['as_of_date'].min().date()} to {universe['as_of_date'].max().date()}")
    
    return universe


def stratified_sample(
    universe: pd.DataFrame,
    max_samples: int,
    stratify_by: List[str] = None,
) -> pd.DataFrame:
    """
    Downsample universe using stratified sampling.
    
    Ensures balanced representation across specified dimensions
    (e.g., years and tickers) to avoid evaluating only recent or popular names.
    
    Args:
        universe: Evaluation universe DataFrame
        max_samples: Maximum number of samples (if None, return all)
        stratify_by: List of column names to stratify by (default: ["year", "ticker"])
        
    Returns:
        Sampled DataFrame
    """
    if max_samples is None or len(universe) <= max_samples:
        return universe
    
    if stratify_by is None:
        stratify_by = DEFAULT_STRATIFY_BY
    
    # Filter to columns that exist
    stratify_by = [col for col in stratify_by if col in universe.columns]
    
    if not stratify_by:
        # No valid stratification columns, just random sample
        return universe.sample(n=max_samples, random_state=42)
    
    print(f"\nStratified sampling to {max_samples} rows...")
    print(f"  Stratifying by: {stratify_by}")
    
    # Group by stratification columns and sample proportionally
    sampled_rows = []
    
    for group_key, group_df in universe.groupby(stratify_by):
        # Sample proportionally from each group
        group_size = len(group_df)
        target_size = max(1, int(max_samples * group_size / len(universe)))
        target_size = min(target_size, group_size)  # Don't oversample
        
        sampled_group = group_df.sample(n=target_size, random_state=42)
        sampled_rows.append(sampled_group)
    
    sampled = pd.concat(sampled_rows, ignore_index=True)
    
    # If we're still over, randomly sample down
    if len(sampled) > max_samples:
        sampled = sampled.sample(n=max_samples, random_state=42)
    
    print(f"  ✓ Sampled to {len(sampled)} rows")
    
    return sampled.reset_index(drop=True)

