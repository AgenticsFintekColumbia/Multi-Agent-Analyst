"""
multi_agents.py

Defines the multi-analyst agents used for the Recommender pipeline:
- fundamental_agent
- technical_agent
- news_agent
- recommender_manager (NEW - synthesizes all three)
"""

import os
from crewai import Agent, LLM
from dotenv import load_dotenv

# Load environment variables when this module is imported
# Silently fail if .env doesn't exist (user might set env vars directly)
try:
    load_dotenv()
except Exception:
    # .env file missing or has issues - that's okay, continue
    pass


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


#Single shared LLM instance for all agents
_llm = _build_gemini_llm()


# ============================================================================
# SPECIALIST ANALYSTS (using vinods implementation)
# ============================================================================

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
    verbose=False,  #Avoid recursion issues
)


#TECHNICAL ANALYST
technical_agent = Agent(
    role="Technical Analyst",
    goal=(
        "Strictly analyze technical indicators such as RSI, MACD, SMA/EMA, "
        "momentum, ATR, volatility, and price patterns. Ignore all fundamentals "
        "and news."
    ),
    backstory=(
        "You are a quant technical trader with expertise in price action and "
        "indicator-driven decision making."
    ),
    allow_delegation=False,
    memory=False,
    llm=_llm,
    verbose=False,  #Avoid recursion issues
)


#NEWS ANALYST
news_agent = Agent(
    role="News & Sentiment Analyst",
    goal=(
        "Strictly analyze sentiment from historical news articles provided. "
        "Assess tone, impact, risk, and market-moving implications. "
        "Do NOT evaluate fundamentals or technical indicators."
    ),
    backstory=(
        "You specialize in news sentiment, macro risk, and market psychology."
    ),
    allow_delegation=False,
    memory=False,
    llm=_llm,
    verbose=False,  #Avoid recursion issues
)


# ============================================================================
# RECOMMENDER MANAGER
# ============================================================================

recommender_manager = Agent(
    role="Portfolio Manager & Rating Synthesizer",
    goal=(
        "Synthesize ratings from the Fundamental Analyst, Technical Analyst, and "
        "News Analyst into a single, coherent model recommendation. Make the final "
        "investment decision: StrongBuy, Buy, Hold, UnderPerform, or Sell."
    ),
    backstory=(
        "You are a veteran portfolio manager with 25+ years of experience managing "
        "institutional equity portfolios. You receive recommendations from three "
        "specialist analysts—Fundamental, Technical, and News—and your job is to "
        "synthesize their views into a single actionable rating.\n\n"
        "Your decision-making process:\n"
        "- You understand that different market regimes favor different signals "
        "(e.g., fundamentals dominate in stable markets, technicals in volatile markets)\n"
        "- You explicitly weigh the strength of each analyst's conviction\n"
        "- You identify contradictions and resolve them with clear logic\n"
        "- You prioritize risk management and downside protection\n"
        "- You provide a confidence score based on signal alignment\n\n"
        "Your style:\n"
        "- Decisive: You choose ONE clear rating, not a hedge\n"
        "- Transparent: You explain your weighting logic\n"
        "- Risk-aware: You acknowledge uncertainties and data quality issues\n"
        "- Quantitative: You reference specific data points from analyst reports\n\n"
        "CRITICAL: You work ONLY with the three analyst reports provided. "
        "You do NOT add external data or speculate beyond what they've reported."
    ),
    allow_delegation=False,
    memory=False,
    llm=_llm,
    verbose=False,  #Avoid recursion issues
)