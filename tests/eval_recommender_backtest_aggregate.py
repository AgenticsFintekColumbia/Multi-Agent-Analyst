"""
Evaluation script for Recommender mode - Backtest Aggregation

This script:
1. Reads backtest trades CSV
2. Computes summary metrics (directional accuracy, P&L, etc.)
3. Prints summary and optionally writes markdown report
"""

import argparse
import csv
import pandas as pd
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate backtest results for Recommender evaluation"
    )
    parser.add_argument(
        "--input_path",
        type=str,
        default="evaluation/recommender_backtest_trades.csv",
        help="Input CSV path (default: evaluation/recommender_backtest_trades.csv)",
    )
    parser.add_argument(
        "--output_md",
        type=str,
        default=None,
        help="Optional: Path to write markdown report (default: same dir as input, with .md extension)",
    )
    
    args = parser.parse_args()
    
    # Load CSV
    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        return
    
    print("=" * 70)
    print("RECOMMENDER BACKTEST: Aggregating Results")
    print("=" * 70)
    print()
    
    print(f"Loading trades from: {input_path}")
    # Try multiple encodings
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    df = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(input_path, encoding=encoding)
            if encoding != 'utf-8-sig':
                print(f"Note: Read file with {encoding} encoding")
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            try:
                df = pd.read_csv(input_path, encoding=encoding, engine='python', on_bad_lines='skip')
                print(f"Note: Read file with {encoding} encoding (lenient mode)")
                break
            except Exception:
                continue
    
    if df is None:
        print("ERROR: Could not read CSV file")
        return
    
    print(f"✓ Loaded {len(df)} trades")
    print()
    
    # Filter to trades with valid returns
    df_1m = df[df["return_1m"].notna()].copy()
    df_3m = df[df["return_3m"].notna()].copy()
    
    print(f"Trades with 1M returns: {len(df_1m)}")
    print(f"Trades with 3M returns: {len(df_3m)}")
    print()
    
    # Compute metrics for 1M horizon
    print("=" * 70)
    print("1-MONTH HORIZON")
    print("=" * 70)
    print()
    
    if len(df_1m) > 0:
        # Directional accuracy (only for non-zero signals)
        model_nonzero_1m = df_1m[df_1m["model_signal"] != 0]
        human_nonzero_1m = df_1m[df_1m["human_signal"] != 0]
        baseline_nonzero_1m = df_1m[df_1m["baseline_signal"] != 0]  # Always 1, so all are nonzero
        
        model_dir_acc_1m = (model_nonzero_1m["model_dir_correct_1m"].sum() / len(model_nonzero_1m) * 100) if len(model_nonzero_1m) > 0 else 0
        human_dir_acc_1m = (human_nonzero_1m["human_dir_correct_1m"].sum() / len(human_nonzero_1m) * 100) if len(human_nonzero_1m) > 0 else 0
        baseline_dir_acc_1m = (baseline_nonzero_1m["baseline_signal"] * df_1m["return_1m"] > 0).sum() / len(baseline_nonzero_1m) * 100 if len(baseline_nonzero_1m) > 0 else 0
        
        # Average P&L per trade
        model_avg_pnl_1m = df_1m["model_pnl_1m"].mean() * 100
        human_avg_pnl_1m = df_1m["human_pnl_1m"].mean() * 100
        baseline_avg_pnl_1m = df_1m["baseline_pnl_1m"].mean() * 100
        
        # Cumulative P&L (sum)
        model_cum_pnl_1m = df_1m["model_pnl_1m"].sum() * 100
        human_cum_pnl_1m = df_1m["human_pnl_1m"].sum() * 100
        baseline_cum_pnl_1m = df_1m["baseline_pnl_1m"].sum() * 100
        
        print(f"Directional Accuracy (non-Hold trades only):")
        print(f"  Model:   {model_dir_acc_1m:.1f}% (N={len(model_nonzero_1m)})")
        print(f"  Human:   {human_dir_acc_1m:.1f}% (N={len(human_nonzero_1m)})")
        print(f"  Baseline: {baseline_dir_acc_1m:.1f}% (N={len(baseline_nonzero_1m)})")
        print()
        print(f"Average P&L per trade:")
        print(f"  Model:   {model_avg_pnl_1m:+.2f}%")
        print(f"  Human:   {human_avg_pnl_1m:+.2f}%")
        print(f"  Baseline: {baseline_avg_pnl_1m:+.2f}%")
        print()
        print(f"Cumulative P&L:")
        print(f"  Model:   {model_cum_pnl_1m:+.2f}%")
        print(f"  Human:   {human_cum_pnl_1m:+.2f}%")
        print(f"  Baseline: {baseline_cum_pnl_1m:+.2f}%")
        print()
        
        # Model vs Human comparison
        model_correct_human_wrong = ((df_1m["model_dir_correct_1m"] == 1) & (df_1m["human_dir_correct_1m"] == 0) & (df_1m["model_signal"] != 0) & (df_1m["human_signal"] != 0)).sum()
        human_correct_model_wrong = ((df_1m["human_dir_correct_1m"] == 1) & (df_1m["model_dir_correct_1m"] == 0) & (df_1m["model_signal"] != 0) & (df_1m["human_signal"] != 0)).sum()
        
        print(f"Model vs Human (1M):")
        print(f"  Model correct, Human wrong: {model_correct_human_wrong}")
        print(f"  Human correct, Model wrong: {human_correct_model_wrong}")
        print()
    else:
        print("No valid 1M returns available")
        print()
    
    # Compute metrics for 3M horizon
    print("=" * 70)
    print("3-MONTH HORIZON")
    print("=" * 70)
    print()
    
    if len(df_3m) > 0:
        # Directional accuracy
        model_nonzero_3m = df_3m[df_3m["model_signal"] != 0]
        human_nonzero_3m = df_3m[df_3m["human_signal"] != 0]
        baseline_nonzero_3m = df_3m[df_3m["baseline_signal"] != 0]
        
        model_dir_acc_3m = (model_nonzero_3m["model_dir_correct_3m"].sum() / len(model_nonzero_3m) * 100) if len(model_nonzero_3m) > 0 else 0
        human_dir_acc_3m = (human_nonzero_3m["human_dir_correct_3m"].sum() / len(human_nonzero_3m) * 100) if len(human_nonzero_3m) > 0 else 0
        baseline_dir_acc_3m = (baseline_nonzero_3m["baseline_signal"] * df_3m["return_3m"] > 0).sum() / len(baseline_nonzero_3m) * 100 if len(baseline_nonzero_3m) > 0 else 0
        
        # Average P&L per trade
        model_avg_pnl_3m = df_3m["model_pnl_3m"].mean() * 100
        human_avg_pnl_3m = df_3m["human_pnl_3m"].mean() * 100
        baseline_avg_pnl_3m = df_3m["baseline_pnl_3m"].mean() * 100
        
        # Cumulative P&L
        model_cum_pnl_3m = df_3m["model_pnl_3m"].sum() * 100
        human_cum_pnl_3m = df_3m["human_pnl_3m"].sum() * 100
        baseline_cum_pnl_3m = df_3m["baseline_pnl_3m"].sum() * 100
        
        print(f"Directional Accuracy (non-Hold trades only):")
        print(f"  Model:   {model_dir_acc_3m:.1f}% (N={len(model_nonzero_3m)})")
        print(f"  Human:   {human_dir_acc_3m:.1f}% (N={len(human_nonzero_3m)})")
        print(f"  Baseline: {baseline_dir_acc_3m:.1f}% (N={len(baseline_nonzero_3m)})")
        print()
        print(f"Average P&L per trade:")
        print(f"  Model:   {model_avg_pnl_3m:+.2f}%")
        print(f"  Human:   {human_avg_pnl_3m:+.2f}%")
        print(f"  Baseline: {baseline_avg_pnl_3m:+.2f}%")
        print()
        print(f"Cumulative P&L:")
        print(f"  Model:   {model_cum_pnl_3m:+.2f}%")
        print(f"  Human:   {human_cum_pnl_3m:+.2f}%")
        print(f"  Baseline: {baseline_cum_pnl_3m:+.2f}%")
        print()
        
        # Model vs Human comparison
        model_correct_human_wrong_3m = ((df_3m["model_dir_correct_3m"] == 1) & (df_3m["human_dir_correct_3m"] == 0) & (df_3m["model_signal"] != 0) & (df_3m["human_signal"] != 0)).sum()
        human_correct_model_wrong_3m = ((df_3m["human_dir_correct_3m"] == 1) & (df_3m["model_dir_correct_3m"] == 0) & (df_3m["model_signal"] != 0) & (df_3m["human_signal"] != 0)).sum()
        
        print(f"Model vs Human (3M):")
        print(f"  Model correct, Human wrong: {model_correct_human_wrong_3m}")
        print(f"  Human correct, Model wrong: {human_correct_model_wrong_3m}")
        print()
    else:
        print("No valid 3M returns available")
        print()
    
    # Write markdown report if requested
    if args.output_md:
        output_md_path = Path(args.output_md)
    else:
        output_md_path = input_path.with_suffix(".md")
    
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_md_path, "w", encoding='utf-8') as f:
        f.write("# Recommender Backtest Results\n\n")
        f.write(f"**Evaluation Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Number of Trades:** {len(df)}\n\n")
        f.write(f"**Trades with 1M returns:** {len(df_1m)}\n\n")
        f.write(f"**Trades with 3M returns:** {len(df_3m)}\n\n")
        f.write("---\n\n")
        
        if len(df_1m) > 0:
            f.write("## 1-Month Horizon\n\n")
            f.write("### Directional Accuracy (non-Hold trades)\n\n")
            f.write("| Strategy | Accuracy | N Trades |\n")
            f.write("|----------|----------|----------|\n")
            f.write(f"| Model | {model_dir_acc_1m:.1f}% | {len(model_nonzero_1m)} |\n")
            f.write(f"| Human | {human_dir_acc_1m:.1f}% | {len(human_nonzero_1m)} |\n")
            f.write(f"| Baseline (Always Long) | {baseline_dir_acc_1m:.1f}% | {len(baseline_nonzero_1m)} |\n\n")
            
            f.write("### Average P&L per Trade\n\n")
            f.write("| Strategy | Avg P&L |\n")
            f.write("|----------|----------|\n")
            f.write(f"| Model | {model_avg_pnl_1m:+.2f}% |\n")
            f.write(f"| Human | {human_avg_pnl_1m:+.2f}% |\n")
            f.write(f"| Baseline | {baseline_avg_pnl_1m:+.2f}% |\n\n")
            
            f.write("### Cumulative P&L\n\n")
            f.write("| Strategy | Cumulative P&L |\n")
            f.write("|----------|-----------------|\n")
            f.write(f"| Model | {model_cum_pnl_1m:+.2f}% |\n")
            f.write(f"| Human | {human_cum_pnl_1m:+.2f}% |\n")
            f.write(f"| Baseline | {baseline_cum_pnl_1m:+.2f}% |\n\n")
            
            f.write("### Model vs Human Comparison\n\n")
            f.write(f"- **Model correct, Human wrong:** {model_correct_human_wrong}\n")
            f.write(f"- **Human correct, Model wrong:** {human_correct_model_wrong}\n\n")
        
        if len(df_3m) > 0:
            f.write("## 3-Month Horizon\n\n")
            f.write("### Directional Accuracy (non-Hold trades)\n\n")
            f.write("| Strategy | Accuracy | N Trades |\n")
            f.write("|----------|----------|----------|\n")
            f.write(f"| Model | {model_dir_acc_3m:.1f}% | {len(model_nonzero_3m)} |\n")
            f.write(f"| Human | {human_dir_acc_3m:.1f}% | {len(human_nonzero_3m)} |\n")
            f.write(f"| Baseline (Always Long) | {baseline_dir_acc_3m:.1f}% | {len(baseline_nonzero_3m)} |\n\n")
            
            f.write("### Average P&L per Trade\n\n")
            f.write("| Strategy | Avg P&L |\n")
            f.write("|----------|----------|\n")
            f.write(f"| Model | {model_avg_pnl_3m:+.2f}% |\n")
            f.write(f"| Human | {human_avg_pnl_3m:+.2f}% |\n")
            f.write(f"| Baseline | {baseline_avg_pnl_3m:+.2f}% |\n\n")
            
            f.write("### Cumulative P&L\n\n")
            f.write("| Strategy | Cumulative P&L |\n")
            f.write("|----------|-----------------|\n")
            f.write(f"| Model | {model_cum_pnl_3m:+.2f}% |\n")
            f.write(f"| Human | {human_cum_pnl_3m:+.2f}% |\n")
            f.write(f"| Baseline | {baseline_cum_pnl_3m:+.2f}% |\n\n")
            
            f.write("### Model vs Human Comparison\n\n")
            f.write(f"- **Model correct, Human wrong:** {model_correct_human_wrong_3m}\n")
            f.write(f"- **Human correct, Model wrong:** {human_correct_model_wrong_3m}\n\n")
        
        f.write("---\n\n")
        f.write("## Trading Rules\n\n")
        f.write("### Signal Mapping\n\n")
        f.write("- **StrongBuy / Buy** → +1 (go long)\n")
        f.write("- **Sell / UnderPerform** → -1 (go short)\n")
        f.write("- **Hold** → 0 (no position)\n\n")
        f.write("### P&L Calculation\n\n")
        f.write("- P&L = signal × future_return\n")
        f.write("- Baseline strategy: always long (+1) for all dates\n\n")
        f.write("### Return Calculation\n\n")
        f.write("- 1M return: price at (rec_date + 21 trading days) / price at rec_date - 1\n")
        f.write("- 3M return: price at (rec_date + 63 trading days) / price at rec_date - 1\n")
    
    print(f"✓ Markdown report written to: {output_md_path}")
    print()
    print("=" * 70)
    print("✓ Aggregation Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

