"""
multi_recommender.py

Multi-agent Recommender pipeline WITH a Portfolio Manager LLM.

Given:
- cusip
- rec_date
- FUND DataFrame
- NEWS DataFrame

It:
- Extracts the latest fundamentals & technicals before rec_date
- Extracts recent news
- Runs 3 specialist analyst agents (fundamental, technical, news)
- Runs Portfolio Manager agent to synthesize their ratings
- Returns a comprehensive markdown report
"""

from typing import List

import pandas as pd
from crewai import Crew, Process

from .agents import (
    fundamental_agent,
    technical_agent,
    news_agent,
    recommender_manager,
)
from .tasks import (
    fundamental_task,
    technical_task,
    news_task,
    create_recommender_manager_task,
)

# Column sets for data extraction
TECHNICAL_COLS: List[str] = [
    "price_adjusted", "volume_adjusted", "daily_return_adjusted",
    "daily_return_excluding_dividends", "shares_outstanding",
    "mean_30d_returns", "vol_30d_returns", "mean_30d_vol", "vol_spike",
    "ewma_vol", "rsi_14", "macd_line", "macd_signal", "macd_hist",
]

FUNDAMENTAL_COLS: List[str] = [
    "epsfxq_ffill", "eps_yoy_growth", "eps_ttm", "niq_ffill", "ceqq_ffill", "roe",
    "atq_ffill", "ltq_ffill", "dlttq_ffill", "lctq_ffill", "leverage",
    "longterm_debt_ratio", "debt_to_equity", "shortterm_liab_ratio", "cash_ratio",
    "oancfy_ffill", "ivncfy_ffill", "fincfy_ffill", "capxy_ffill", "fcf",
    "ocf_to_assets", "fcf_to_sales", "ocf_to_ni", "cash_flow_to_debt",
    "net_cash_flow", "reinvestment_rate", "croe", "fcf_yield_assets",
    "eps_growth_2q", "eps_growth_4q",
]


