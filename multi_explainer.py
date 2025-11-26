"""
multi_explainer.py

Orchestrates the multi-agent Explainer team:
1. Splits the context data into three parts (fundamental, technical, news)
2. Runs three specialist analysts in parallel
3. Runs the manager to synthesize their outputs
4. Returns a comprehensive explanation
"""

import pandas as pd
from datetime import timedelta
from crewai import Crew, Process

from multi_explainer_agents import (
    create_fundamental_explainer_analyst,
    create_technical_explainer_analyst,
    create_news_explainer_analyst,
    create_explainer_manager,
)
from multi_explainer_tasks import (
    create_fundamental_explainer_task,
    create_technical_explainer_task,
    create_news_explainer_task,
    create_explainer_manager_task,
)


def extract_fundamental_data(rec_series, fund_df: pd.DataFrame, fund_window_days: int = 30) -> str:
    """
    Extract and format fundamental data for the Fundamental Analyst.
    
    Returns a structured string containing:
    - Latest fundamental metrics (EPS, ROE, leverage, etc.)
    - Recent price levels (but NOT detailed price movements - that's technical)
    """
    cusip = rec_series["cusip"]
    ann_date = rec_series["anndats"]
    
    if pd.isna(ann_date):
        return "ERROR: Invalid announcement date."
    
    # Get FUND data for this company in the window before rec date
    fund_company = fund_df[fund_df["cusip"] == cusip].copy()
    start_date = ann_date - timedelta(days=fund_window_days)
    fund_window = fund_company[
        (fund_company["date"] >= start_date) & 
        (fund_company["date"] < ann_date)
    ].sort_values("date")
    
    if len(fund_window) == 0:
        return "⚠ No fundamental data available for this time window."
    
    # Get the most recent row for fundamentals
    latest = fund_window.iloc[-1]
    
    parts = []
    parts.append("FUNDAMENTAL METRICS")
    parts.append("=" * 60)
    parts.append(f"Data as of: {latest['date'].date() if pd.notna(latest['date']) else 'N/A'}")
    parts.append(f"Stock Price: ${latest.get('price', 'N/A')}")
    parts.append("")
    
    # Earnings & Profitability
    parts.append("Earnings & Profitability:")
    eps = latest.get("eps_ttm", None)
    parts.append(f"  • EPS (TTM): {eps:.2f}" if pd.notna(eps) else "  • EPS (TTM): N/A")
    
    roe = latest.get("roe", None)
    parts.append(f"  • ROE: {roe:.2%}" if pd.notna(roe) else "  • ROE: N/A")
    
    roa = latest.get("roa", None)
    parts.append(f"  • ROA: {roa:.2%}" if pd.notna(roa) else "  • ROA: N/A")
    
    parts.append("")
    
    # Balance Sheet
    parts.append("Balance Sheet:")
    leverage = latest.get("leverage", None)
    parts.append(f"  • Leverage: {leverage:.2f}" if pd.notna(leverage) else "  • Leverage: N/A")
    
    de_ratio = latest.get("de_ratio", None)
    parts.append(f"  • D/E Ratio: {de_ratio:.2f}" if pd.notna(de_ratio) else "  • D/E Ratio: N/A")
    
    parts.append("")
    
    # Cash Flow (if available)
    parts.append("Cash Flow:")
    fcf = latest.get("fcf", None)
    parts.append(f"  • Free Cash Flow: ${fcf:,.0f}" if pd.notna(fcf) else "  • Free Cash Flow: N/A")
    
    parts.append("")
    parts.append("=" * 60)
    
    return "\n".join(parts)


