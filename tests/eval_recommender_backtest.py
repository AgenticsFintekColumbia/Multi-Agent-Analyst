"""
Evaluation script for Recommender mode - Backtest

This script:
1. Runs Recommender on historical IBES recommendations
2. Records model rating, human rating, and future returns
3. Computes trading signals and P&L
4. Exports results to CSV for analysis
"""

import os
import sys
import argparse
import csv
import re
import pandas as pd
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_loader import load_datasets
from src.recommender import run_multi_analyst_recommendation
from backend.utils import split_manager_and_analysts, extract_final_rating


def normalize_human_rating(rating_text: str) -> str:
    """
    Normalize human analyst rating text to standard categories.
    
    Returns: "Buy", "Sell", or "Hold"
    """
    if pd.isna(rating_text) or not rating_text:
        return "Hold"
    
    rating_upper = str(rating_text).upper().strip()
    
    # Buy signals
    if any(keyword in rating_upper for keyword in ["BUY", "OUTPERFORM", "OVERWEIGHT", "STRONG BUY", "STRONGBUY", "POSITIVE"]):
        return "Buy"
    
    # Sell signals
    if any(keyword in rating_upper for keyword in ["SELL", "UNDERPERFORM", "UNDERWEIGHT", "NEGATIVE"]):
        return "Sell"
    
    # Hold signals (default)
    if any(keyword in rating_upper for keyword in ["HOLD", "NEUTRAL", "IN-LINE", "MARKET PERFORM", "EQUAL", "EQUALWEIGHT"]):
        return "Hold"
    
    # Default to Hold if unclear
    return "Hold"


def rating_to_signal(rating: str) -> int:
    """
    Convert rating to trading signal.
    
    Returns:
        +1 for Buy/StrongBuy (go long)
        -1 for Sell/UnderPerform (go short)
        0 for Hold (no position)
    """
    rating_upper = str(rating).upper().strip()
    
    if rating_upper in ["BUY", "STRONGBUY", "STRONG BUY"]:
        return 1
    elif rating_upper in ["SELL", "UNDERPERFORM"]:
        return -1
    else:  # Hold or unknown
        return 0


def compute_future_returns(
    cusip: str,
    rec_date: pd.Timestamp,
    fund_df: pd.DataFrame,
    days_1m: int = 21,
    days_3m: int = 63,
) -> dict:
    """
    Compute future 1-month and 3-month returns.
    
    Returns dict with:
    - return_1m: 1-month forward return (or None if unavailable)
    - return_3m: 3-month forward return (or None if unavailable)
    - price_at_rec: price at recommendation date (or None)
    - price_1m: price 1 month later (or None)
    - price_3m: price 3 months later (or None)
    """
    # Get FUND data for this company
    fund_company = fund_df[fund_df["cusip"] == cusip].copy()
    
    if fund_company.empty:
        return {
            "return_1m": None,
            "return_3m": None,
            "price_at_rec": None,
            "price_1m": None,
            "price_3m": None,
        }
    
    # Find price at or before rec_date (use most recent available)
    fund_before = fund_company[fund_company["date"] <= rec_date].sort_values("date")
    
    if fund_before.empty:
        return {
            "return_1m": None,
            "return_3m": None,
            "price_at_rec": None,
            "price_1m": None,
            "price_3m": None,
        }
    
    # Get price at rec_date (or most recent before)
    price_at_rec = None
    price_col = "price_adjusted" if "price_adjusted" in fund_before.columns else "price"
    
    if price_col in fund_before.columns:
        latest_row = fund_before.iloc[-1]
        price_at_rec = latest_row[price_col]
        rec_date_actual = latest_row["date"]  # Use actual data date
    else:
        return {
            "return_1m": None,
            "return_3m": None,
            "price_at_rec": None,
            "price_1m": None,
            "price_3m": None,
        }
    
    if pd.isna(price_at_rec) or price_at_rec <= 0:
        return {
            "return_1m": None,
            "return_3m": None,
            "price_at_rec": None,
            "price_1m": None,
            "price_3m": None,
        }
    
    # Find prices at future dates
    date_1m = rec_date_actual + timedelta(days=days_1m)
    date_3m = rec_date_actual + timedelta(days=days_3m)
    
    # Get prices at or after target dates (use earliest available after target)
    fund_after_1m = fund_company[fund_company["date"] >= date_1m].sort_values("date")
    fund_after_3m = fund_company[fund_company["date"] >= date_3m].sort_values("date")
    
    price_1m = None
    price_3m = None
    
    if not fund_after_1m.empty and price_col in fund_after_1m.columns:
        price_1m = fund_after_1m.iloc[0][price_col]
    
    if not fund_after_3m.empty and price_col in fund_after_3m.columns:
        price_3m = fund_after_3m.iloc[0][price_col]
    
    # Compute returns
    return_1m = None
    return_3m = None
    
    if pd.notna(price_1m) and price_1m > 0:
        return_1m = (price_1m / price_at_rec) - 1.0
    
    if pd.notna(price_3m) and price_3m > 0:
        return_3m = (price_3m / price_at_rec) - 1.0
    
    return {
        "return_1m": return_1m,
        "return_3m": return_3m,
        "price_at_rec": price_at_rec,
        "price_1m": price_1m,
        "price_3m": price_3m,
    }


