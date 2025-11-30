# Evaluation Framework

A comprehensive evaluation framework for assessing the performance of the Recommender mode in a realistic hedge fund research environment.

## Overview

This framework provides:

- **No Look-Ahead Protection**: All evaluation respects temporal constraints - only data available as of each decision date is used
- **Realistic Backtesting**: Portfolio construction with transaction costs, turnover constraints, and next-day execution
- **Statistical Rigor**: Information Coefficient (IC) with Newey-West adjusted t-statistics
- **Comprehensive Analysis**: Decay analysis, consensus vs contrarian, cross-sectional breakdowns

## Quick Start

### Basic Usage

```bash
# Run full evaluation with default settings
python -m evaluation.run_evaluation

# Specify date range and sample size
python -m evaluation.run_evaluation \
    --start-date 2010-01-01 \
    --end-date 2020-12-31 \
    --max-samples 100 \
    --horizon 21

# Skip signal generation (use existing signals)
python -m evaluation.run_evaluation --skip-signals

# Run Explainer evaluation (explanation quality)
python -m evaluation.run_evaluation --run-explainer --explainer-sample-size 5

# Run both Recommender and Explainer evaluations
python -m evaluation.run_evaluation --max-samples 50 --run-explainer --explainer-sample-size 5
```

### Command-Line Arguments

- `--start-date YYYY-MM-DD`: Start of evaluation period (default: 2008-01-01)
- `--end-date YYYY-MM-DD`: End of evaluation period (default: 2024-12-31)
- `--horizon N`: Primary forward return horizon in days (default: 21)
- `--max-samples N`: Maximum number of (ticker, date) samples to evaluate
- `--skip-signals`: Skip AI signal generation (use existing signals in universe)
- `--run-explainer`: Run Explainer evaluation (evaluates explanation quality)
- `--explainer-sample-size N`: Number of cases to evaluate for Explainer (default: 5)
- `--output-dir PATH`: Output directory for results (default: `evaluation/outputs/`)
- `--data-dir PATH`: Data directory (default: `data/`)

## Output Files

Results are saved to the output directory (default: `evaluation/outputs/`):

- `universe_with_signals.csv`: Full evaluation universe with AI signals (also serves as cache - see below)
- `ic_series.csv`: Time series of Information Coefficients
- `decay_analysis.csv`: IC statistics across multiple horizons
- `portfolio_backtest.csv`: Portfolio returns and turnover over time
- `summary.json`: Summary statistics in JSON format
- `explainer_results.csv`: Explainer evaluation results (if `--run-explainer` used)
- `explainer_summary.json`: Explainer evaluation summary (if `--run-explainer` used)

## Signal Caching

The framework automatically caches AI signals to avoid redundant API calls:

- **Cache File**: `evaluation/outputs/universe_with_signals.csv` serves as a persistent cache
- **Automatic Reuse**: On each run, the framework:
  1. Loads existing cache (if present)
  2. Merges cached signals with the current evaluation universe
  3. Only calls the Recommender for (ticker, as_of_date) pairs that aren't in the cache
  4. Saves the updated cache (merged with new signals) back to the file

**Benefits**:
- Re-running with the same date range and `--max-samples` reuses previously computed signals
- No API calls for cached (ticker, date) pairs
- Cache grows incrementally - each run adds new signals without losing old ones
- Saves time and API quota

**Example**:
```bash
# First run: generates signals for 100 points
python -m evaluation.run_evaluation --max-samples 100

# Second run with same params: reuses all 100 signals, no API calls
python -m evaluation.run_evaluation --max-samples 100

# Third run with larger sample: reuses 100, generates 50 new
python -m evaluation.run_evaluation --max-samples 150
```

The cache is keyed on `(ticker, as_of_date)`, so signals are reused across different runs as long as those pairs match.

## Module Structure

### `config.py`
Default parameters: horizons, transaction costs, portfolio constraints, date ranges.

### `data.py`
- `load_datasets()`: Load and normalize IBES, FUND, NEWS data
- `build_evaluation_universe()`: Build evaluation universe with forward returns
- `compute_forward_returns()`: Compute forward returns with no look-ahead
- `stratified_sample()`: Downsample with balanced representation

### `signal.py`
- `call_recommender_safe()`: Call Recommender with no look-ahead
- `parse_rating_and_confidence()`: Extract rating/confidence from output
- `compute_signal()`: Convert to numeric signal (base_score × confidence)
- `generate_signals_for_universe()`: Batch signal generation

