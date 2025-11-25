"""
data_loader.py

This  loads IBES, FUND, and NEWS data from .feather files,
and builds human-readable context strings for analyst recommendations.

"""

import pandas as pd
from pathlib import Path
from datetime import timedelta


def load_datasets(data_dir: str = "data/"):
    """
    Load the three main datasets from .feather files.
    
    What this does:
    1. Reads binary .feather files into pandas DataFrames
    2. Converts date columns from text to proper date objects
    3. Returns all three datasets for use in other functions
    
    Args:
        data_dir: Path to the folder containing .feather files
        
    Returns:
        tuple: (ibes_df, fund_df, news_df) - three pandas DataFrames
    """
    data_path = Path(data_dir)
    
    print("Loading IBES data...")
    ibes = pd.read_feather(data_path / "ibes_dj30_stock_rec_2008_24.feather")
    
    print("Loading FUND data...")
    fund = pd.read_feather(data_path / "fund_tech_dj30_stocks_2008_24.feather")
    
    print("Loading NEWS data...")
    news = pd.read_feather(data_path / "ciq_dj30_stock_news_2008_24.feather")
    
    #convert date strings to datetime objects for proper date arithmetic
    #the "errors='coerce'" means: if a date is invalid, replace it with NaT (Not a Time)
    print("Converting date columns...")
    ibes["anndats"] = pd.to_datetime(ibes["anndats"], errors="coerce")
    ibes["actdats"] = pd.to_datetime(ibes["actdats"], errors="coerce")
    
    #FUND date is already datetime, but let's ensure it
    fund["date"] = pd.to_datetime(fund["date"], errors="coerce")
    
    #NEWS announcedate needs conversion
    news["announcedate"] = pd.to_datetime(news["announcedate"], errors="coerce")
    
    #Clean CUSIP: strip whitespace and make uppercase for consistent matching
    ibes["cusip"] = ibes["cusip"].str.strip().str.upper()
    fund["cusip"] = fund["cusip"].str.strip().str.upper()
    news["cusip"] = news["cusip"].str.strip().str.upper()
    
    print(f"✓ Loaded {len(ibes)} IBES recommendations")
    print(f"✓ Loaded {len(fund)} FUND rows")
    print(f"✓ Loaded {len(news)} NEWS items")
    
    return ibes, fund, news


