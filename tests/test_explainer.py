"""
test_multi_explainer.py

Simple test script to verify the multi-agent Explainer team works.
Run this before integrating into the GUI.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_loader import load_datasets
from src.explainer import run_multi_analyst_explainer


def main():
    # Load environment variables
    load_dotenv()
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("=" * 70)
        print("ERROR: Gemini API key not found!")
        print("=" * 70)
        print("\nPlease create a .env file with your Gemini API key.")
        sys.exit(1)
    
    print("=" * 70)
    print("TESTING MULTI-AGENT EXPLAINER")
    print("=" * 70)
    print()
    
    # Load datasets
    print("Loading datasets...")
    ibes, fund, news = load_datasets(data_dir="data/")
    print()
    
    # Test with first recommendation
    rec_index = 0
    rec = ibes.iloc[rec_index]
    
    print("=" * 70)
    print("TESTING WITH RECOMMENDATION:")
    print("=" * 70)
    print(f"Ticker: {rec.get('ticker', 'N/A')}")
    print(f"Company: {rec.get('cname', 'N/A')}")
    print(f"Date: {rec['anndats'].date() if rec['anndats'] is not None else 'N/A'}")
    print(f"Rating: {rec.get('etext', 'N/A')}")
    print("=" * 70)
    print()
    
    # Run the multi-agent explainer
    print("Running multi-agent Explainer team...")
    print("(This will take 30-60 seconds as multiple agents run...)")
    print()
    
    try:
        explanation = run_multi_analyst_explainer(
            ibes_df=ibes,
            fund_df=fund,
            news_df=news,
            rec_index=rec_index,
            fund_window_days=30,
            news_window_days=7,
        )
        
        print()
        print("=" * 70)
        print("FINAL EXPLANATION OUTPUT")
        print("=" * 70)
        print()
        print(explanation)
        print()
        print("=" * 70)
        print("✓ Test complete!")
        print("=" * 70)
        
    except Exception as e:
        print()
        print("=" * 70)
        print("ERROR during multi-agent Explainer test:")
        print("=" * 70)
        print(f"\n{type(e).__name__}: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()