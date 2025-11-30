"""
CLI driver script for evaluation framework.

Runs end-to-end evaluation:
1. Build universe
2. (Optionally) stratified sample
3. Generate AI signals
4. Compute IC + decay
5. Run portfolio backtest
6. Run consensus vs contrarian analysis
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

from .config import (
    DEFAULT_DATA_DIR,
    DEFAULT_START_DATE,
    DEFAULT_END_DATE,
    DEFAULT_HORIZONS,
    PRIMARY_HORIZON,
    DEFAULT_MAX_SAMPLES,
    DEFAULT_OUTPUT_DIR,
)
from .data import load_datasets, build_evaluation_universe, stratified_sample
from .signal import generate_signals_for_universe
from .backtest import (
    compute_ic_series,
    compute_ic_statistics,
    compute_decay_analysis,
    run_portfolio_backtest,
    compute_performance_metrics,
)
from .analysis import (
    analyze_consensus_contrarian,
    analyze_by_year,
    analyze_by_regime,
    separate_holdout_period,
)
from .explainer_evaluation import (
    evaluate_explainer,
    save_explainer_results,
    print_explainer_summary,
)


def format_number(value, decimals=4):
    """Format number for display."""
    if value is None or pd.isna(value):
        return "N/A"
    try:
        return f"{value:.{decimals}f}"
    except (TypeError, ValueError):
        return "N/A"


def print_summary(results: dict):
    """Print a concise text summary of evaluation results."""
    
    def safe_get(row, key, default=None):
        """Safely get value from pandas Series row, handling missing columns and None/NaN."""
        try:
            if key in row.index:
                val = row[key]
                return default if (val is None or pd.isna(val)) else val
            return default
        except (KeyError, IndexError, AttributeError):
            return default
    
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    
    # IC Statistics
    if "ic_stats" in results:
        print("\n📊 Information Coefficient (IC) Statistics")
        print("-" * 80)
        ic = results["ic_stats"]
        n_obs = ic.get('n_observations', 0)
        if n_obs == 0:
            print("  Not enough observations to compute IC statistics (N=0).")
            print("  Need at least 2 unique dates with valid signals and returns.")
        else:
            print(f"  Mean IC:           {format_number(ic.get('mean_ic'))}")
            print(f"  Std Dev:           {format_number(ic.get('std_ic'))}")
            print(f"  Newey-West t-stat: {format_number(ic.get('t_stat'))}")
            print(f"  Hit Ratio:         {format_number(ic.get('hit_ratio'), 2)}")
            print(f"  Observations:      {n_obs}")
    
    # Decay Analysis
    if "decay" in results and len(results["decay"]) > 0:
        print("\n📉 Signal Decay Analysis")
        print("-" * 80)
        print("  Horizon (days) | Mean IC | t-stat | Hit Ratio")
        print("  " + "-" * 50)
        for _, row in results["decay"].iterrows():
            print(f"  {int(row['horizon']):13d} | {format_number(row['mean_ic']):7s} | "
                  f"{format_number(row['t_stat']):6s} | {format_number(row['hit_ratio'], 2):9s}")
    
    # Portfolio Performance
    if "portfolio_metrics" in results:
        print("\n💰 Portfolio Performance")
        print("-" * 80)
        pm = results["portfolio_metrics"]
        if pm is None:
            print("  Not enough observations to compute portfolio metrics.")
        else:
            cagr = pm.get('cagr')
            volatility = pm.get('volatility')
            sharpe = pm.get('sharpe')
            max_dd = pm.get('max_drawdown')
            calmar = pm.get('calmar')
            
            # Safely format CAGR with percentage
            cagr_str = format_number(cagr, 4)
            cagr_pct = "N/A"
            if cagr is not None and not pd.isna(cagr):
                try:
                    cagr_pct = format_number(cagr * 100, 2) + "%"
                except (TypeError, ValueError):
                    pass
            
            # Safely format volatility with percentage
            vol_str = format_number(volatility, 4)
            vol_pct = "N/A"
            if volatility is not None and not pd.isna(volatility):
                try:
                    vol_pct = format_number(volatility * 100, 2) + "%"
                except (TypeError, ValueError):
                    pass
            
            # Safely format max drawdown with percentage
            dd_str = format_number(max_dd, 4)
            dd_pct = "N/A"
            if max_dd is not None and not pd.isna(max_dd):
                try:
                    dd_pct = format_number(max_dd * 100, 2) + "%"
                except (TypeError, ValueError):
                    pass
            
            print(f"  CAGR:             {cagr_str} ({cagr_pct})")
            print(f"  Volatility:       {vol_str} ({vol_pct})")
            print(f"  Sharpe Ratio:     {format_number(sharpe)}")
            print(f"  Max Drawdown:     {dd_str} ({dd_pct})")
            print(f"  Calmar Ratio:     {format_number(calmar)}")
    
    # Consensus vs Contrarian
    if "consensus_contrarian" in results and len(results["consensus_contrarian"]) > 0:
        print("\n🤝 Consensus vs Contrarian Analysis")
        print("-" * 80)
        print("  Bucket              | Avg Return | Count | IC Mean | t-stat")
        print("  " + "-" * 65)
        for _, row in results["consensus_contrarian"].iterrows():
            # Defensive access - handle missing columns gracefully
            bucket = safe_get(row, "bucket", "Unknown")
            
            # Safe access with fallback to None
            avg_ret_val = safe_get(row, "avg_return")
            avg_ret = format_number(avg_ret_val, 4)
            
            count_val = safe_get(row, "count", 0)
            try:
                count = int(count_val) if count_val is not None and not pd.isna(count_val) else 0
            except (ValueError, TypeError):
                count = 0
            
            ic_mean_val = safe_get(row, "ic_mean")
            ic_mean = format_number(ic_mean_val)
            
            t_stat_val = safe_get(row, "t_stat")
            t_stat = format_number(t_stat_val)
            
            print(f"  {bucket:19s} | {avg_ret:10s} | {count:5d} | {ic_mean:7s} | {t_stat:6s}")
    elif "consensus_contrarian" in results:
        # Empty DataFrame - show message
        print("\n🤝 Consensus vs Contrarian Analysis")
        print("-" * 80)
        print("  No consensus/contrarian data available.")
    
    # Year Breakdown
    if "year_analysis" in results and len(results["year_analysis"]) > 0:
        print("\n📅 IC by Year")
        print("-" * 80)
        print("  Year | Mean IC | t-stat | Hit Ratio | N Obs")
        print("  " + "-" * 50)
        for _, row in results["year_analysis"].iterrows():
            # Defensive access
            year_val = safe_get(row, "year", 0)
            try:
                year = int(year_val) if year_val is not None and not pd.isna(year_val) else 0
            except (ValueError, TypeError):
                year = 0
            
            ic_mean = format_number(safe_get(row, "mean_ic"))
            t_stat = format_number(safe_get(row, "t_stat"))
            hit_ratio = format_number(safe_get(row, "hit_ratio"), 2)
            
            n_obs_val = safe_get(row, "n_observations", 0)
            try:
                n_obs = int(n_obs_val) if n_obs_val is not None and not pd.isna(n_obs_val) else 0
            except (ValueError, TypeError):
                n_obs = 0
            
            print(f"  {year:4d} | {ic_mean:7s} | {t_stat:6s} | {hit_ratio:9s} | {n_obs:5d}")
    
    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Recommender performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help=f"Start date (YYYY-MM-DD, default: {DEFAULT_START_DATE.date()})",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help=f"End date (YYYY-MM-DD, default: {DEFAULT_END_DATE.date()})",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=PRIMARY_HORIZON,
        help=f"Primary forward return horizon in days (default: {PRIMARY_HORIZON})",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Maximum number of (ticker, date) samples to evaluate (default: all)",
    )
    parser.add_argument(
        "--skip-signals",
        action="store_true",
        help="Skip signal generation (use existing signals in universe)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help=f"Output directory for CSV/JSON files (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help=f"Data directory (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--run-explainer",
        action="store_true",
        default=False,
        help="Run Explainer evaluation (evaluates explanation quality)",
    )
    parser.add_argument(
        "--explainer-sample-size",
        type=int,
        default=5,
        help="Number of cases to evaluate for Explainer (default: 5)",
    )
    
    args = parser.parse_args()
    
    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d") if args.start_date else DEFAULT_START_DATE
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else DEFAULT_END_DATE
    
    # Output directory
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Data directory
    data_dir = Path(args.data_dir) if args.data_dir else DEFAULT_DATA_DIR
    
    print("=" * 80)
    print("RECOMMENDER EVALUATION FRAMEWORK")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Start date:     {start_date.date()}")
    print(f"  End date:       {end_date.date()}")
    print(f"  Primary horizon: {args.horizon} days")
    print(f"  Max samples:    {args.max_samples or 'All'}")
    print(f"  Output dir:    {output_dir}")
    print(f"  Data dir:       {data_dir}")
    
    # Step 1: Load data
    print("\n" + "=" * 80)
    print("STEP 1: Loading Data")
    print("=" * 80)
    ibes, fund, news = load_datasets(data_dir=data_dir)
    
    # Step 2: Build universe
    print("\n" + "=" * 80)
    print("STEP 2: Building Evaluation Universe")
    print("=" * 80)
    universe = build_evaluation_universe(
        ibes_df=ibes,
        fund_df=fund,
        start_date=start_date,
        end_date=end_date,
        horizons=DEFAULT_HORIZONS,
        primary_horizon=args.horizon,
    )
    
    if len(universe) == 0:
        print("ERROR: No valid evaluation points found. Exiting.")
        return
    
    # Step 3: Stratified sampling (if requested)
    if args.max_samples is not None:
        print("\n" + "=" * 80)
        print("STEP 3: Stratified Sampling")
        print("=" * 80)
        
        # Warning for very small sample sizes
        if args.max_samples < 30:
            print(f"\n⚠️  Warning: max_samples is very small (N={args.max_samples}).")
            print("   IC and portfolio statistics may be undefined or unstable.")
            print("   Consider using at least 30-50 samples for reliable metrics.\n")
        
        universe = stratified_sample(
            universe=universe,
            max_samples=args.max_samples,
        )
    
    # Step 4: Generate signals (unless skipped)
    if not args.skip_signals:
        print("\n" + "=" * 80)
        print("STEP 4: Generating AI Signals")
        print("=" * 80)
        
        # Cache path for reusing previously computed signals
        cache_path = output_dir / "universe_with_signals.csv"
        
        universe = generate_signals_for_universe(
            universe=universe,
            fund_df=fund,
            news_df=news,
            max_samples=None,  # Already sampled if needed
            verbose=True,
            cache_path=cache_path,
        )
    else:
        print("\n" + "=" * 80)
        print("STEP 4: Skipping Signal Generation (using existing signals)")
        print("=" * 80)
    
    # Filter to rows with valid signals
    universe_with_signals = universe[universe["ai_signal"].notna()].copy()
    
    if len(universe_with_signals) == 0:
        print("ERROR: No valid AI signals found. Exiting.")
        return
    
    print(f"\n✓ Proceeding with {len(universe_with_signals)} evaluation points with signals")
    
    # Step 5: Compute IC and decay
    print("\n" + "=" * 80)
    print("STEP 5: Computing IC Statistics")
    print("=" * 80)
    
    return_col = f"forward_return_{args.horizon}d"
    
    ic_series = compute_ic_series(
        universe=universe_with_signals,
        signal_col="ai_signal",
        return_col=return_col,
        horizon=args.horizon,
    )
    
    # Check if we have enough observations for IC
    if len(ic_series) == 0:
        print(f"  ⚠ Not enough observations to compute IC statistics (N=0).")
        print("     Need at least 2 unique dates with valid signals and returns.")
        ic_stats = {
            "mean_ic": None,
            "std_ic": None,
            "t_stat": None,
            "hit_ratio": None,
            "n_observations": 0,
        }
    elif len(ic_series) < 5:
        print(f"  ⚠ Warning: Very few IC observations (N={len(ic_series)}).")
        print("     Statistics may be unreliable. Returning results anyway.")
        ic_stats = compute_ic_statistics(ic_series)
    else:
        ic_stats = compute_ic_statistics(ic_series)
    
    decay_df = compute_decay_analysis(
        universe=universe_with_signals,
        signal_col="ai_signal",
        horizons=DEFAULT_HORIZONS,
    )
    
    # Step 6: Portfolio backtest
    print("\n" + "=" * 80)
    print("STEP 6: Running Portfolio Backtest")
    print("=" * 80)
    
    backtest_df = run_portfolio_backtest(
        universe=universe_with_signals,
        signal_col="ai_signal",
        return_col=return_col,
        horizon=args.horizon,
    )
    
    portfolio_metrics = None
    if len(backtest_df) == 0:
        print(f"  ⚠ Not enough observations to run portfolio backtest (N=0).")
        print("     Need at least 1 date with valid portfolio construction.")
    elif len(backtest_df) < 5:
        print(f"  ⚠ Warning: Very few portfolio periods (N={len(backtest_df)}).")
        print("     Performance metrics may be unreliable. Computing anyway...")
        portfolio_metrics = compute_performance_metrics(
            return_series=backtest_df["net_return"],
            periods_per_year=252,  # Approximate trading days per year
        )
    else:
        portfolio_metrics = compute_performance_metrics(
            return_series=backtest_df["net_return"],
            periods_per_year=252,  # Approximate trading days per year
        )
    
    # Step 7: Consensus vs Contrarian
    print("\n" + "=" * 80)
    print("STEP 7: Consensus vs Contrarian Analysis")
    print("=" * 80)
    
    consensus_df = analyze_consensus_contrarian(
        universe=universe_with_signals,
        return_col=return_col,
        horizon=args.horizon,
    )
    
    # Step 8: Year and regime breakdowns
    print("\n" + "=" * 80)
    print("STEP 8: Cross-Sectional Analysis")
    print("=" * 80)
    
    year_df = analyze_by_year(
        universe=universe_with_signals,
        signal_col="ai_signal",
        return_col=return_col,
        horizon=args.horizon,
    )
    
    regime_df = analyze_by_regime(
        universe=universe_with_signals,
        signal_col="ai_signal",
        return_col=return_col,
        horizon=args.horizon,
    )
    
    # Compile results
    results = {
        "ic_stats": ic_stats,
        "decay": decay_df,
        "portfolio_metrics": portfolio_metrics,
        "consensus_contrarian": consensus_df,
        "year_analysis": year_df,
        "regime_analysis": regime_df,
    }
    
    # Print summary
    print_summary(results)
    
    # Save outputs
    print("\n" + "=" * 80)
    print("Saving Results")
    print("=" * 80)
    
    # Save universe with signals (this file also serves as cache for future runs)
    universe_path = output_dir / "universe_with_signals.csv"
    
    # If cache exists, merge with it to preserve previously computed signals
    # that might not be in the current run
    if universe_path.exists():
        try:
            existing_cache = pd.read_csv(universe_path)
            existing_cache["as_of_date"] = pd.to_datetime(existing_cache["as_of_date"])
            
            # Normalize tickers for merging
            universe_with_signals["ticker"] = universe_with_signals["ticker"].astype(str).str.strip().str.upper()
            existing_cache["ticker"] = existing_cache["ticker"].astype(str).str.strip().str.upper()
            
            # Merge: keep all rows from both, but prefer new signals over old
            merge_keys = ["ticker", "as_of_date"]
            if all(col in existing_cache.columns for col in merge_keys):
                # Combine: use new signals where available, keep old ones for rows not in current run
                combined = pd.concat([universe_with_signals, existing_cache], ignore_index=True)
                # Remove duplicates, keeping the first (newer) occurrence
                combined = combined.drop_duplicates(subset=merge_keys, keep="first")
                combined.to_csv(universe_path, index=False)
                print(f"  ✓ Saved universe (merged with cache): {universe_path}")
            else:
                # Fallback: just save current run
                universe_with_signals.to_csv(universe_path, index=False)
                print(f"  ✓ Saved universe: {universe_path}")
        except Exception as e:
            # If merging fails, just save current run
            universe_with_signals.to_csv(universe_path, index=False)
            print(f"  ✓ Saved universe (cache merge failed, saved current run): {universe_path}")
    else:
        universe_with_signals.to_csv(universe_path, index=False)
        print(f"  ✓ Saved universe (cache): {universe_path}")
    
    # Save IC series
    ic_path = output_dir / "ic_series.csv"
    if len(ic_series) > 0:
        ic_series.to_csv(ic_path)
        print(f"  ✓ Saved IC series: {ic_path}")
    else:
        # Save empty series with just header
        pd.Series(dtype=float, name="IC").to_csv(ic_path)
        print(f"  ✓ Saved empty IC series: {ic_path}")
    
    # Save decay analysis
    if len(decay_df) > 0:
        decay_path = output_dir / "decay_analysis.csv"
        decay_df.to_csv(decay_path, index=False)
        print(f"  ✓ Saved decay analysis: {decay_path}")
    
    # Save backtest results
    if len(backtest_df) > 0:
        backtest_path = output_dir / "portfolio_backtest.csv"
        backtest_df.to_csv(backtest_path, index=False)
        print(f"  ✓ Saved backtest results: {backtest_path}")
    
    # Save summary JSON
    summary_path = output_dir / "summary.json"
    
    # Convert DataFrames to dicts for JSON
    summary = {
        "ic_stats": ic_stats,
        "portfolio_metrics": portfolio_metrics,
    }
    
    if len(decay_df) > 0:
        summary["decay"] = decay_df.to_dict("records")
    
    if len(consensus_df) > 0:
        summary["consensus_contrarian"] = consensus_df.to_dict("records")
    
    if len(year_df) > 0:
        summary["year_analysis"] = year_df.to_dict("records")
    
    if len(regime_df) > 0:
        summary["regime_analysis"] = regime_df.to_dict("records")
    
    # Helper function for JSON serialization of None/NaN values
    def json_serializer(obj):
        """Custom JSON serializer for None, NaN, and other non-serializable values."""
        if obj is None:
            return None
        if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
            return None
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        if isinstance(obj, (pd.Timestamp, pd.Timedelta)):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")
    
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=json_serializer)
    
    print(f"  ✓ Saved summary: {summary_path}")
    
    print("\n" + "=" * 80)
    print("✓ Recommender Evaluation Complete!")
    print("=" * 80)
    
    # Explainer evaluation (if requested)
    if args.run_explainer:
        print("\n" + "=" * 80)
        print("EXPLAINER EVALUATION")
        print("=" * 80)
        
        try:
            # Use the same universe (before signal generation, since we need human_rating)
            # But we need to rebuild it to ensure we have human_rating
            explainer_universe = build_evaluation_universe(
                ibes_df=ibes,
                fund_df=fund,
                start_date=start_date,
                end_date=end_date,
                horizons=DEFAULT_HORIZONS,
                primary_horizon=args.horizon,
            )
            
            if len(explainer_universe) == 0:
                print("ERROR: No valid evaluation points found for Explainer. Skipping.")
            else:
                # Run Explainer evaluation
                explainer_results = evaluate_explainer(
                    universe_df=explainer_universe,
                    ibes_df=ibes,
                    fund_df=fund,
                    news_df=news,
                    sample_size=args.explainer_sample_size,
                    verbose=True,
                )
                
                # Save results
                csv_path, json_path = save_explainer_results(
                    results_df=explainer_results,
                    output_dir=output_dir,
                )
                
                print(f"\n✓ Saved Explainer results: {csv_path}")
                print(f"✓ Saved Explainer summary: {json_path}")
                
                # Print summary
                print_explainer_summary(explainer_results)
        
        except Exception as e:
            print(f"\n⚠️  Error during Explainer evaluation: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✓ Evaluation Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

