"""
multi_agents.py

Defines the multi-analyst agents used for the Recommender pipeline:
- fundamental_agent
- technical_agent
- news_agent
"""

import os
from crewai import Agent, LLM
from dotenv import load_dotenv

#Load environment variables when this module is imported
load_dotenv()


def _get_gemini_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "No Gemini API key found. Please set GEMINI_API_KEY or GOOGLE_API_KEY "
            "in your environment or .env file."
        )
    return api_key


def _build_gemini_llm(
    model: str = "gemini-2.5-flash",
    temperature: float = 0.2,
) -> LLM:
    api_key = _get_gemini_api_key()
    llm = LLM(
        model=model,
        api_key=api_key,
        temperature=temperature,
    )
    print(f"[DEBUG] Multi-agent Gemini LLM model: {llm.model!r}")
    return llm


#Single shared LLM instance for all three agents
_llm = _build_gemini_llm()


#FUNDAMENTAL ANALYST
fundamental_agent = Agent(
    role="Fundamental Analyst",
    goal=(
        "Strictly evaluate fundamentals (EPS, ROE, margins, revenue growth, "
        "cash flow, leverage, debt quality, liquidity, FCF, valuation ratios). "
        "Do NOT analyze technical indicators or news."
    ),
    backstory=(
        "You are a senior equity research analyst specializing in deep fundamental "
        "analysis for institutional investors. You focus on company financial health, "
        "earnings quality, and valuation."
    ),
    allow_delegation=False,
    memory=False,
    llm=_llm,
    verbose=True,
)


#TECHNICAL ANALYST
technical_agent = Agent(
    role="Technical Analyst",
    goal=(
        "Strictly analyze technical indicators such as RSI, MACD, SMA/EMA, "
        "momentum, ATR, volatility, and price patterns. Ignore all fundamentals "
        "and news."
    ),
    backstory="You are a quant technical trader with expertise in price action and "
              "indicator-driven decision making.",
    allow_delegation=False,
    memory=False,
    llm=_llm,
    verbose=True,
)


#NEWS ANALYST
news_agent = Agent(
    role="News & Sentiment Analyst",
    goal=(
        "Strictly analyze sentiment from historical news articles provided. "
        "Assess tone, impact, risk, and market-moving implications. "
        "Do NOT evaluate fundamentals or technical indicators."
    ),
    backstory="You specialize in news sentiment, macro risk, and market psychology.",
    allow_delegation=False,
    memory=False,
    llm=_llm,
    verbose=True,
)
