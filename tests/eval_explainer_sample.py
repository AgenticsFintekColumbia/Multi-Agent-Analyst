"""
Evaluation script for Explainer mode - Sampling & Export

This script:
1. Loads IBES recommendations and computes data completeness scores
2. Selects top-N recommendations with best data coverage
3. Runs Explainer on each sample
4. Exports results to CSV for human evaluation
"""

import os
import sys
import argparse
import csv
import pandas as pd
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_loader import load_datasets
from src.explainer import run_multi_analyst_explainer

# Column sets for data completeness scoring (from recommender orchestrator)
TECHNICAL_COLS = [
    "price_adjusted", "volume_adjusted", "daily_return_adjusted",
    "daily_return_excluding_dividends", "shares_outstanding",
    "mean_30d_returns", "vol_30d_returns", "mean_30d_vol", "vol_spike",
    "ewma_vol", "rsi_14", "macd_line", "macd_signal", "macd_hist",
]

FUNDAMENTAL_COLS = [
    "epsfxq_ffill", "eps_yoy_growth", "eps_ttm", "niq_ffill", "ceqq_ffill", "roe",
    "atq_ffill", "ltq_ffill", "dlttq_ffill", "lctq_ffill", "leverage",
    "longterm_debt_ratio", "debt_to_equity", "shortterm_liab_ratio", "cash_ratio",
    "oancfy_ffill", "ivncfy_ffill", "fincfy_ffill", "capxy_ffill", "fcf",
    "ocf_to_assets", "fcf_to_sales", "ocf_to_ni", "cash_flow_to_debt",
    "net_cash_flow", "reinvestment_rate", "croe", "fcf_yield_assets",
    "eps_growth_2q", "eps_growth_4q",
]


def compute_data_completeness_score(
    rec_series: pd.Series,
    fund_df: pd.DataFrame,
    news_df: pd.DataFrame,
    fund_window_days: int = 90,
    news_window_days: int = 30,
) -> dict:
    """
    Compute data completeness score for a recommendation.
    
    Returns a dict with:
    - fund_non_null_ratio: ratio of non-null fundamental columns
    - tech_non_null_ratio: ratio of non-null technical columns
    - has_news_indicator: 1 if news exists, else 0
    - news_count: number of news items in window
    - data_completeness_score: combined score (fund + tech + news indicator)
    """
    cusip = rec_series["cusip"]
    ann_date = rec_series["anndats"]
    
    if pd.isna(ann_date) or pd.isna(cusip):
        return {
            "fund_non_null_ratio": 0.0,
            "tech_non_null_ratio": 0.0,
            "has_news_indicator": 0,
            "news_count": 0,
            "data_completeness_score": 0.0,
        }
    
    # Get FUND data for this company in the window before rec date
    fund_company = fund_df[fund_df["cusip"] == cusip].copy()
    start_date = ann_date - timedelta(days=fund_window_days)
    fund_window = fund_company[
        (fund_company["date"] >= start_date) & 
        (fund_company["date"] < ann_date)
    ].sort_values("date")
    
    # Compute fundamental completeness
    fund_non_null_ratio = 0.0
    tech_non_null_ratio = 0.0
    
    if len(fund_window) > 0:
        latest = fund_window.iloc[-1]
        
        # Check which fundamental columns exist in the dataframe
        available_fund_cols = [c for c in FUNDAMENTAL_COLS if c in fund_df.columns]
        if len(available_fund_cols) > 0:
            non_null_fund = latest[available_fund_cols].notna().sum()
            fund_non_null_ratio = non_null_fund / len(available_fund_cols)
        
        # Check which technical columns exist in the dataframe
        available_tech_cols = [c for c in TECHNICAL_COLS if c in fund_df.columns]
        if len(available_tech_cols) > 0:
            non_null_tech = latest[available_tech_cols].notna().sum()
            tech_non_null_ratio = non_null_tech / len(available_tech_cols)
    
    # Get NEWS data
    news_company = news_df[news_df["cusip"] == cusip].copy()
    news_start = ann_date - timedelta(days=news_window_days)
    news_end = ann_date + timedelta(days=news_window_days)
    news_window = news_company[
        (news_company["announcedate"] >= news_start)
        & (news_company["announcedate"] <= news_end)
    ]
    
    news_count = len(news_window)
    has_news_indicator = 1 if news_count > 0 else 0
    
    # Combined score: fund + tech + news indicator (max 3.0)
    data_completeness_score = fund_non_null_ratio + tech_non_null_ratio + has_news_indicator
    
    return {
        "fund_non_null_ratio": fund_non_null_ratio,
        "tech_non_null_ratio": tech_non_null_ratio,
        "has_news_indicator": has_news_indicator,
        "news_count": news_count,
        "data_completeness_score": data_completeness_score,
    }


