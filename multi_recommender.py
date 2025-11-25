"""
multi_recommender.py

Multi-agent Recommender pipeline WITHOUT a Portfolio Manager LLM.

Given:
- cusip
- rec_date
- FUND DataFrame
- NEWS DataFrame

It:
- Extracts the latest fundamentals & technicals before rec_date
- Extracts recent news
- Runs 3 analyst agents (fundamental, technical, news)
- Combines their ratings in Python (simple rule) into a final model rating
- Returns a markdown report.
"""

from typing import List, Optional
from collections import Counter

import pandas as pd
from crewai import Crew

from multi_agents import fundamental_agent, technical_agent, news_agent
from multi_tasks import fundamental_task, technical_task, news_task

#These column sets mirror vinods code
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

#Canonical rating labels we expect from agents (we should normailize these)
CANONICAL_RATINGS = ["StrongBuy", "Buy", "Hold", "UnderPerform", "Sell"]


def _extract_rating(text: str) -> Optional[str]:
    """
    Try to extract a rating from the agent's text output.

    We look for any of the canonical labels (or common variants)
    in a case-insensitive way and map them to one of:
    {StrongBuy, Buy, Hold, UnderPerform, Sell}.
    """
    if not text:
        return None

    lower = text.lower()

    patterns = [
        ("strongbuy", "StrongBuy"),
        ("strong buy", "StrongBuy"),
        ("strong_buy", "StrongBuy"),
        ("strong-buy", "StrongBuy"),
        ("strong sell", "Sell"),  #just in case

        ("underperform", "UnderPerform"),
        ("under perform", "UnderPerform"),

        ("hold", "Hold"),

        ("sell", "Sell"),
        ("buy", "Buy"),
    ]

    #Find the earliest occurrence of any pattern
    best_pos = None
    best_label = None

    for pat, label in patterns:
        idx = lower.find(pat)
        if idx != -1:
            if best_pos is None or idx < best_pos:
                best_pos = idx
                best_label = label

    return best_label


def _combine_ratings(fund_rating: Optional[str],
                     tech_rating: Optional[str],
                     news_rating: Optional[str]) -> str:
    """
    Combine the three analyst ratings into a single final rating.

    Simple rule:
    - Use majority vote over {fund, tech, news} (ignoring None).
    - If all three disagree or there is a tie -> return 'Hold'.
    - If no rating at all -> return 'Unknown'.
    """
    ratings = [r for r in [fund_rating, tech_rating, news_rating] if r is not None]

    if not ratings:
        return "Unknown"

    counts = Counter(ratings)
    #Most common returns list of tuples sorted by count desc
    most_common = counts.most_common()

    if len(most_common) == 1:
        # Only one unique rating
        return most_common[0][0]

    #Check for a clear majority (e.g., 2 vs 1)
    if most_common[0][1] > most_common[1][1]:
        return most_common[0][0]

    #Otherwise, tie or all different -> default to Hold
    return "Hold"


def run_multi_analyst_recommendation(
    cusip: str,
    rec_date: pd.Timestamp,
    fund_df: pd.DataFrame,
    news_df: pd.DataFrame,
    news_window_days: int = 30,
) -> str:
    """
    Run the full multi-agent recommender for a given cusip and rec_date.

    Returns:
        Markdown string summarizing:
        - Final model rating
        - Fundamental, technical, and news ratings + their reasoning.
    """
    rec_date = pd.to_datetime(rec_date)

    #1. Select latest FUND row before rec_date

    stock_rows = fund_df[
        (fund_df["cusip"] == cusip) & (fund_df["date"] <= rec_date)
    ].sort_values("date")

    if stock_rows.empty:
        return f"## Model Multi-Analyst Recommendation\n\n" \
               f"No FUND data found for CUSIP {cusip} on or before {rec_date.date()}."

    stock_row = stock_rows.iloc[-1]

    #Only keep columns that actually exist to avoid KeyError
    fundamental_cols = [c for c in FUNDAMENTAL_COLS if c in fund_df.columns]
    technical_cols = [c for c in TECHNICAL_COLS if c in fund_df.columns]

    fundamental_prompt = stock_row[fundamental_cols].to_dict()
    technical_prompt = stock_row[technical_cols].to_dict()

    #2. Extract NEWS window

    start_date = rec_date - pd.Timedelta(days=news_window_days)

    news_filtered = news_df[
        (news_df["cusip"] == cusip)
        & (news_df["announcedate"] >= start_date)
        & (news_df["announcedate"] <= rec_date)
    ].copy()

    if news_filtered.empty:
        news_prompt = "No news in the specified window."
    else:
        #JSON string of list-of-records
        news_prompt = news_filtered.to_json(orient="records")

    #3. Run Fundamental Analyst

    fund_crew = Crew(
        agents=[fundamental_agent],
        tasks=[fundamental_task],
        verbose=True,
    )
    fundamental_output = fund_crew.kickoff(inputs={"fundamentals": fundamental_prompt})
    fundamental_text = str(fundamental_output)
    fund_rating = _extract_rating(fundamental_text)

    #4. Run Technical Analyst

    tech_crew = Crew(
        agents=[technical_agent],
        tasks=[technical_task],
        verbose=True,
    )
    technical_output = tech_crew.kickoff(inputs={"technicals": technical_prompt})
    technical_text = str(technical_output)
    tech_rating = _extract_rating(technical_text)

    #5. Run News Analyst

    news_crew = Crew(
        agents=[news_agent],
        tasks=[news_task],
        verbose=True,
    )
    news_output = news_crew.kickoff(inputs={"news": news_prompt})
    news_text = str(news_output)
    news_rating = _extract_rating(news_text)

    #6. Combine into final rating

    final_rating = _combine_ratings(fund_rating, tech_rating, news_rating)

    #7. Build markdown report (we shoudl edit this)

    lines = []
    lines.append("## Model Multi-Analyst Recommendation")
    lines.append(f"- **Final model rating:** {final_rating}")
    lines.append("")
    lines.append("### Fundamental Analyst")
    lines.append(fundamental_text if fundamental_text else "_No output_")
    lines.append("")
    lines.append("### Technical Analyst")
    lines.append(technical_text if technical_text else "_No output_")
    lines.append("")
    lines.append("### News & Sentiment Analyst")
    lines.append(news_text if news_text else "_No output_")

    return "\n".join(lines)