def extract_technical_data(rec_series, fund_df: pd.DataFrame, fund_window_days: int = 30) -> str:
    """
    Extract and format technical/price data for the Technical Analyst.
    
    Returns a structured string containing:
    - Recent price movements and returns
    - Volume patterns
    - Momentum indicators (if available)
    """
    cusip = rec_series["cusip"]
    ann_date = rec_series["anndats"]
    
    if pd.isna(ann_date):
        return "ERROR: Invalid announcement date."
    
    # Get FUND data for this company
    fund_company = fund_df[fund_df["cusip"] == cusip].copy()
    start_date = ann_date - timedelta(days=fund_window_days)
    fund_window = fund_company[
        (fund_company["date"] >= start_date) & 
        (fund_company["date"] < ann_date)
    ].sort_values("date")
    
    if len(fund_window) == 0:
        return "⚠ No technical data available for this time window."
    
    parts = []
    parts.append("TECHNICAL & PRICE DATA")
    parts.append("=" * 60)
    parts.append(f"Analysis window: {start_date.date()} to {ann_date.date()}")
    parts.append("")
    
    # Price summary
    if "price" in fund_window.columns and len(fund_window) > 0:
        latest_price = fund_window.iloc[-1]["price"]
        first_price = fund_window.iloc[0]["price"]
        
        parts.append("Price Summary:")
        parts.append(f"  • Latest price: ${latest_price:.2f}" if pd.notna(latest_price) else "  • Latest price: N/A")
        parts.append(f"  • Starting price: ${first_price:.2f}" if pd.notna(first_price) else "  • Starting price: N/A")
        
        if pd.notna(latest_price) and pd.notna(first_price) and first_price != 0:
            period_return = (latest_price - first_price) / first_price
            parts.append(f"  • Period return: {period_return:+.2%}")
        parts.append("")
    
    # Recent daily data (last 10 days)
    parts.append("Recent Daily Price Action (last 10 days):")
    recent = fund_window.tail(10)
    
    for _, row in recent.iterrows():
        date_str = row["date"].date() if pd.notna(row["date"]) else "N/A"
        price = row.get("price", "N/A")
        daily_ret = row.get("daily_return_adjusted", "N/A")
        volume = row.get("volume", "N/A")
        
        price_str = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)
        ret_str = f"{daily_ret:+.2%}" if isinstance(daily_ret, (int, float)) else str(daily_ret)
        vol_str = f"{volume:,.0f}" if isinstance(volume, (int, float)) else str(volume)
        
        parts.append(f"  • {date_str}: Price={price_str}, Return={ret_str}, Volume={vol_str}")
    
    parts.append("")
    
    # Volume analysis
    if "volume" in fund_window.columns:
        avg_vol = fund_window["volume"].mean()
        parts.append("Volume Analysis:")
        parts.append(f"  • Average daily volume: {avg_vol:,.0f}" if pd.notna(avg_vol) else "  • Average daily volume: N/A")
        
        latest_vol = fund_window.iloc[-1]["volume"]
        if pd.notna(latest_vol) and pd.notna(avg_vol) and avg_vol != 0:
            vol_ratio = latest_vol / avg_vol
            parts.append(f"  • Latest volume vs average: {vol_ratio:.2f}x")
        parts.append("")
    
    # Technical indicators (if available in data)
    parts.append("Technical Indicators:")
    latest = fund_window.iloc[-1]
    
    rsi = latest.get("rsi_14", None)
    parts.append(f"  • RSI (14-day): {rsi:.1f}" if pd.notna(rsi) else "  • RSI (14-day): N/A")
    
    volatility = latest.get("volatility_30d", None)
    parts.append(f"  • Volatility (30d): {volatility:.2%}" if pd.notna(volatility) else "  • Volatility (30d): N/A")
    
    parts.append("")
    parts.append("=" * 60)
    
    return "\n".join(parts)


def extract_news_data(rec_series, news_df: pd.DataFrame, news_window_days: int = 7) -> str:
    """
    Extract and format news data for the News Analyst.
    
    Returns a structured string containing:
    - News headlines around the recommendation date
    - Event types
    """
    cusip = rec_series["cusip"]
    ann_date = rec_series["anndats"]
    
    if pd.isna(ann_date):
        return "ERROR: Invalid announcement date."
    
    # Get NEWS data for this company
    news_company = news_df[news_df["cusip"] == cusip].copy()
    news_start = ann_date - timedelta(days=news_window_days)
    news_end = ann_date + timedelta(days=news_window_days)
    news_window = news_company[
        (news_company["announcedate"] >= news_start) &
        (news_company["announcedate"] <= news_end)
    ].sort_values("announcedate")
    
    parts = []
    parts.append("NEWS HEADLINES & EVENTS")
    parts.append("=" * 60)
    parts.append(f"Window: ±{news_window_days} days around {ann_date.date()}")
    parts.append("")
    
    if len(news_window) == 0:
        parts.append("⚠ No news data available for this time window.")
    else:
        parts.append(f"Total news items: {len(news_window)}")
        parts.append("")
        
        for _, news_row in news_window.iterrows():
            news_date = news_row["announcedate"].date() if pd.notna(news_row["announcedate"]) else "N/A"
            headline = news_row.get("headline", "No headline")
            event_type = news_row.get("eventtype", "")
            
            parts.append(f"📰 {news_date}:")
            parts.append(f"   {headline}")
            if event_type and pd.notna(event_type):
                parts.append(f"   [Event Type: {event_type}]")
            parts.append("")
    
    parts.append("=" * 60)
    
    return "\n".join(parts)