### `backtest.py`
- `compute_ic_series()`: Time series of cross-sectional ICs
- `compute_ic_statistics()`: IC stats with Newey-West adjustment
- `compute_decay_analysis()`: IC across multiple horizons
- `run_portfolio_backtest()`: Full backtest with transaction costs
- `compute_performance_metrics()`: CAGR, Sharpe, drawdown, etc.

### `analysis.py`
- `analyze_consensus_contrarian()`: AI vs human rating analysis
- `analyze_by_year()`: IC breakdown by calendar year
- `analyze_by_regime()`: IC by time period (pre-2015, 2015-2019, etc.)
- `separate_holdout_period()`: Split backtest vs holdout periods

### `explainer_evaluation.py`
- `run_explainer()`: Call Explainer team for a (ticker, date, rating)
- `evaluate_explainer()`: Evaluate Explainer on a sample of cases
- `compute_faithfulness()`: Check if explanation matches actual data
- `compute_sentiment_alignment()`: Check if explanation tone matches rating
- `compute_coverage()`: Check if explanation mentions available data sources

## Key Design Principles

### No Look-Ahead

All data filtering respects temporal constraints:
- FUND data: `date <= as_of_date`
- NEWS data: `announcedate <= as_of_date`
- Forward returns: computed from next trading day after `as_of_date`

### Realistic Execution

- Decisions made at close of `as_of_date`
- Execution at next day's open (1-day delay)
- Forward returns measured from execution date

### Transaction Costs

- Turnover-based costs: `cost = turnover × cost_per_side × 2`
- Default: 10 bps per side (20 bps round-trip)
- Costs subtracted from gross returns

### Signal Construction

- Base score: -2 (Sell) to +2 (StrongBuy)
- Confidence: 0 (Low) to 1 (High)
- Signal: `base_score × confidence`

This ensures low-confidence StrongBuy ranks below high-confidence Buy.

## Example Workflow

```python
from evaluation.data import load_datasets, build_evaluation_universe
from evaluation.signal import generate_signals_for_universe
from evaluation.backtest import compute_ic_statistics, compute_ic_series

# Load data
ibes, fund, news = load_datasets()

# Build universe
universe = build_evaluation_universe(ibes, fund, start_date=..., end_date=...)

# Generate signals
universe = generate_signals_for_universe(universe, fund, news, max_samples=100)

# Compute IC
ic_series = compute_ic_series(universe, signal_col="ai_signal")
ic_stats = compute_ic_statistics(ic_series)

print(f"Mean IC: {ic_stats['mean_ic']:.4f}")
print(f"t-stat: {ic_stats['t_stat']:.2f}")
```

## Explainer Evaluation

The framework includes a lightweight evaluation module for the Explainer team that assesses explanation quality using three metrics:

### Metrics

1. **Faithfulness**: Checks if explanations match actual data
   - Price trend consistency (uptrend/downtrend mentions vs actual returns)
   - News sentiment consistency (positive/negative mentions vs actual sentiment)
   - Fundamentals consistency (strong/weak mentions vs actual metrics)

2. **Rating-Explanation Consistency**: Checks if explanation tone matches the human rating
   - Computes sentiment score from positive/negative word counts
   - Verifies alignment: Buy ratings should have positive sentiment, Sell ratings negative, Hold neutral

3. **Coverage/Completeness**: Checks if explanation mentions available data sources
   - Fundamentals: keywords like "earnings", "revenue", "margin"
   - Technicals: keywords like "price", "trend", "momentum", "RSI"
   - News: keywords like "news", "headline", "catalyst"

### Usage

```bash
# Run Explainer evaluation only
python -m evaluation.run_evaluation --run-explainer --explainer-sample-size 5

# Run both Recommender and Explainer
python -m evaluation.run_evaluation --max-samples 50 --run-explainer --explainer-sample-size 5
```

The Explainer evaluation:
- Samples cases from the evaluation universe (stratified by rating when possible)
- Runs the Explainer team on each case
- Computes all three metrics
- Saves results to `explainer_results.csv` and `explainer_summary.json`
- Prints a brief summary

## Notes

- **LLM Training Horizon**: The framework treats 2023+ as a holdout period, acknowledging that the LLM may have been trained on data up to ~2023
- **Price vs Total Returns**: Currently uses price returns (not total returns including dividends). This is explicit in the code comments.
- **Execution Speed**: Signal generation is slow (~60-90 seconds per evaluation point) due to LLM inference. Use `--max-samples` for faster iteration.
- **Explainer Evaluation**: Each explanation takes ~60-90 seconds. Use `--explainer-sample-size` to control evaluation time.

