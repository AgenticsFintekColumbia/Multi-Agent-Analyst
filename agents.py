"""
agents.py

Defines the AI agents for our system using Google Gemini via CrewAI.
"""

import os
from crewai import Agent, LLM


def _get_gemini_api_key() -> str:
    """Fetch Gemini API key from env (GEMINI_API_KEY or GOOGLE_API_KEY)."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "No Gemini API key found. Please set GEMINI_API_KEY or GOOGLE_API_KEY "
            "in your environment or .env file."
        )
    return api_key


def _build_gemini_llm(temperature: float = 0.3) -> LLM:
    """Create a Gemini LLM instance for CrewAI."""
    api_key = _get_gemini_api_key()
    llm = LLM(
        model="gemini-2.5-flash",   # Fast & cheap, good for this use case
        api_key=api_key,
        temperature=temperature,
    )
    print(f"[DEBUG] CrewAI Gemini LLM model: {llm.model!r}")
    return llm


def create_explainer_agent() -> Agent:
    """
    Create an Explainer Agent that analyzes analyst recommendations.

    This agent acts like a senior sell-side equity analyst who:
    - Reads IBES recommendation data, price/fundamental data, and news
    - Explains the rationale behind why an analyst gave a specific rating
    - Provides structured, professional analysis
    """

    llm = _build_gemini_llm(temperature=0.3)

    agent = Agent(
        role="Sell-Side Equity Analyst Explainer",
        goal=(
            "Analyze analyst recommendations by examining price data, fundamentals, "
            "and news to provide clear, structured explanations for why an analyst "
            "likely gave a specific BUY/HOLD/SELL rating."
        ),
        backstory=(
            "You are a highly experienced senior equity analyst with 15+ years on Wall Street. "
            "Your specialty is reverse-engineering analyst ratings by carefully examining "
            "the available data—stock price movements, fundamental metrics, and news flow—"
            "to construct logical, evidence-based explanations for why a particular rating was issued.\n\n"
            "You understand that analyst recommendations are driven by:\n"
            "- Recent price performance and technical indicators\n"
            "- Fundamental metrics (EPS growth, ROE, leverage, cash flows)\n"
            "- News catalysts (product launches, earnings, legal issues, partnerships)\n"
            "- Valuation concerns and risk factors\n"
            "- Industry trends and competitive dynamics\n\n"
            "Your analysis is always:\n"
            "- Evidence-based: You cite specific data points from the provided context\n"
            "- Structured: You organize findings into clear categories\n"
            "- Honest about limitations: You acknowledge when data is incomplete\n"
            "- Professional: You write in clear financial language suitable for institutional investors\n\n"
            "CRITICAL RULES:\n"
            "1. Use ONLY the data provided in the context—do not hallucinate events or numbers\n"
            "2. If fundamental data is missing (N/A), acknowledge it but don't make up values\n"
            "3. If something is uncertain, say so—don't be overconfident\n"
            "4. Focus on explaining the rating, not predicting future outcomes"
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )

    return agent


def create_recommender_agent() -> Agent:
    """
    Create a Recommender Agent that issues its own BUY/HOLD/SELL-style rating.

    This agent:
    - Reads the same IBES/FUND/NEWS context
    - Ignores the analyst's rating when forming its OWN view
    - Outputs a discrete rating from {STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL}
      plus a confidence score and a short rationale
    """

    # For reproducibility, we can keep temperature low
    llm = _build_gemini_llm(temperature=0.2)

    agent = Agent(
        role="Sell-Side Equity Analyst Recommender",
        goal=(
            "Given contextual data about a stock (recent price action, fundamentals, "
            "and news), issue your own recommendation rating from the set "
            "{STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL} with a confidence score "
            "and a concise rationale."
        ),
        backstory=(
            "You are a disciplined, valuation-driven equity analyst. You read market "
            "data, company fundamentals, and news flow, and then form your own view "
            "on whether the stock should be rated STRONG_BUY, BUY, HOLD, SELL, or STRONG_SELL.\n\n"
            "You are aware that IBES already contains an analyst rating, but your job "
            "is NOT to repeat or mimic that rating blindly. Instead, you should form "
            "your OWN independent view based strictly on the data in the context.\n\n"
            "Your style:\n"
            "- You prefer clear categorical recommendations over hedged language.\n"
            "- You explicitly balance positive drivers vs risks.\n"
            "- You provide a confidence score between 0 and 100.\n"
            "- You avoid speculation beyond the provided data."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )

    return agent