def extract_ibes_info(rec_series) -> str:
    """
    Extract IBES recommendation info for the manager.
    """
    parts = []
    parts.append("IBES RECOMMENDATION DETAILS")
    parts.append("=" * 60)
    parts.append(f"Ticker: {rec_series.get('ticker', 'N/A')}")
    parts.append(f"Company: {rec_series.get('cname', 'N/A')}")
    parts.append(f"CUSIP: {rec_series.get('cusip', 'N/A')}")
    parts.append(f"Recommendation Date: {rec_series['anndats'].date() if pd.notna(rec_series['anndats']) else 'N/A'}")
    parts.append(f"Analyst: {rec_series.get('analyst', 'Unknown')}")
    parts.append("")
    parts.append(f"Rating (etext): {rec_series.get('etext', 'N/A')}")
    parts.append(f"Rating Code (ereccd): {rec_series.get('ereccd', 'N/A')}")
    parts.append("")
    parts.append("=" * 60)
    
    return "\n".join(parts)


def run_multi_analyst_explainer(
    ibes_df: pd.DataFrame,
    fund_df: pd.DataFrame,
    news_df: pd.DataFrame,
    rec_index: int = 0,
    fund_window_days: int = 30,
    news_window_days: int = 7,
) -> str:
    """
    Run the multi-agent Explainer team.
    
    Steps:
    1. Extract IBES recommendation
    2. Split data into fundamental/technical/news components
    3. Run three specialist analysts
    4. Run manager to synthesize outputs
    5. Return final explanation
    """
    
    # Get the recommendation
    rec_series = ibes_df.iloc[rec_index]
    
    print("\n" + "=" * 70)
    print("MULTI-AGENT EXPLAINER: Data Extraction")
    print("=" * 70)
    
    # Extract data for each analyst
    print("Extracting fundamental data...")
    fundamental_data = extract_fundamental_data(rec_series, fund_df, fund_window_days)
    
    print("Extracting technical data...")
    technical_data = extract_technical_data(rec_series, fund_df, fund_window_days)
    
    print("Extracting news data...")
    news_data = extract_news_data(rec_series, news_df, news_window_days)
    
    print("Extracting IBES info...")
    ibes_info = extract_ibes_info(rec_series)
    
    # Create agents
    print("\n" + "=" * 70)
    print("MULTI-AGENT EXPLAINER: Creating Agents")
    print("=" * 70)
    
    fundamental_analyst = create_fundamental_explainer_analyst()
    technical_analyst = create_technical_explainer_analyst()
    news_analyst = create_news_explainer_analyst()
    explainer_manager = create_explainer_manager()
    
    # Create tasks for the three specialist analysts
    print("\n" + "=" * 70)
    print("MULTI-AGENT EXPLAINER: Running Specialist Analysts")
    print("=" * 70)
    
    fundamental_task = create_fundamental_explainer_task(fundamental_analyst, fundamental_data)
    technical_task = create_technical_explainer_task(technical_analyst, technical_data)
    news_task = create_news_explainer_task(news_analyst, news_data)
    
    # Run the three analysts (they can run in parallel conceptually, but CrewAI runs sequentially)
    # Note: verbose=False to avoid Rich console recursion issues with multiple crews
    print("\nRunning Fundamental Analyst...")
    fundamental_crew = Crew(
        agents=[fundamental_analyst],
        tasks=[fundamental_task],
        process=Process.sequential,
        verbose=False,  # Changed to False to avoid recursion
    )
    fundamental_report = fundamental_crew.kickoff()
    print("✓ Fundamental Analyst complete")
    
    print("\nRunning Technical Analyst...")
    technical_crew = Crew(
        agents=[technical_analyst],
        tasks=[technical_task],
        process=Process.sequential,
        verbose=False,  # Changed to False to avoid recursion
    )
    technical_report = technical_crew.kickoff()
    print("✓ Technical Analyst complete")
    
    print("\nRunning News Analyst...")
    news_crew = Crew(
        agents=[news_analyst],
        tasks=[news_task],
        process=Process.sequential,
        verbose=False,  # Changed to False to avoid recursion
    )
    news_report = news_crew.kickoff()
    print("✓ News Analyst complete")
    
    # Now run the manager to synthesize
    print("\n" + "=" * 70)
    print("MULTI-AGENT EXPLAINER: Manager Synthesis")
    print("=" * 70)
    
    manager_task = create_explainer_manager_task(
        explainer_manager,
        ibes_info,
        str(fundamental_report),
        str(technical_report),
        str(news_report),
    )
    
    manager_crew = Crew(
        agents=[explainer_manager],
        tasks=[manager_task],
        process=Process.sequential,
        verbose=False,  # Changed to False to avoid recursion
    )
    
    final_explanation = manager_crew.kickoff()
    print("✓ Manager synthesis complete")
    
    print("\n" + "=" * 70)
    print("✓ Multi-Agent Explainer Complete!")
    print("=" * 70)
    
    return str(final_explanation)