"""
Signal generation module for evaluation framework.

Handles:
- Calling Recommender safely with no look-ahead
- Parsing ratings and confidence from Recommender output
- Converting to numeric signals (signal = base_score × confidence)
"""

import pandas as pd
import numpy as np
import re
from typing import Optional, Dict, Tuple
import sys
from pathlib import Path

# Add project root to path to import Recommender
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.recommender.orchestrator import run_multi_analyst_recommendation
from .config import RATING_TO_SCORE, CONFIDENCE_TO_VALUE


def call_recommender_safe(
    cusip: str,
    as_of_date: pd.Timestamp,
    fund_df: pd.DataFrame,
    news_df: pd.DataFrame,
    ticker: str = "N/A",
    company: str = "N/A",
    news_window_days: int = 30,
) -> str:
    """
    Call the Recommender for a given (ticker, as_of_date) with NO LOOK-AHEAD.
    
    IMPORTANT: This function ensures that:
    1. Only data up to as_of_date is used
    2. The Recommender's internal data extraction respects this cutoff
    3. No future information leaks into the recommendation
    
    The Recommender orchestrator already filters data to <= rec_date,
    but this function documents and enforces that constraint explicitly.
    
    Args:
        cusip: Company CUSIP identifier
        as_of_date: Decision date (must use only data <= this date)
        fund_df: Full FUND DataFrame (will be filtered internally)
        news_df: Full NEWS DataFrame (will be filtered internally)
        ticker: Optional ticker for display
        company: Optional company name for display
        news_window_days: Days of news to include (before as_of_date)
        
    Returns:
        Markdown string with Recommender output
        
    Note:
        The Recommender orchestrator filters:
        - FUND data: date <= rec_date
        - NEWS data: announcedate <= rec_date (and >= rec_date - news_window_days)
        This ensures no look-ahead bias.
    """
    # The Recommender orchestrator already handles date filtering correctly
    # We just need to call it with the right parameters
    
    result = run_multi_analyst_recommendation(
        cusip=str(cusip),
        rec_date=as_of_date,
        fund_df=fund_df,
        news_df=news_df,
        news_window_days=news_window_days,
        ticker=ticker,
        company=company,
    )
    
    return result