def run_multi_analyst_recommendation(
    cusip: str,
    rec_date: pd.Timestamp,
    fund_df: pd.DataFrame,
    news_df: pd.DataFrame,
    news_window_days: int = 30,
    ticker: str = "N/A",
    company: str = "N/A",
) -> str:
    """
    Run the full multi-agent recommender with Portfolio Manager synthesis.

    Args:
        cusip: Company CUSIP identifier
        rec_date: Recommendation date
        fund_df: FUND DataFrame with fundamentals and technicals
        news_df: NEWS DataFrame
        news_window_days: Days of news to include
        ticker: Optional ticker for display
        company: Optional company name for display

    Returns:
        Markdown string with complete recommendation report
    """
    rec_date = pd.to_datetime(rec_date)

    print("\n" + "=" * 70)
    print("MULTI-AGENT RECOMMENDER: Data Extraction")
    print("=" * 70)
    
    # ========================================================================
    # 1. Extract latest FUND row before rec_date
    # ========================================================================
    
    stock_rows = fund_df[
        (fund_df["cusip"] == cusip) & (fund_df["date"] <= rec_date)
    ].sort_values("date")

    if stock_rows.empty:
        return (
            f"## Model Multi-Analyst Recommendation\n\n"
            f"❌ **Error**: No FUND data found for CUSIP {cusip} on or before {rec_date.date()}."
        )

    stock_row = stock_rows.iloc[-1]
    data_date = stock_row["date"]
    
    print(f"  Using FUND data from: {data_date.date()}")

    # Only keep columns that exist
    fundamental_cols = [c for c in FUNDAMENTAL_COLS if c in fund_df.columns]
    technical_cols = [c for c in TECHNICAL_COLS if c in fund_df.columns]

    fundamental_prompt = stock_row[fundamental_cols].to_dict()
    technical_prompt = stock_row[technical_cols].to_dict()
    
    print(f"  Extracted {len(fundamental_cols)} fundamental metrics")
    print(f"  Extracted {len(technical_cols)} technical indicators")

    # ========================================================================
    # 2. Extract NEWS window
    # ========================================================================
    
    start_date = rec_date - pd.Timedelta(days=news_window_days)

    news_filtered = news_df[
        (news_df["cusip"] == cusip)
        & (news_df["announcedate"] >= start_date)
        & (news_df["announcedate"] <= rec_date)
    ].copy()

    if news_filtered.empty:
        news_prompt = "No news in the specified window."
        print(f"  ⚠ No news found in {news_window_days}-day window")
    else:
        news_prompt = news_filtered.to_json(orient="records")
        print(f"  Found {len(news_filtered)} news items in {news_window_days}-day window")

    # Stock info for context
    stock_info = f"""
Stock Context:
- Ticker: {ticker}
- Company: {company}
- CUSIP: {cusip}
- Analysis Date: {rec_date.date()}
- Data as of: {data_date.date()}
"""

    # ========================================================================
    # 3. Run Fundamental Analyst
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("MULTI-AGENT RECOMMENDER: Running Specialists")
    print("=" * 70)
    
    print("\nRunning Fundamental Analyst...")
    fund_crew = Crew(
        agents=[fundamental_agent],
        tasks=[fundamental_task],
        process=Process.sequential,
        verbose=False,  # Avoid recursion issues
    )
    fundamental_output = fund_crew.kickoff(inputs={"fundamentals": fundamental_prompt})
    fundamental_text = str(fundamental_output)
    print("✓ Fundamental Analyst complete")

    # ========================================================================
    # 4. Run Technical Analyst
    # ========================================================================
    
    print("\nRunning Technical Analyst...")
    tech_crew = Crew(
        agents=[technical_agent],
        tasks=[technical_task],
        process=Process.sequential,
        verbose=False,  # Avoid recursion issues
    )
    technical_output = tech_crew.kickoff(inputs={"technicals": technical_prompt})
    technical_text = str(technical_output)
    print("✓ Technical Analyst complete")

    # ========================================================================
    # 5. Run News Analyst
    # ========================================================================
    
    print("\nRunning News Analyst...")
    news_crew = Crew(
        agents=[news_agent],
        tasks=[news_task],
        process=Process.sequential,
        verbose=False,  # Avoid recursion issues
    )
    news_output = news_crew.kickoff(inputs={"news": news_prompt})
    news_text = str(news_output)
    print("✓ News Analyst complete")

    # ========================================================================
    # 6. Run Portfolio Manager to synthesize
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("MULTI-AGENT RECOMMENDER: Manager Synthesis")
    print("=" * 70)
    
    manager_task = create_recommender_manager_task(
        fundamental_report=fundamental_text,
        technical_report=technical_text,
        news_report=news_text,
        stock_info=stock_info,
    )
    
    manager_crew = Crew(
        agents=[recommender_manager],
        tasks=[manager_task],
        process=Process.sequential,
        verbose=False,  # Avoid recursion issues
    )
    
    final_recommendation = manager_crew.kickoff()
    final_text = str(final_recommendation)
    print("✓ Manager synthesis complete")

    # ========================================================================
    # 7. Build comprehensive markdown report
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("✓ Multi-Agent Recommender Complete!")
    print("=" * 70)
    
    lines = []
    
    # Header
    lines.append("# 🤖 Multi-Agent Model Recommendation")
    lines.append("")
    lines.append(f"**Stock**: {ticker} ({company})")
    lines.append(f"**Analysis Date**: {rec_date.date()}")
    lines.append(f"**Data as of**: {data_date.date()}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Final recommendation first (most important)
    lines.append(final_text)
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Then show individual analyst reports
    lines.append("# 📊 Individual Analyst Reports")
    lines.append("")
    
    lines.append("## 1️⃣ Fundamental Analyst Report")
    lines.append(fundamental_text if fundamental_text else "_No output_")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    lines.append("## 2️⃣ Technical Analyst Report")
    lines.append(technical_text if technical_text else "_No output_")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    lines.append("## 3️⃣ News & Sentiment Analyst Report")
    lines.append(news_text if news_text else "_No output_")

    return "\n".join(lines)