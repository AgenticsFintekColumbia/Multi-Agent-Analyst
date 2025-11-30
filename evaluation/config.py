"""
Configuration module for evaluation framework.

Defines default parameters for evaluation runs, including:
- Forward return horizons
- Portfolio construction parameters
- Transaction cost assumptions
- Date ranges
- Data paths
"""

from pathlib import Path
from datetime import datetime
from typing import List

# Default data directory
DEFAULT_DATA_DIR = Path("data/")

# Default forward return horizons (in calendar days)
DEFAULT_HORIZONS: List[int] = [5, 10, 21, 63]

# Primary horizon for main analysis (typically 21 days = ~1 month)
PRIMARY_HORIZON: int = 21

# Portfolio construction parameters
DEFAULT_QUANTILE_SIZE: float = 0.2  # Top/bottom 20% for long/short
DEFAULT_MAX_POSITION_WEIGHT: float = 0.10  # Max 10% per name (diversification constraint)

# Transaction costs (in basis points per side)
# Typical institutional costs: 5-20 bps per side
DEFAULT_COST_PER_SIDE_BPS: float = 10.0  # 10 bps = 0.1%

# Execution assumptions
# Decisions made at close of as_of_date, executed at next day's open
# Forward returns measured from execution date (next day) to target date
EXECUTION_DELAY_DAYS: int = 1

# Default evaluation date range
DEFAULT_START_DATE: datetime = datetime(2008, 1, 1)
DEFAULT_END_DATE: datetime = datetime(2024, 12, 31)

# Holdout period (post-training window for LLM)
# Assume LLM trained on data up to ~2023
HOLDOUT_START_DATE: datetime = datetime(2023, 1, 1)

# Stratified sampling defaults
DEFAULT_MAX_SAMPLES: int = None  # None = use all available
DEFAULT_STRATIFY_BY: List[str] = ["year", "ticker"]  # Stratify across years and tickers

# IBES rating mapping to numeric scores
# Symmetric scale: -2 to +2
RATING_TO_SCORE = {
    "StrongBuy": 2.0,
    "Buy": 1.0,
    "Hold": 0.0,
    "UnderPerform": -1.0,
    "Sell": -2.0,
    # Handle variations
    "STRONG BUY": 2.0,
    "STRONGBUY": 2.0,
    "STRONG BUY": 2.0,
    "BUY": 1.0,
    "HOLD": 0.0,
    "UNDERPERFORM": -1.0,
    "UNDER PERFORM": -1.0,
    "SELL": -2.0,
}

# Confidence mapping to numeric [0, 1]
CONFIDENCE_TO_VALUE = {
    "High": 1.0,
    "Medium": 0.6,
    "Low": 0.3,
    "HIGH": 1.0,
    "MEDIUM": 0.6,
    "LOW": 0.3,
}

# Newey-West adjustment parameters
DEFAULT_NW_LAGS: int = 5  # Number of lags for autocorrelation adjustment

# Output paths
DEFAULT_OUTPUT_DIR = Path("evaluation/outputs/")