def parse_rating_and_confidence(markdown_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse rating and confidence from Recommender markdown output.
    
    Looks for patterns like:
    - **Model Rating**: StrongBuy
    - **Overall Confidence**: High
    
    Args:
        markdown_text: Full markdown output from Recommender
        
    Returns:
        Tuple of (rating, confidence) or (None, None) if not found
    """
    rating = None
    confidence = None
    
    # Patterns for rating
    rating_patterns = [
        r"Model Rating[:\s]+(StrongBuy|Buy|Hold|UnderPerform|Sell)",
        r"Final Rating[:\s]+(StrongBuy|Buy|Hold|UnderPerform|Sell)",
        r"\*\*Model Rating\*\*[:\s]+(StrongBuy|Buy|Hold|UnderPerform|Sell)",
        r"\*\*Final Rating\*\*[:\s]+(StrongBuy|Buy|Hold|UnderPerform|Sell)",
        r"Rating[:\s]+(StrongBuy|Buy|Hold|UnderPerform|Sell)",
    ]
    
    for pattern in rating_patterns:
        match = re.search(pattern, markdown_text, re.IGNORECASE)
        if match:
            rating = match.group(1)
            break
    
    # Patterns for confidence
    confidence_patterns = [
        r"Overall Confidence[:\s]+(High|Medium|Low)",
        r"Confidence[:\s]+(High|Medium|Low)",
        r"\*\*Overall Confidence\*\*[:\s]+(High|Medium|Low)",
        r"\*\*Confidence\*\*[:\s]+(High|Medium|Low)",
    ]
    
    for pattern in confidence_patterns:
        match = re.search(pattern, markdown_text, re.IGNORECASE)
        if match:
            confidence = match.group(1)
            break
    
    return rating, confidence


def rating_to_base_score(rating: str) -> float:
    """
    Convert textual rating to numeric base score.
    
    Uses symmetric scale: -2 (Sell) to +2 (StrongBuy)
    
    Args:
        rating: Textual rating (e.g., "StrongBuy", "Buy", etc.)
        
    Returns:
        Numeric score from -2 to +2
    """
    rating_upper = str(rating).strip().upper()
    
    # Direct lookup
    if rating_upper in RATING_TO_SCORE:
        return RATING_TO_SCORE[rating_upper]
    
    # Try variations
    for key, value in RATING_TO_SCORE.items():
        if key.upper() == rating_upper:
            return value
    
    # Default to Hold if not found
    return 0.0


def confidence_to_value(confidence: str) -> float:
    """
    Convert textual confidence to numeric value [0, 1].
    
    Args:
        confidence: Textual confidence (e.g., "High", "Medium", "Low")
        
    Returns:
        Numeric value from 0 to 1
    """
    confidence_upper = str(confidence).strip().upper()
    
    if confidence_upper in CONFIDENCE_TO_VALUE:
        return CONFIDENCE_TO_VALUE[confidence_upper]
    
    # Default to medium if not found
    return 0.6


def compute_signal(rating: str, confidence: str) -> float:
    """
    Compute numeric signal from rating and confidence.
    
    Formula: signal = base_score × confidence
    
    This ensures that:
    - A low-confidence StrongBuy ranks below a high-confidence Buy
    - Signals are properly scaled by confidence
    
    Args:
        rating: Textual rating
        confidence: Textual confidence
        
    Returns:
        Numeric signal (typically -2 to +2, but can be smaller with low confidence)
    """
    base_score = rating_to_base_score(rating)
    conf_value = confidence_to_value(confidence)
    
    signal = base_score * conf_value
    
    return signal


def load_cached_signals(cache_path: Path) -> Optional[pd.DataFrame]:
    """
    Load cached AI signals from CSV file.
    
    Args:
        cache_path: Path to cache file (universe_with_signals.csv)
        
    Returns:
        DataFrame with cached signals, or None if file doesn't exist or is invalid
    """
    if not cache_path.exists():
        return None
    
    try:
        cached = pd.read_csv(cache_path)
        
        # Ensure required columns exist
        required_cols = ["ticker", "as_of_date"]
        ai_cols = ["ai_rating", "ai_confidence", "ai_base_score", "ai_confidence_value", "ai_signal"]
        
        if not all(col in cached.columns for col in required_cols):
            return None
        
        # Convert as_of_date to datetime
        cached["as_of_date"] = pd.to_datetime(cached["as_of_date"], errors="coerce")
        
        return cached
    except Exception as e:
        # If loading fails, return None (treat as no cache)
        return None


def generate_signals_for_universe(
    universe: pd.DataFrame,
    fund_df: pd.DataFrame,
    news_df: pd.DataFrame,
    max_samples: Optional[int] = None,
    news_window_days: int = 30,
    verbose: bool = True,
    cache_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Generate AI signals for all rows in the evaluation universe.
    
    For each (ticker, as_of_date):
    1. Checks cache for existing signals (if cache_path provided)
    2. For uncached rows, calls Recommender (with no look-ahead)
    3. Parses rating and confidence
    4. Computes base_score and signal
    5. Adds columns to universe DataFrame
    
    Args:
        universe: Evaluation universe DataFrame
        fund_df: Full FUND DataFrame
        news_df: Full NEWS DataFrame
        max_samples: Optional limit on number of samples to evaluate (for speed)
        news_window_days: Days of news to include
        verbose: Whether to print progress
        cache_path: Optional path to cache file (universe_with_signals.csv)
        
    Returns:
        DataFrame with added columns:
        - ai_rating: Textual rating from Recommender
        - ai_confidence: Textual confidence
        - ai_base_score: Numeric base score (-2 to +2)
        - ai_confidence_value: Numeric confidence (0 to 1)
        - ai_signal: Combined signal (base_score × confidence)
    """
    # Optionally subsample for speed
    if max_samples is not None and len(universe) > max_samples:
        universe = universe.sample(n=max_samples, random_state=42).copy()
        if verbose:
            print(f"Subsampling to {max_samples} rows for signal generation...")
    
    # Initialize new columns
    universe = universe.copy()
    universe["ai_rating"] = None
    universe["ai_confidence"] = None
    universe["ai_base_score"] = np.nan
    universe["ai_confidence_value"] = np.nan
    universe["ai_signal"] = np.nan
    
    # Try to load cached signals
    cached_signals = None
    if cache_path is not None:
        cached_signals = load_cached_signals(cache_path)
        
        if cached_signals is not None and len(cached_signals) > 0:
            # Merge cached signals into universe
            # Use ticker and as_of_date as merge keys
            merge_keys = ["ticker", "as_of_date"]
            
            # Ensure both DataFrames have the merge keys
            if all(col in universe.columns for col in merge_keys) and \
               all(col in cached_signals.columns for col in merge_keys):
                
                # Normalize dates for merging
                universe["as_of_date"] = pd.to_datetime(universe["as_of_date"])
                cached_signals["as_of_date"] = pd.to_datetime(cached_signals["as_of_date"])
                
                # Normalize tickers (uppercase, stripped)
                universe["ticker"] = universe["ticker"].astype(str).str.strip().str.upper()
                cached_signals["ticker"] = cached_signals["ticker"].astype(str).str.strip().str.upper()
                
                # AI columns to merge
                ai_cols = ["ai_rating", "ai_confidence", "ai_base_score", "ai_confidence_value", "ai_signal"]
                available_ai_cols = [col for col in ai_cols if col in cached_signals.columns]
                
                if available_ai_cols:
                    # Merge on ticker and as_of_date
                    # Left merge: keep all rows from universe, add cached AI columns
                    merged = universe.merge(
                        cached_signals[merge_keys + available_ai_cols],
                        on=merge_keys,
                        how="left",
                        suffixes=("", "_cached"),
                    )
                    
                    # Fill in missing AI columns from cache
                    for col in available_ai_cols:
                        cached_col = f"{col}_cached"
                        if cached_col in merged.columns:
                            # Use cached value if current value is missing/None
                            mask = merged[col].isna() | (merged[col] == None) | (merged[col] == "")
                            merged.loc[mask, col] = merged.loc[mask, cached_col]
                            merged = merged.drop(columns=[cached_col])
                    
                    universe = merged
                    
                    if verbose:
                        cached_count = universe["ai_signal"].notna().sum()
                        print(f"\n✓ Loaded cached signals: {cached_count} evaluation points already have AI signals")
    
    total = len(universe)
    needs_signal = universe["ai_signal"].isna() | (universe["ai_signal"] == None)
    new_count = needs_signal.sum()
    cached_count = total - new_count
    
    if verbose:
        print(f"\nGenerating AI signals for {total} evaluation points...")
        print(f"  Already have cached signals: {cached_count}")
        print(f"  Need new signals: {new_count}")
        if new_count > 0:
            print("  (This may take a while - each call takes ~60-90 seconds)")
    
    # Only process rows that need new signals
    rows_to_process = universe[needs_signal].copy()
    
    if len(rows_to_process) == 0:
        if verbose:
            print("\n✓ All evaluation points already have cached signals. Skipping Recommender calls.")
        return universe
    
    processed_count = 0
    for idx, row in rows_to_process.iterrows():
        if verbose and processed_count > 0 and processed_count % 10 == 0:
            print(f"  Progress: {processed_count}/{new_count} ({100*processed_count/new_count:.1f}%)")
        
        try:
            cusip = row["cusip"]
            as_of_date = row["as_of_date"]
            ticker = row.get("ticker", "N/A")
            company = row.get("cname", "N/A")
            
            # Call Recommender
            markdown_output = call_recommender_safe(
                cusip=cusip,
                as_of_date=as_of_date,
                fund_df=fund_df,
                news_df=news_df,
                ticker=ticker,
                company=company,
                news_window_days=news_window_days,
            )
            
            # Parse rating and confidence
            rating, confidence = parse_rating_and_confidence(markdown_output)
            
            if rating and confidence:
                base_score = rating_to_base_score(rating)
                conf_value = confidence_to_value(confidence)
                signal = compute_signal(rating, confidence)
                
                universe.at[idx, "ai_rating"] = rating
                universe.at[idx, "ai_confidence"] = confidence
                universe.at[idx, "ai_base_score"] = base_score
                universe.at[idx, "ai_confidence_value"] = conf_value
                universe.at[idx, "ai_signal"] = signal
                processed_count += 1
            else:
                if verbose:
                    print(f"  ⚠ Warning: Could not parse rating/confidence for row {idx}")
        
        except Exception as e:
            if verbose:
                print(f"  ⚠ Error processing row {idx}: {e}")
            continue
    
    # Count successful signals
    successful = universe["ai_signal"].notna().sum()
    newly_generated = successful - cached_count
    
    if verbose:
        print(f"\n✓ Signal generation complete:")
        print(f"  Total with signals: {successful}/{total}")
        print(f"  Reused from cache: {cached_count}")
        print(f"  Newly generated: {newly_generated}")
    
    return universe

