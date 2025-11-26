"""
test_multi_recommender.py

Simple test script to verify the multi-agent Recommender team with Manager works.
"""

import os
import sys
from dotenv import load_dotenv

from data_loader import load_datasets
from src.recommender import run_multi_analyst_recommendation


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
    print("TESTING MULTI-AGENT RECOMMENDER WITH MANAGER")
    print("=" * 70)
    print()
    
    # Load datasets
    print("Loading datasets...")
    ibes, fund, news = load_datasets(data_dir="data/")
    print()
    
    # Test with first recommendation
    rec_index = 0
    rec = ibes.iloc[rec_index]
    
    cusip = rec.get("cusip")
    rec_date = rec.get("anndats")
    ticker = rec.get("ticker", "N/A")
    company = rec.get("cname", "N/A")
    
    print("=" * 70)
    print("TESTING WITH RECOMMENDATION:")
    print("=" * 70)
    print(f"Ticker: {ticker}")
    print(f"Company: {company}")
    print(f"CUSIP: {cusip}")
    print(f"Date: {rec_date.date() if rec_date is not None else 'N/A'}")
    print(f"Human Analyst Rating: {rec.get('etext', 'N/A')}")
    print("=" * 70)
    print()
    
    # Run the multi-agent recommender with manager
    print("Running multi-agent Recommender team with Portfolio Manager...")
    print("(This will take 60-90 seconds as 4 agents run sequentially...)")
    print()
    
    try:
        recommendation = run_multi_analyst_recommendation(
            cusip=cusip,
            rec_date=rec_date,
            fund_df=fund,
            news_df=news,
            news_window_days=30,
            ticker=ticker,
            company=company,
        )
        
        print()
        print("=" * 70)
        print("FINAL RECOMMENDATION OUTPUT")
        print("=" * 70)
        print()
        print(recommendation)
        print()
        print("=" * 70)
        print("✓ Test complete!")
        print("=" * 70)
        
    except Exception as e:
        print()
        print("=" * 70)
        print("ERROR during multi-agent Recommender test:")
        print("=" * 70)
        print(f"\n{type(e).__name__}: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()