def extract_manager_markdown(full_markdown: str) -> str:
    """
    Extract just the manager's explanation from the full markdown.
    The manager report is everything before "# 📊 Individual Analyst Reports".
    """
    marker = "# 📊 Individual Analyst Reports"
    if marker in full_markdown:
        return full_markdown.split(marker, 1)[0].strip()
    # Fallback: look for first analyst-style heading
    analyst_markers = [
        "## 1️⃣ Fundamental Analyst Report",
        "## Fundamental Analyst Report",
        "## 2️⃣ Technical Analyst Report",
        "## Technical Analyst Report",
    ]
    for m in analyst_markers:
        if m in full_markdown:
            return full_markdown.split(m, 1)[0].strip()
    return full_markdown.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Sample high-quality recommendations for Explainer evaluation"
    )
    parser.add_argument(
        "--n_samples",
        type=int,
        default=20,
        help="Number of samples to generate (default: 20)",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="evaluation/explainer_human_study_samples.csv",
        help="Output CSV path (default: evaluation/explainer_human_study_samples.csv)",
    )
    parser.add_argument(
        "--fund_window_days",
        type=int,
        default=90,
        help="Fundamental/technical data window in days (default: 90)",
    )
    parser.add_argument(
        "--news_window_days",
        type=int,
        default=30,
        help="News data window in days (default: 30)",
    )
    parser.add_argument(
        "--max_candidates",
        type=int,
        default=1000,
        help="Maximum number of candidates to score (default: 1000, use 0 for all)",
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
    print("EXPLAINER EVALUATION: Sampling High-Quality Recommendations")
    print("=" * 70)
    print()
    
    # Load datasets
    print("Loading datasets...")
    ibes, fund, news = load_datasets(data_dir="data/")
    print(f"✓ Loaded {len(ibes)} IBES recommendations")
    print(f"✓ Loaded {len(fund)} FUND rows")
    print(f"✓ Loaded {len(news)} NEWS items")
    print()
    
    # Filter IBES to valid recommendations (has date and cusip)
    print("Filtering valid recommendations...")
    valid_ibes = ibes[
        ibes["anndats"].notna() & ibes["cusip"].notna()
    ].copy()
    print(f"✓ {len(valid_ibes)} valid recommendations (with date and CUSIP)")
    print()
    
    # Limit candidates if specified
    if args.max_candidates > 0 and len(valid_ibes) > args.max_candidates:
        print(f"Limiting to first {args.max_candidates} candidates for scoring...")
        candidates = valid_ibes.head(args.max_candidates).copy()
    else:
        candidates = valid_ibes.copy()
    
    # Compute data completeness scores for all candidates
    print("Computing data completeness scores...")
    print("(This may take a minute...)")
    print()
    
    scores = []
    for idx, rec in candidates.iterrows():
        score_dict = compute_data_completeness_score(
            rec,
            fund,
            news,
            fund_window_days=args.fund_window_days,
            news_window_days=args.news_window_days,
        )
        score_dict["rec_index"] = idx
        scores.append(score_dict)
    
    # Create scores dataframe
    scores_df = pd.DataFrame(scores)
    
    # Merge with IBES to get recommendation details
    scores_df = scores_df.merge(
        candidates[["ticker", "cname", "anndats", "etext", "cusip"]],
        left_on="rec_index",
        right_index=True,
        how="left",
    )
    
    # Sort by data completeness score (descending)
    scores_df = scores_df.sort_values("data_completeness_score", ascending=False)
    
    print(f"Data completeness score statistics:")
    print(f"  Mean: {scores_df['data_completeness_score'].mean():.2f} / 3.0")
    print(f"  Min:  {scores_df['data_completeness_score'].min():.2f} / 3.0")
    print(f"  Max:  {scores_df['data_completeness_score'].max():.2f} / 3.0")
    print()
    
    # Select top N
    n_samples = min(args.n_samples, len(scores_df))
    selected = scores_df.head(n_samples).copy()
    
    print(f"Selected top {n_samples} recommendations by data completeness score")
    print(f"  Mean score of selected: {selected['data_completeness_score'].mean():.2f} / 3.0")
    print(f"  Min score of selected:  {selected['data_completeness_score'].min():.2f} / 3.0")
    print()
    
    # Run Explainer on each selected recommendation
    print("=" * 70)
    print("Running Explainer on selected samples...")
    print("=" * 70)
    print()
    
    results = []
    
    for i, row in selected.iterrows():
        rec_index = int(row["rec_index"])
        ticker = str(row.get("ticker", "N/A"))
        company = str(row.get("cname", "N/A"))
        rec_date = row["anndats"]
        human_rating = str(row.get("etext", "N/A"))
        
        print(f"[{len(results) + 1}/{n_samples}] Processing: {ticker} ({company})")
        print(f"  Date: {rec_date.date() if pd.notna(rec_date) else 'N/A'}")
        print(f"  Rating: {human_rating}")
        print(f"  Data completeness: {row['data_completeness_score']:.2f} / 3.0")
        print()
        
        try:
            # Run Explainer
            full_markdown = run_multi_analyst_explainer(
                ibes_df=ibes,
                fund_df=fund,
                news_df=news,
                rec_index=rec_index,
                fund_window_days=args.fund_window_days,
                news_window_days=args.news_window_days,
            )
            
            # Extract manager markdown (everything before "---")
            manager_markdown = extract_manager_markdown(full_markdown)
            
            # Extract individual reports (optional, for reference)
            if "## 1️⃣ Fundamental Analyst Report" in full_markdown:
                parts = full_markdown.split("## 1️⃣ Fundamental Analyst Report")
                if len(parts) > 1:
                    rest = parts[1]
                    if "## 2️⃣ Technical Analyst Report" in rest:
                        fundamental_report = rest.split("## 2️⃣ Technical Analyst Report")[0].strip()
                    else:
                        fundamental_report = rest.strip()
                else:
                    fundamental_report = ""
            else:
                fundamental_report = ""
            
            if "## 2️⃣ Technical Analyst Report" in full_markdown:
                parts = full_markdown.split("## 2️⃣ Technical Analyst Report")
                if len(parts) > 1:
                    rest = parts[1]
                    if "## 3️⃣ News & Sentiment Analyst Report" in rest:
                        technical_report = rest.split("## 3️⃣ News & Sentiment Analyst Report")[0].strip()
                    else:
                        technical_report = rest.strip()
                else:
                    technical_report = ""
            else:
                technical_report = ""
            
            if "## 3️⃣ News & Sentiment Analyst Report" in full_markdown:
                parts = full_markdown.split("## 3️⃣ News & Sentiment Analyst Report")
                if len(parts) > 1:
                    news_report = parts[1].strip()
                else:
                    news_report = ""
            else:
                news_report = ""
            
            results.append({
                "sample_id": len(results) + 1,
                "rec_index": rec_index,
                "ticker": ticker,
                "company": company,
                "rec_date": rec_date.date() if pd.notna(rec_date) else None,
                "human_rating": human_rating,
                "data_completeness_score": row["data_completeness_score"],
                "fund_non_null_ratio": row["fund_non_null_ratio"],
                "tech_non_null_ratio": row["tech_non_null_ratio"],
                "news_count": row["news_count"],
                "explainer_manager_markdown": manager_markdown,
                "fundamental_report": fundamental_report,
                "technical_report": technical_report,
                "news_report": news_report,
                # Empty columns for human evaluation
                "plausibility_1_5": "",
                "signal_coverage_1_5": "",
                "internal_consistency_1_5": "",
                "mentions_fundamental": "",
                "mentions_technical": "",
                "mentions_news": "",
                "calls_out_missing_data": "",
            })
            
            print(f"  ✓ Complete")
            print()
            
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            print()
            import traceback
            traceback.print_exc()
            continue
    
    # Create output DataFrame
    output_df = pd.DataFrame(results)
    
    # Ensure output directory exists
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV with UTF-8 encoding and proper quoting to handle commas/newlines in markdown
    output_df.to_csv(
        output_path, 
        index=False, 
        encoding='utf-8-sig',
        quoting=csv.QUOTE_ALL,  # Quote all fields to handle commas/newlines
        escapechar='\\'  # Escape special characters
    )
    
    print("=" * 70)
    print("✓ Sampling Complete!")
    print("=" * 70)
    print()
    print(f"Generated {len(results)} explainer samples at {args.output_path}")
    print(f"Mean data completeness score of selected samples: {output_df['data_completeness_score'].mean():.2f} / 3.0")
    print(f"Min data completeness score: {output_df['data_completeness_score'].min():.2f} / 3.0")
    print(f"Max data completeness score: {output_df['data_completeness_score'].max():.2f} / 3.0")
    print()
    print("Next steps:")
    print("1. Open the CSV file and fill in the rating columns:")
    print("   - plausibility_1_5")
    print("   - signal_coverage_1_5")
    print("   - internal_consistency_1_5")
    print("   - mentions_fundamental (yes/no/na)")
    print("   - mentions_technical (yes/no/na)")
    print("   - mentions_news (yes/no/na)")
    print("   - calls_out_missing_data (yes/no/na)")
    print("2. Save the CSV with a new name (e.g., explainer_human_study_samples_rated.csv)")
    print("3. Run: python tests/eval_explainer_aggregate.py --input_path <rated_csv_path>")


if __name__ == "__main__":
    main()

