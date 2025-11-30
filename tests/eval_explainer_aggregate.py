"""
Evaluation script for Explainer mode - Aggregation

This script:
1. Reads a CSV with human ratings
2. Computes summary metrics (mean scores, modality alignment)
3. Prints summary and optionally writes markdown report
"""

import argparse
import csv
import pandas as pd
from pathlib import Path


def compute_modality_alignment(row: pd.Series) -> dict:
    """
    Compute modality alignment metrics for a single row.
    
    Returns dict with:
    - fund_aligned: True if fundamentals available AND mentions_fundamental == "yes"
    - tech_aligned: True if technicals available AND mentions_technical == "yes"
    - news_aligned: True if news available AND mentions_news == "yes"
    - missing_data_acknowledged: True if any modality missing AND calls_out_missing_data == "yes"
    """
    # Check if data was available
    fund_available = row.get("fund_non_null_ratio", 0) > 0.1  # At least 10% coverage
    tech_available = row.get("tech_non_null_ratio", 0) > 0.1
    news_available = row.get("news_count", 0) > 0
    
    # Check if explanation mentioned it
    mentions_fund = str(row.get("mentions_fundamental", "")).lower().strip() == "yes"
    mentions_tech = str(row.get("mentions_technical", "")).lower().strip() == "yes"
    mentions_news_val = str(row.get("mentions_news", "")).lower().strip() == "yes"
    calls_out_missing = str(row.get("calls_out_missing_data", "")).lower().strip() == "yes"
    
    # Alignment: available AND mentioned
    fund_aligned = fund_available and mentions_fund
    tech_aligned = tech_available and mentions_tech
    news_aligned = news_available and mentions_news_val
    
    # Missing data: at least one modality missing AND acknowledged
    any_missing = not fund_available or not tech_available or not news_available
    missing_data_acknowledged = any_missing and calls_out_missing
    
    return {
        "fund_aligned": fund_aligned,
        "tech_aligned": tech_aligned,
        "news_aligned": news_aligned,
        "missing_data_acknowledged": missing_data_acknowledged,
        "fund_available": fund_available,
        "tech_available": tech_available,
        "news_available": news_available,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate human ratings for Explainer evaluation"
    )
    parser.add_argument(
        "--input_path",
        type=str,
        required=True,
        help="Path to CSV with human ratings",
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
    print("EXPLAINER EVALUATION: Aggregating Human Ratings")
    print("=" * 70)
    print()
    
    print(f"Loading ratings from: {input_path}")
    # Try multiple encodings and parsing strategies to handle special characters
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    df = None
    last_error = None
    
    for encoding in encodings:
        # Strategy 1: Try standard parsing (works for properly quoted CSV)
        try:
            df = pd.read_csv(input_path, encoding=encoding)
            if encoding != 'utf-8-sig':
                print(f"Note: Read file with {encoding} encoding")
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            last_error = e
            # Strategy 2: Try with Python engine (more lenient, handles malformed lines)
            try:
                df = pd.read_csv(
                    input_path,
                    encoding=encoding,
                    on_bad_lines='skip',
                    engine='python'
                )
                print(f"Note: Read file with {encoding} encoding (lenient mode)")
                break
            except Exception as e2:
                last_error = e2
                # Strategy 3: Try with error handling for bad lines
                try:
                    df = pd.read_csv(
                        input_path,
                        encoding=encoding,
                        on_bad_lines='warn',  # Warn but continue
                        engine='python',
                        sep=',',
                        quotechar='"',
                        skipinitialspace=True
                    )
                    print(f"Note: Read file with {encoding} encoding (warn on bad lines)")
                    break
                except Exception:
                    continue
    
    if df is None:
        print("ERROR: Could not read CSV file with any supported encoding or parsing method")
        if last_error:
            print(f"Last error: {last_error}")
        print("\nThe file may have formatting issues. Suggestions:")
        print("1. Check if the CSV has consistent column counts")
        print("2. Ensure markdown fields are properly quoted")
        print("3. Try regenerating the CSV with the updated sampling script")
        return
    
    print(f"✓ Loaded {len(df)} samples")
    print()
    
    # Filter to rows with ratings (non-empty plausibility)
    rated_df = df[df["plausibility_1_5"].notna() & (df["plausibility_1_5"] != "")].copy()
    
    if len(rated_df) == 0:
        print("ERROR: No rated samples found. Please ensure plausibility_1_5 column is filled.")
        return
    
    print(f"Found {len(rated_df)} rated samples (out of {len(df)} total)")
    print()
    
    # Convert rating columns to numeric
    for col in ["plausibility_1_5", "signal_coverage_1_5", "internal_consistency_1_5"]:
        rated_df[col] = pd.to_numeric(rated_df[col], errors="coerce")
    
    # Compute mean scores
    mean_plausibility = rated_df["plausibility_1_5"].mean()
    mean_signal_coverage = rated_df["signal_coverage_1_5"].mean()
    mean_internal_consistency = rated_df["internal_consistency_1_5"].mean()
    
    # Compute modality alignment
    alignment_results = []
    for _, row in rated_df.iterrows():
        alignment = compute_modality_alignment(row)
        alignment_results.append(alignment)
    
    alignment_df = pd.DataFrame(alignment_results)
    
    # Compute percentages
    fund_aligned_pct = (alignment_df["fund_aligned"].sum() / alignment_df["fund_available"].sum() * 100) if alignment_df["fund_available"].sum() > 0 else 0
    tech_aligned_pct = (alignment_df["tech_aligned"].sum() / alignment_df["tech_available"].sum() * 100) if alignment_df["tech_available"].sum() > 0 else 0
    news_aligned_pct = (alignment_df["news_aligned"].sum() / alignment_df["news_available"].sum() * 100) if alignment_df["news_available"].sum() > 0 else 0
    
    any_missing_mask = ~alignment_df["fund_available"] | ~alignment_df["tech_available"] | ~alignment_df["news_available"]
    missing_acknowledged_pct = (alignment_df.loc[any_missing_mask, "missing_data_acknowledged"].sum() / any_missing_mask.sum() * 100) if any_missing_mask.sum() > 0 else 0
    
    # Average data completeness
    avg_completeness = rated_df["data_completeness_score"].mean()
    
    # Print summary
    print("=" * 70)
    print(f"Explainer Human-Study Evaluation (N = {len(rated_df)} samples)")
    print("=" * 70)
    print()
    print("Mean Scores:")
    print(f"  Mean Plausibility:          {mean_plausibility:.1f} / 5")
    print(f"  Mean Signal Coverage:        {mean_signal_coverage:.1f} / 5")
    print(f"  Mean Internal Consistency:   {mean_internal_consistency:.1f} / 5")
    print()
    print("Modality Alignment:")
    print(f"  Mentions fundamentals when available: {fund_aligned_pct:.0f}%")
    print(f"  Mentions technicals when available:   {tech_aligned_pct:.0f}%")
    print(f"  Mentions news when available:          {news_aligned_pct:.0f}%")
    print(f"  Explicitly calls out missing data:    {missing_acknowledged_pct:.0f}%")
    print()
    print(f"Average data completeness score (on sampled set): {avg_completeness:.2f} / 3.0")
    print()
    
    # Write markdown report if requested
    if args.output_md:
        output_md_path = Path(args.output_md)
    else:
        output_md_path = input_path.with_suffix(".md")
    
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_md_path, "w") as f:
        f.write("# Explainer Human-Study Evaluation Results\n\n")
        f.write(f"**Evaluation Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Number of Samples:** {len(rated_df)}\n\n")
        f.write("---\n\n")
        
        f.write("## Mean Scores\n\n")
        f.write(f"- **Plausibility:** {mean_plausibility:.2f} / 5.0\n")
        f.write(f"- **Signal Coverage:** {mean_signal_coverage:.2f} / 5.0\n")
        f.write(f"- **Internal Consistency:** {mean_internal_consistency:.2f} / 5.0\n\n")
        
        f.write("## Modality Alignment\n\n")
        f.write(f"- **Mentions fundamentals when available:** {fund_aligned_pct:.0f}%\n")
        f.write(f"- **Mentions technicals when available:** {tech_aligned_pct:.0f}%\n")
        f.write(f"- **Mentions news when available:** {news_aligned_pct:.0f}%\n")
        f.write(f"- **Explicitly calls out missing data:** {missing_acknowledged_pct:.0f}%\n\n")
        
        f.write("## Data Quality\n\n")
        f.write(f"- **Average data completeness score:** {avg_completeness:.2f} / 3.0\n\n")
        
        f.write("---\n\n")
        f.write("## Rating Guidelines\n\n")
        f.write("### Plausibility (1-5)\n")
        f.write('"Does this explanation feel like something a real sell-side analyst could plausibly have written as the reasoning behind the rating?"\n')
        f.write("- 1 = not at all\n")
        f.write("- 5 = extremely plausible\n\n")
        
        f.write("### Signal Coverage (1-5)\n")
        f.write('"Given the data shown to each agent (fundamental, technical, news), does the final explanation actually reference the most important signals?"\n')
        f.write("- 1 = major signals missing / made up\n")
        f.write("- 5 = covers key signals correctly\n\n")
        
        f.write("### Internal Consistency (1-5)\n")
        f.write('"Does the explainer\'s conclusion (e.g. why they rated SELL) follow logically from the signals it described?"\n')
        f.write("- 1 = contradicts itself\n")
        f.write("- 5 = strongly consistent\n\n")
        
        f.write("### Modality Checklist\n\n")
        f.write("- **mentions_fundamental:** If fundamental data exists, did the explanation talk about it? (yes/no/na)\n")
        f.write("- **mentions_technical:** If technical data exists, did the explanation talk about it? (yes/no/na)\n")
        f.write("- **mentions_news:** If news exists, did the explanation talk about it? (yes/no/na)\n")
        f.write("- **calls_out_missing_data:** If a modality is missing, does the explanation acknowledge that instead of hallucinating numbers? (yes/no/na)\n")
    
    print(f"✓ Markdown report written to: {output_md_path}")
    print()
    print("=" * 70)
    print("✓ Aggregation Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

