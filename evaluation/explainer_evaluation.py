"""
Explainer evaluation module.

Evaluates the quality of Explainer team explanations using three metrics:
1. Faithfulness to data (no hallucinations)
2. Rating-explanation consistency (tone vs rating)
3. Coverage/completeness (mentions available data sources)
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, Optional, List, Tuple
from datetime import datetime, date
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.explainer.orchestrator import run_multi_analyst_explainer
from .config import DEFAULT_OUTPUT_DIR


def run_explainer(
    ticker: str,
    as_of_date: date,
    human_rating: str,
    ibes_df: pd.DataFrame,
    fund_df: pd.DataFrame,
    news_df: pd.DataFrame,
    fund_window_days: int = 90,
    news_window_days: int = 30,
) -> Dict[str, str]:
    """
    Call the Explainer team for a given (ticker, date, human_rating).
    
    MUST only use data up to as_of_date (no look-ahead).
    The Explainer orchestrator already enforces this by filtering data.
    
    Args:
        ticker: Stock ticker
        as_of_date: Recommendation date
        human_rating: Human analyst rating (for context)
        ibes_df: IBES DataFrame
        fund_df: FUND DataFrame (will be filtered to <= as_of_date)
        news_df: NEWS DataFrame (will be filtered to <= as_of_date)
        fund_window_days: Days of fundamental data to include
        news_window_days: Days of news to include
        
    Returns:
        Dict with at least:
        - "explanation": str (full markdown explanation)
        - "manager_report": str (manager synthesis only, if parseable)
    """
    # Find matching IBES recommendation
    as_of_date_ts = pd.Timestamp(as_of_date)
    
    # Normalize ticker for matching
    ticker_upper = str(ticker).strip().upper()
    
    # Find IBES row matching ticker and date
    matching_rows = ibes_df[
        (ibes_df["ticker"].astype(str).str.strip().str.upper() == ticker_upper) &
        (pd.to_datetime(ibes_df["anndats"]) == as_of_date_ts)
    ]
    
    if len(matching_rows) == 0:
        # Try to find by date only (if ticker doesn't match exactly)
        matching_rows = ibes_df[pd.to_datetime(ibes_df["anndats"]) == as_of_date_ts]
    
    if len(matching_rows) == 0:
        return {
            "explanation": f"ERROR: No IBES recommendation found for {ticker} on {as_of_date}",
            "manager_report": "",
        }
    
    # Use first matching row
    rec_index = matching_rows.index[0]
    
    # The Explainer orchestrator already filters data to <= as_of_date
    # We just need to call it
    explanation_md = run_multi_analyst_explainer(
        ibes_df=ibes_df,
        fund_df=fund_df,
        news_df=news_df,
        rec_index=rec_index,
        fund_window_days=fund_window_days,
        news_window_days=news_window_days,
    )
    
    # Try to extract manager report (first section before "Individual Analyst Reports")
    manager_report = explanation_md
    if "# 📊 Individual Analyst Reports" in explanation_md:
        manager_report = explanation_md.split("# 📊 Individual Analyst Reports")[0].strip()
    
    return {
        "explanation": explanation_md,
        "manager_report": manager_report,
    }


def get_ground_truth(
    row: pd.Series,
    fund_df: pd.DataFrame,
    news_df: pd.DataFrame,
) -> Dict:
    """
    Extract ground truth data for a given evaluation point.
    
    Args:
        row: Row from evaluation universe DataFrame
        fund_df: FUND DataFrame
        news_df: NEWS DataFrame
        
    Returns:
        Dict with:
        - fwd_ret_21d: Forward return (if available)
        - fwd_ret_63d: Forward return (if available)
        - fundamentals_available: bool
        - technicals_available: bool
        - news_available: bool
        - price_trend: "up" / "down" / "neutral" / None (based on forward return)
    """
    ground_truth = {
        "fwd_ret_21d": None,
        "fwd_ret_63d": None,
        "fundamentals_available": False,
        "technicals_available": False,
        "news_available": False,
        "price_trend": None,
    }
    
    # Forward returns
    if "forward_return_21d" in row.index:
        ground_truth["fwd_ret_21d"] = row.get("forward_return_21d")
    
    if "forward_return_63d" in row.index:
        ground_truth["fwd_ret_63d"] = row.get("forward_return_63d")
    
    # Determine price trend from forward return
    if ground_truth["fwd_ret_21d"] is not None and not pd.isna(ground_truth["fwd_ret_21d"]):
        ret = ground_truth["fwd_ret_21d"]
        if ret > 0.02:  # > 2% = uptrend
            ground_truth["price_trend"] = "up"
        elif ret < -0.02:  # < -2% = downtrend
            ground_truth["price_trend"] = "down"
        else:
            ground_truth["price_trend"] = "neutral"
    
    # Check data availability
    cusip = row.get("cusip")
    as_of_date = pd.to_datetime(row.get("as_of_date"))
    
    if cusip and not pd.isna(as_of_date):
        # Check fundamentals/technicals (from FUND)
        fund_data = fund_df[
            (fund_df["cusip"] == cusip) &
            (fund_df["date"] <= as_of_date)
        ]
        
        if len(fund_data) > 0:
            ground_truth["fundamentals_available"] = True
            ground_truth["technicals_available"] = True
        
        # Check news
        news_data = news_df[
            (news_df["cusip"] == cusip) &
            (pd.to_datetime(news_df["announcedate"]) <= as_of_date)
        ]
        
        if len(news_data) > 0:
            ground_truth["news_available"] = True
    
    return ground_truth


def compute_faithfulness(
    explanation: str,
    ground_truth: Dict,
) -> Dict:
    """
    Compute faithfulness metrics: check if explanation matches actual data.
    
    Args:
        explanation: Full explanation text
        ground_truth: Ground truth dict from get_ground_truth()
        
    Returns:
        Dict with:
        - faithfulness_score: float (0-1)
        - price_trend_consistent: bool/None
        - news_sentiment_consistent: bool/None
        - fundamentals_consistent: bool/None
    """
    explanation_lower = explanation.lower()
    
    flags = {
        "price_trend_consistent": None,
        "news_sentiment_consistent": None,
        "fundamentals_consistent": None,
    }
    
    # Check price trend consistency
    price_trend = ground_truth.get("price_trend")
    fwd_ret = ground_truth.get("fwd_ret_21d")
    
    if price_trend is not None and fwd_ret is not None:
        # Look for uptrend mentions
        uptrend_words = ["uptrend", "rising", "strong price", "momentum", "gaining", "rally", "surge"]
        downtrend_words = ["downtrend", "falling", "weak price", "declining", "pressure", "selloff", "drop"]
        
        mentions_uptrend = any(word in explanation_lower for word in uptrend_words)
        mentions_downtrend = any(word in explanation_lower for word in downtrend_words)
        
        if mentions_uptrend or mentions_downtrend:
            if mentions_uptrend:
                flags["price_trend_consistent"] = (price_trend == "up" or fwd_ret > 0)
            elif mentions_downtrend:
                flags["price_trend_consistent"] = (price_trend == "down" or fwd_ret < 0)
    
    # Check news sentiment consistency (simple heuristic)
    if ground_truth.get("news_available"):
        negative_news_words = ["negative news", "headwinds", "bad news", "concerns", "worries", "risks"]
        positive_news_words = ["positive news", "tailwinds", "good news", "opportunities", "catalyst"]
        
        mentions_negative = any(word in explanation_lower for word in negative_news_words)
        mentions_positive = any(word in explanation_lower for word in positive_news_words)
        
        if mentions_negative or mentions_positive:
            # Simple check: if forward return is negative, negative news is consistent
            # This is a heuristic - not perfect but catches obvious contradictions
            if mentions_negative and fwd_ret is not None:
                flags["news_sentiment_consistent"] = (fwd_ret < 0.05)  # Allow some tolerance
            elif mentions_positive and fwd_ret is not None:
                flags["news_sentiment_consistent"] = (fwd_ret > -0.05)
    
    # Check fundamentals consistency (simple heuristic)
    if ground_truth.get("fundamentals_available"):
        strong_fundamentals_words = ["strong fundamentals", "solid earnings", "growth", "improving", "robust"]
        weak_fundamentals_words = ["weak fundamentals", "declining", "deteriorating", "concerns"]
        
        mentions_strong = any(word in explanation_lower for word in strong_fundamentals_words)
        mentions_weak = any(word in explanation_lower for word in weak_fundamentals_words)
        
        if mentions_strong or mentions_weak:
            # Simple check: if forward return is positive, strong fundamentals is consistent
            if mentions_strong and fwd_ret is not None:
                flags["fundamentals_consistent"] = (fwd_ret > -0.05)
            elif mentions_weak and fwd_ret is not None:
                flags["fundamentals_consistent"] = (fwd_ret < 0.05)
    
    # Compute faithfulness score
    non_none_flags = [v for v in flags.values() if v is not None]
    if len(non_none_flags) > 0:
        faithfulness_score = sum(non_none_flags) / len(non_none_flags)
    else:
        faithfulness_score = 1.0  # If no checks possible, assume faithful
    
    return {
        "faithfulness_score": faithfulness_score,
        **flags,
    }


def compute_sentiment_alignment(
    explanation: str,
    human_rating: str,
) -> Dict:
    """
    Compute sentiment alignment: does explanation tone match the rating?
    
    Args:
        explanation: Full explanation text
        human_rating: Human rating (Buy, Sell, Hold, etc.)
        
    Returns:
        Dict with:
        - sentiment_score: float (-1 to 1)
        - sentiment_aligned_with_rating: bool
    """
    explanation_lower = explanation.lower()
    
    # Simple word lists
    positive_words = [
        "strong", "solid", "improving", "positive", "upside", "opportunity", 
        "growth", "robust", "favorable", "bullish", "gaining", "momentum"
    ]
    negative_words = [
        "weak", "declining", "negative", "risk", "downside", "pressure", 
        "headwinds", "concerns", "deteriorating", "bearish", "falling", "weakness"
    ]
    
    # Count occurrences
    pos_count = sum(1 for word in positive_words if word in explanation_lower)
    neg_count = sum(1 for word in negative_words if word in explanation_lower)
    
    total_count = pos_count + neg_count
    if total_count > 0:
        sentiment_score = (pos_count - neg_count) / total_count
    else:
        sentiment_score = 0.0
    
    # Determine expected sentiment from rating
    rating_upper = str(human_rating).strip().upper()
    
    if "BUY" in rating_upper or "STRONG" in rating_upper:
        expected_positive = True
    elif "SELL" in rating_upper or "UNDER" in rating_upper:
        expected_positive = False
    else:  # Hold or neutral
        expected_positive = None
    
    # Check alignment
    if expected_positive is True:
        sentiment_aligned = sentiment_score > 0
    elif expected_positive is False:
        sentiment_aligned = sentiment_score < 0
    else:  # Hold - should be near neutral
        sentiment_aligned = abs(sentiment_score) < 0.3
    
    return {
        "sentiment_score": sentiment_score,
        "sentiment_aligned_with_rating": sentiment_aligned,
    }


def compute_coverage(
    explanation: str,
    ground_truth: Dict,
) -> Dict:
    """
    Compute coverage: does explanation mention available data sources?
    
    Args:
        explanation: Full explanation text
        ground_truth: Ground truth dict from get_ground_truth()
        
    Returns:
        Dict with:
        - coverage_score: float (0-1)
        - available_sources: List[str]
        - mentioned_sources: List[str]
    """
    explanation_lower = explanation.lower()
    
    # Determine available sources
    available_sources = []
    if ground_truth.get("fundamentals_available"):
        available_sources.append("fundamentals")
    if ground_truth.get("technicals_available"):
        available_sources.append("technicals")
    if ground_truth.get("news_available"):
        available_sources.append("news")
    
    # Keywords for each source
    fundamental_keywords = [
        "earnings", "revenue", "margin", "pe", "valuation", "profit", 
        "eps", "roe", "roa", "leverage", "cash flow", "fundamental"
    ]
    technical_keywords = [
        "price", "trend", "momentum", "volatility", "moving average", 
        "rsi", "macd", "technical", "chart", "indicator"
    ]
    news_keywords = [
        "news", "headline", "article", "announcement", "sentiment", 
        "catalyst", "event", "press release"
    ]
    
    # Check which sources are mentioned
    mentioned_sources = []
    
    if "fundamentals" in available_sources:
        if any(keyword in explanation_lower for keyword in fundamental_keywords):
            mentioned_sources.append("fundamentals")
    
    if "technicals" in available_sources:
        if any(keyword in explanation_lower for keyword in technical_keywords):
            mentioned_sources.append("technicals")
    
    if "news" in available_sources:
        if any(keyword in explanation_lower for keyword in news_keywords):
            mentioned_sources.append("news")
    
    # Compute coverage score
    if len(available_sources) > 0:
        coverage_score = len(mentioned_sources) / len(available_sources)
    else:
        coverage_score = 1.0  # If no sources available, perfect coverage
    
    return {
        "coverage_score": coverage_score,
        "available_sources": available_sources,
        "mentioned_sources": mentioned_sources,
    }


def evaluate_explainer(
    universe_df: pd.DataFrame,
    ibes_df: pd.DataFrame,
    fund_df: pd.DataFrame,
    news_df: pd.DataFrame,
    sample_size: int = 5,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Evaluate Explainer team on a sample of evaluation points.
    
    Args:
        universe_df: Evaluation universe DataFrame (must have ticker, as_of_date, human_rating)
        ibes_df: IBES DataFrame
        fund_df: FUND DataFrame
        news_df: NEWS DataFrame
        sample_size: Number of points to evaluate
        verbose: Whether to print progress
        
    Returns:
        DataFrame with one row per explanation, columns:
        - ticker, as_of_date, human_rating, explanation
        - faithfulness_score, price_trend_consistent, news_sentiment_consistent, fundamentals_consistent
        - sentiment_score, sentiment_aligned_with_rating
        - coverage_score, available_sources, mentioned_sources
    """
    # Filter to rows with required columns
    required_cols = ["ticker", "as_of_date", "human_rating"]
    if not all(col in universe_df.columns for col in required_cols):
        raise ValueError(f"Universe DataFrame must have columns: {required_cols}")
    
    valid_universe = universe_df[universe_df[required_cols].notna().all(axis=1)].copy()
    
    if len(valid_universe) == 0:
        raise ValueError("No valid evaluation points found in universe")
    
    # Stratified sampling by rating
    if "human_rating" in valid_universe.columns:
        # Try to get at least 1-2 examples of each major rating
        ratings = valid_universe["human_rating"].value_counts()
        major_ratings = ["Buy", "Sell", "Hold", "StrongBuy", "UnderPerform"]
        
        sampled_rows = []
        target_per_rating = max(1, sample_size // len(major_ratings))
        
        for rating in major_ratings:
            rating_data = valid_universe[
                valid_universe["human_rating"].astype(str).str.upper().str.contains(rating.upper(), na=False)
            ]
            if len(rating_data) > 0:
                n_sample = min(target_per_rating, len(rating_data))
                sampled_rows.append(rating_data.sample(n=n_sample, random_state=42))
        
        if len(sampled_rows) > 0:
            sampled = pd.concat(sampled_rows, ignore_index=True)
            # If we need more, randomly sample from remaining
            if len(sampled) < sample_size:
                # Get original indices from sampled rows
                sampled_original_indices = set()
                for df in sampled_rows:
                    sampled_original_indices.update(df.index)
                
                remaining = valid_universe[~valid_universe.index.isin(sampled_original_indices)]
                if len(remaining) > 0:
                    n_more = min(sample_size - len(sampled), len(remaining))
                    sampled = pd.concat([sampled, remaining.sample(n=n_more, random_state=42)], ignore_index=True)
        else:
            # Fallback to random sampling
            if verbose:
                print("  ⚠ Warning: Could not stratify by rating, using random sampling")
            sampled = valid_universe.sample(n=min(sample_size, len(valid_universe)), random_state=42)
    else:
        # Random sampling
        sampled = valid_universe.sample(n=min(sample_size, len(valid_universe)), random_state=42)
    
    if verbose:
        print(f"\nEvaluating Explainer on {len(sampled)} cases...")
        print("  (Each explanation takes ~60-90 seconds)")
    
    results = []
    
    for idx, row in sampled.iterrows():
        if verbose:
            print(f"\n  Processing {idx + 1}/{len(sampled)}: {row['ticker']} on {row['as_of_date']}")
        
        try:
            ticker = row["ticker"]
            as_of_date = pd.to_datetime(row["as_of_date"]).date()
            human_rating = str(row["human_rating"])
            
            # Run Explainer
            explainer_result = run_explainer(
                ticker=ticker,
                as_of_date=as_of_date,
                human_rating=human_rating,
                ibes_df=ibes_df,
                fund_df=fund_df,
                news_df=news_df,
            )
            
            explanation = explainer_result.get("explanation", "")
            
            # Get ground truth
            ground_truth = get_ground_truth(row, fund_df, news_df)
            
            # Compute metrics
            faithfulness = compute_faithfulness(explanation, ground_truth)
            sentiment = compute_sentiment_alignment(explanation, human_rating)
            coverage = compute_coverage(explanation, ground_truth)
            
            # Build result row
            # Convert lists to strings for CSV compatibility
            available_sources_str = ", ".join(coverage.get("available_sources", []))
            mentioned_sources_str = ", ".join(coverage.get("mentioned_sources", []))
            
            result_row = {
                "ticker": ticker,
                "as_of_date": as_of_date,
                "human_rating": human_rating,
                "explanation": explanation,
                **faithfulness,
                **sentiment,
                "coverage_score": coverage.get("coverage_score"),
                "available_sources": available_sources_str,
                "mentioned_sources": mentioned_sources_str,
            }
            
            results.append(result_row)
            
        except Exception as e:
            if verbose:
                print(f"  ⚠ Error processing row {idx}: {e}")
            continue
    
    if len(results) == 0:
        raise ValueError("No explanations were successfully generated")
    
    return pd.DataFrame(results)


def save_explainer_results(
    results_df: pd.DataFrame,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Tuple[Path, Path]:
    """
    Save Explainer evaluation results to CSV and JSON summary.
    
    Args:
        results_df: Results DataFrame from evaluate_explainer()
        output_dir: Output directory
        
    Returns:
        Tuple of (csv_path, json_path)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    csv_path = output_dir / "explainer_results.csv"
    results_df.to_csv(csv_path, index=False)
    
    # Compute summary statistics
    n_cases = len(results_df)
    mean_faithfulness = results_df["faithfulness_score"].mean() if "faithfulness_score" in results_df.columns else None
    sentiment_aligned = results_df["sentiment_aligned_with_rating"].sum() if "sentiment_aligned_with_rating" in results_df.columns else 0
    sentiment_aligned_pct = (sentiment_aligned / n_cases * 100) if n_cases > 0 else 0
    mean_coverage = results_df["coverage_score"].mean() if "coverage_score" in results_df.columns else None
    
    summary = {
        "n_cases": n_cases,
        "mean_faithfulness_score": float(mean_faithfulness) if mean_faithfulness is not None else None,
        "sentiment_aligned_count": int(sentiment_aligned),
        "sentiment_aligned_percent": float(sentiment_aligned_pct),
        "mean_coverage_score": float(mean_coverage) if mean_coverage is not None else None,
    }
    
    # Save JSON
    json_path = output_dir / "explainer_summary.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    return csv_path, json_path


def print_explainer_summary(results_df: pd.DataFrame):
    """
    Print a brief summary of Explainer evaluation results.
    
    Args:
        results_df: Results DataFrame from evaluate_explainer()
    """
    n_cases = len(results_df)
    
    mean_faithfulness = results_df["faithfulness_score"].mean() if "faithfulness_score" in results_df.columns else None
    sentiment_aligned = results_df["sentiment_aligned_with_rating"].sum() if "sentiment_aligned_with_rating" in results_df.columns else 0
    sentiment_aligned_pct = (sentiment_aligned / n_cases * 100) if n_cases > 0 else 0
    mean_coverage = results_df["coverage_score"].mean() if "coverage_score" in results_df.columns else None
    
    print("\n" + "=" * 80)
    print("Explainer Evaluation Summary")
    print("=" * 80)
    print(f"  Cases: {n_cases}")
    
    if mean_faithfulness is not None:
        print(f"  Mean faithfulness score: {mean_faithfulness:.2f}")
    else:
        print(f"  Mean faithfulness score: N/A")
    
    print(f"  Sentiment aligned with rating: {sentiment_aligned}/{n_cases} ({sentiment_aligned_pct:.1f}%)")
    
    if mean_coverage is not None:
        print(f"  Mean coverage score: {mean_coverage:.2f}")
    else:
        print(f"  Mean coverage score: N/A")
    
    print("=" * 80)