def compute_directional_correctness(signal: int, return_val: float) -> int:
    """
    Check if signal direction matches return direction.
    
    Returns:
        1 if sign(signal) == sign(return) and signal != 0
        0 otherwise (including Hold signals)
    """
    if signal == 0 or pd.isna(return_val):
        return 0
    
    signal_sign = 1 if signal > 0 else -1
    return_sign = 1 if return_val > 0 else -1
    
    return 1 if signal_sign == return_sign else 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate backtest dataset for Recommender evaluation"
    )
    parser.add_argument(
        "--max_samples",
        type=int,
        default=300,
        help="Maximum number of recommendations to process (default: 300)",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="evaluation/recommender_backtest_trades.csv",
        help="Output CSV path (default: evaluation/recommender_backtest_trades.csv)",
    )
    parser.add_argument(
        "--news_window_days",
        type=int,
        default=30,
        help="News window in days for Recommender (default: 30)",
    )
    parser.add_argument(
        "--random_seed",
        type=int,
        default=42,
        help="Random seed for sampling (default: 42)",
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    try:
        load_dotenv()
    except Exception:
        pass
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("=" * 70)
        print("ERROR: Gemini API key not found!")
        print("=" * 70)
        print("\nPlease create a .env file with your Gemini API key.")
        sys.exit(1)
    
    print("=" * 70)
    print("RECOMMENDER BACKTEST: Generating Trading Dataset")
    print("=" * 70)
    print()
    
    # Load datasets
    print("Loading datasets...")
    ibes, fund, news = load_datasets(data_dir="data/")
    print(f"✓ Loaded {len(ibes)} IBES recommendations")
    print(f"✓ Loaded {len(fund)} FUND rows")
    print(f"✓ Loaded {len(news)} NEWS items")
    print()
    
    # Filter IBES to valid recommendations (has date, cusip, and rating)
    print("Filtering valid recommendations...")
    valid_ibes = ibes[
        ibes["anndats"].notna() 
        & ibes["cusip"].notna()
        & ibes["etext"].notna()
    ].copy()
    print(f"✓ {len(valid_ibes)} valid recommendations (with date, CUSIP, and rating)")
    print()
    
    # Sample recommendations
    if len(valid_ibes) > args.max_samples:
        print(f"Sampling {args.max_samples} recommendations (random seed: {args.random_seed})...")
        sampled = valid_ibes.sample(n=args.max_samples, random_state=args.random_seed).copy()
    else:
        print(f"Using all {len(valid_ibes)} recommendations...")
        sampled = valid_ibes.copy()
    
    sampled = sampled.sort_values("anndats").reset_index(drop=True)
    print(f"✓ Selected {len(sampled)} recommendations")
    print()
    
    # Process each recommendation
    print("=" * 70)
    print("Running Recommender and computing returns...")
    print("=" * 70)
    print()
    
    results = []
    
    for idx, rec in sampled.iterrows():
        rec_index = rec.name  # Original index in IBES
        ticker = str(rec.get("ticker", "N/A"))
        company = str(rec.get("cname", "N/A"))
        rec_date = rec["anndats"]
        cusip = rec["cusip"]
        human_raw_rating = str(rec.get("etext", "N/A"))
        
        print(f"[{idx + 1}/{len(sampled)}] Processing: {ticker} ({company})")
        print(f"  Date: {rec_date.date() if pd.notna(rec_date) else 'N/A'}")
        print(f"  Human rating: {human_raw_rating}")
        
        # Normalize human rating
        human_normalized = normalize_human_rating(human_raw_rating)
        human_signal = rating_to_signal(human_normalized)
        
        # Compute future returns
        returns = compute_future_returns(cusip, rec_date, fund)
        
        if returns["return_1m"] is None and returns["return_3m"] is None:
            print(f"  ⚠ Skipping: No future price data available")
            print()
            continue
        
        # Run Recommender
        try:
            print(f"  Running Recommender...")
            reco_md = run_multi_analyst_recommendation(
                cusip=str(cusip),
                rec_date=rec_date,
                fund_df=fund,
                news_df=news,
                news_window_days=args.news_window_days,
                ticker=ticker,
                company=company,
            )
            
            # Extract model rating
            manager_md, _ = split_manager_and_analysts(reco_md)
            model_raw_rating = extract_final_rating(manager_md or reco_md)
            
            if not model_raw_rating:
                print(f"  ⚠ Skipping: Could not extract model rating")
                print()
                continue
            
            model_signal = rating_to_signal(model_raw_rating)
            
            print(f"  Model rating: {model_raw_rating} (signal: {model_signal})")
            
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            print()
            import traceback
            traceback.print_exc()
            continue
        
        # Compute P&L
        return_1m = returns["return_1m"] if returns["return_1m"] is not None else 0.0
        return_3m = returns["return_3m"] if returns["return_3m"] is not None else 0.0
        
        model_pnl_1m = model_signal * return_1m if returns["return_1m"] is not None else None
        human_pnl_1m = human_signal * return_1m if returns["return_1m"] is not None else None
        baseline_pnl_1m = 1.0 * return_1m if returns["return_1m"] is not None else None  # Always long
        
        model_pnl_3m = model_signal * return_3m if returns["return_3m"] is not None else None
        human_pnl_3m = human_signal * return_3m if returns["return_3m"] is not None else None
        baseline_pnl_3m = 1.0 * return_3m if returns["return_3m"] is not None else None  # Always long
        
        # Directional correctness
        model_dir_correct_1m = compute_directional_correctness(model_signal, return_1m) if returns["return_1m"] is not None else None
        human_dir_correct_1m = compute_directional_correctness(human_signal, return_1m) if returns["return_1m"] is not None else None
        
        model_dir_correct_3m = compute_directional_correctness(model_signal, return_3m) if returns["return_3m"] is not None else None
        human_dir_correct_3m = compute_directional_correctness(human_signal, return_3m) if returns["return_3m"] is not None else None
        
        results.append({
            "rec_index": rec_index,
            "ticker": ticker,
            "company": company,
            "rec_date": rec_date.date() if pd.notna(rec_date) else None,
            "human_raw_rating": human_raw_rating,
            "human_normalized": human_normalized,
            "model_raw_rating": model_raw_rating,
            "human_signal": human_signal,
            "model_signal": model_signal,
            "baseline_signal": 1,  # Always long
            "return_1m": return_1m,
            "return_3m": return_3m,
            "model_pnl_1m": model_pnl_1m,
            "human_pnl_1m": human_pnl_1m,
            "baseline_pnl_1m": baseline_pnl_1m,
            "model_pnl_3m": model_pnl_3m,
            "human_pnl_3m": human_pnl_3m,
            "baseline_pnl_3m": baseline_pnl_3m,
            "model_dir_correct_1m": model_dir_correct_1m,
            "human_dir_correct_1m": human_dir_correct_1m,
            "model_dir_correct_3m": model_dir_correct_3m,
            "human_dir_correct_3m": human_dir_correct_3m,
        })
        
        print(f"  ✓ Complete (1M return: {return_1m:.2%}, 3M return: {return_3m:.2%})")
        print()
    
    # Create output DataFrame
    output_df = pd.DataFrame(results)
    
    if len(output_df) == 0:
        print("ERROR: No valid trades generated. Check data availability.")
        return
    
    # Ensure output directory exists
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV with proper encoding and quoting
    output_df.to_csv(
        output_path,
        index=False,
        encoding='utf-8-sig',
        quoting=csv.QUOTE_ALL,
        escapechar='\\'
    )
    
    print("=" * 70)
    print("✓ Backtest Dataset Generation Complete!")
    print("=" * 70)
    print()
    print(f"Generated {len(output_df)} trades at {args.output_path}")
    print()
    print("Summary:")
    print(f"  Valid 1M returns: {output_df['return_1m'].notna().sum()}")
    print(f"  Valid 3M returns: {output_df['return_3m'].notna().sum()}")
    print()
    print("Next step: Run aggregation script:")
    print(f"  python tests/eval_recommender_backtest_aggregate.py --input_path {args.output_path}")


if __name__ == "__main__":
    main()

