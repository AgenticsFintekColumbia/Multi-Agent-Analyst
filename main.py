"""
main.py

Entry point for the agentic recommendation explainer system using Google Gemini.
"""

import pandas as pd
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

from data_loader import load_datasets, build_context_for_rec
from crew_config import create_explainer_crew


def main():
    """
    Main function that orchestrates the workflow.
    """
    
       #Load environment variables (like API keys) from .env file
    load_dotenv()

    #Check if API key is set (support both GEMINI_API_KEY and GOOGLE_API_KEY)
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("=" * 70)
        print("ERROR: Gemini API key not found!")
        print("=" * 70)
        print("\nPlease create a .env file with your Gemini API key, e.g.:")
        print("GEMINI_API_KEY=your_key_here")
        print("  (Optionally, you can also set GOOGLE_API_KEY=your_key_here)")
        print("\nGet your key at: https://aistudio.google.com/app/apikey")
        sys.exit(1)
    
    print("=" * 70)
    print("AGENTIC RECOMMENDATION EXPLAINER (using Google Gemini)")
    print("=" * 70)
    print()
    
    #Step 1: Load all datasets
    print("Step 1: Loading datasets...")
    ibes, fund, news = load_datasets(data_dir="data/")
    print()
    
    #Step 2: Build context for a recommendation
    print("Step 2: Building context for first recommendation...")
    rec_index = 0  #Change this to explore different recommendations
    
    context_str, rec_row = build_context_for_rec(
        ibes=ibes,
        fund=fund,
        news=news,
        rec_index=rec_index,
        fund_window_days=30,
        news_window_days=7,
    )
    
    print()
    print("=" * 70)
    print("SELECTED RECOMMENDATION")
    print("=" * 70)
    print(f"Ticker: {rec_row.get('ticker', 'N/A')}")
    print(f"Company: {rec_row.get('cname', 'N/A')}")
    print(f"Date: {rec_row['anndats'].date() if pd.notna(rec_row['anndats']) else 'N/A'}")
    print(f"Recommendation: {rec_row.get('etext', 'N/A')}")
    print("=" * 70)
    print()
    
    #Step 3: Run the Explainer agent
    print("Step 3: Running Explainer Agent with Gemini...")
    print("(This will take 10-30 seconds as the AI analyzes the data...)")
    print()
    
    try:
        #Create and run the crew
        crew = create_explainer_crew(context_str)
        result = crew.kickoff()
        
        #Print the result
        print()
        print("=" * 70)
        print("EXPLAINER AGENT OUTPUT")
        print("=" * 70)
        print()
        print(result)
        print()
        print("=" * 70)
        print("✓ Analysis complete!")
        print("=" * 70)
        
    except Exception as e:
        print()
        print("=" * 70)
        print("ERROR running Explainer agent:")
        print("=" * 70)
        print(f"\n{type(e).__name__}: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()