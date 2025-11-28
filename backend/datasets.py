"""
Dataset management module - handles loading and caching datasets.
This module is imported by both main.py and API routes to avoid circular imports.
"""

from data_loader import load_datasets

# Global cache for datasets
_datasets_cache = None


def initialize_datasets(data_dir: str = "data/"):
    """Load datasets and cache them."""
    global _datasets_cache
    print("=" * 60)
    print("Loading datasets at startup...")
    try:
        _datasets_cache = load_datasets(data_dir=data_dir)
        print("✓ Datasets loaded successfully")
    except Exception as e:
        print(f"⚠ Error loading datasets: {e}")
        _datasets_cache = None
    print("=" * 60)


def get_datasets():
    """Get cached datasets."""
    if _datasets_cache is None:
        raise Exception("Datasets not loaded. Call initialize_datasets() first.")
    return _datasets_cache


def clear_datasets():
    """Clear the dataset cache."""
    global _datasets_cache
    _datasets_cache = None