def build_context_for_rec(
    ibes: pd.DataFrame,
    fund: pd.DataFrame,
    news: pd.DataFrame,
    rec_index: int = 0,
    fund_window_days: int = 30,
    news_window_days: int = 7,
) -> tuple[str, pd.Series]:
    """
    Build a human-readable context string for a single IBES recommendation.
    
    What this does:
    1. Gets one row from IBES (the recommendation we're explaining)
    2. Finds matching FUND data (price/volume) from the 30 days BEFORE the recommendation
    3. Finds matching NEWS headlines from ±7 days around the recommendation
    4. Formats everything into a nice text block
    
    Args:
        ibes: IBES DataFrame with analyst recommendations
        fund: FUND DataFrame with price and fundamental data
        news: NEWS DataFrame with company news
        rec_index: Which row in IBES to analyze (0 = first row)
        fund_window_days: How many days before recommendation to include FUND data
        news_window_days: How many days before/after to include NEWS
        
    Returns:
        tuple: (context_string, recommendation_row)
            - context_string: The formatted text for the LLM
            - recommendation_row: The IBES row as a pandas Series for reference
    """
    
    # Get the specific recommendation we're analyzing
    rec = ibes.iloc[rec_index]
    
    # Extract key information
    cusip = rec["cusip"]
    ticker = rec.get("ticker", "N/A")
    company = rec.get("cname", "N/A")
    ann_date = rec["anndats"]
    analyst = rec.get("analyst", "Unknown")
    
    # Recommendation codes and text
    ereccd = rec.get("ereccd", "N/A")
    etext = rec.get("etext", "N/A")
    ireccd = rec.get("ireccd", "N/A")
    itext = rec.get("itext", "N/A")
    
    # Check if date is valid
    if pd.isna(ann_date):
        return "ERROR: Invalid announcement date for this recommendation.", rec
    
    print(f"\nBuilding context for: {ticker} ({company})")
    print(f"  Recommendation date: {ann_date.date()}")
    print(f"  CUSIP: {cusip}")
    
    #FUND DATA: Last 30 days before recommendation
    
    #Filter FUND data for same company (matching CUSIP)
    fund_company = fund[fund["cusip"] == cusip].copy()
    
    #nly keep rows where date is BEFORE the recommendation date
    #and within the last 30 days before that date
    start_date = ann_date - timedelta(days=fund_window_days)
    fund_window = fund_company[
        (fund_company["date"] >= start_date) & 
        (fund_company["date"] < ann_date)
    ].sort_values("date")
    
    print(f"  Found {len(fund_window)} FUND rows in 30-day window before {ann_date.date()}")
    
    #NEWS DATA: ±7 days around recommendation
    
    #Filter NEWS data for same company
    news_company = news[news["cusip"] == cusip].copy()
    
    #keep news from 7 days before to 7 days after
    news_start = ann_date - timedelta(days=news_window_days)
    news_end = ann_date + timedelta(days=news_window_days)
    news_window = news_company[
        (news_company["announcedate"] >= news_start) &
        (news_company["announcedate"] <= news_end)
    ].sort_values("announcedate")
    
    print(f"  Found {len(news_window)} NEWS items in ±7 day window")
    
    #build the context string
    
    context_parts = []
    
    #Header with basic info
    context_parts.append("=" * 70)
    context_parts.append("ANALYST RECOMMENDATION CONTEXT")
    context_parts.append("=" * 70)
    context_parts.append("")
    context_parts.append(f"Ticker: {ticker}")
    context_parts.append(f"Company: {company}")
    context_parts.append(f"CUSIP: {cusip}")
    context_parts.append(f"Recommendation Date: {ann_date.date()}")
    context_parts.append(f"Analyst: {analyst}")
    context_parts.append("")
    context_parts.append(f"IBES Recommendation Codes:")
    context_parts.append(f"  - Expected Recommendation Code (ereccd): {ereccd}")
    context_parts.append(f"  - Expected Recommendation Text (etext): {etext}")
    context_parts.append(f"  - Investment Recommendation Code (ireccd): {ireccd}")
    context_parts.append(f"  - Investment Recommendation Text (itext): {itext}")
    context_parts.append("")
    
    #FUND data section
    context_parts.append("-" * 70)
    context_parts.append(f"PRICE & FUNDAMENTALS (Last {fund_window_days} days before recommendation)")
    context_parts.append("-" * 70)
    context_parts.append("")
    
    if len(fund_window) > 0:
        #Show summary statistics
        latest_price = fund_window.iloc[-1]["price"] if "price" in fund_window.columns else "N/A"
        avg_volume = fund_window["volume"].mean() if "volume" in fund_window.columns else "N/A"
        
        context_parts.append(f"Latest Price: ${latest_price:.2f}" if isinstance(latest_price, (int, float)) else f"Latest Price: {latest_price}")
        context_parts.append(f"Average Daily Volume: {avg_volume:,.0f}" if isinstance(avg_volume, (int, float)) else f"Average Daily Volume: {avg_volume}")
        context_parts.append("")
        
        #Show recent daily data (last 10 days or all if fewer)
        recent_days = fund_window.tail(10)
        context_parts.append("Recent Daily Data:")
        
        for _, row in recent_days.iterrows():
            date_str = row["date"].date() if pd.notna(row["date"]) else "N/A"
            price = row.get("price", "N/A")
            daily_ret = row.get("daily_return_adjusted", "N/A")
            volume = row.get("volume", "N/A")
            
            #Format numbers nicely
            price_str = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)
            ret_str = f"{daily_ret:+.3%}" if isinstance(daily_ret, (int, float)) else str(daily_ret)
            vol_str = f"{volume:,.0f}" if isinstance(volume, (int, float)) else str(volume)
            
            context_parts.append(f"  • {date_str}: Price={price_str}, Return={ret_str}, Volume={vol_str}")
        
        #Add key fundamentals if available
        if "eps_ttm" in fund_window.columns or "roe" in fund_window.columns:
            context_parts.append("")
            context_parts.append("Key Fundamentals (most recent):")
            latest_fund = fund_window.iloc[-1]
            
            if "eps_ttm" in latest_fund.index:
                eps = latest_fund["eps_ttm"]
                context_parts.append(f"  • EPS (TTM): {eps:.2f}" if pd.notna(eps) else "  • EPS (TTM): N/A")
            
            if "roe" in latest_fund.index:
                roe = latest_fund["roe"]
                context_parts.append(f"  • ROE: {roe:.2%}" if pd.notna(roe) else "  • ROE: N/A")
            
            if "leverage" in latest_fund.index:
                lev = latest_fund["leverage"]
                context_parts.append(f"  • Leverage: {lev:.2f}" if pd.notna(lev) else "  • Leverage: N/A")
    else:
        context_parts.append("⚠ No FUND data available for this time window.")
    
    context_parts.append("")
    
    #NEWS data section
    context_parts.append("-" * 70)
    context_parts.append(f"COMPANY NEWS (±{news_window_days} days around recommendation)")
    context_parts.append("-" * 70)
    context_parts.append("")
    
    if len(news_window) > 0:
        for _, news_row in news_window.iterrows():
            news_date = news_row["announcedate"].date() if pd.notna(news_row["announcedate"]) else "N/A"
            headline = news_row.get("headline", "No headline")
            event_type = news_row.get("eventtype", "")
            
            context_parts.append(f"  • {news_date}: {headline}")
            if event_type and pd.notna(event_type):
                context_parts.append(f"    Event Type: {event_type}")
    else:
        context_parts.append("⚠ No NEWS data available for this time window.")
    
    context_parts.append("")
    context_parts.append("=" * 70)
    
    #Join all parts into one string
    context_str = "\n".join(context_parts)
    
    return context_str, rec


#tester
if __name__ == "__main__":
    """
    This runs only when you execute: python data_loader.py test to make sure you data is laoding properly
    """
    print("Testing data_loader.py...")
    ibes, fund, news = load_datasets()
    print("\n" + "="*70)
    print("Dataset shapes:")
    print(f"  IBES: {ibes.shape}")
    print(f"  FUND: {fund.shape}")
    print(f"  NEWS: {news.shape}")
    print("="*70)