"""
agents.py

Defines the AI agents for our system using Google Gemini via CrewAI.
"""

import os
from crewai import Agent, LLM


def create_explainer_agent():
    """
    Create an Explainer Agent that analyzes analyst recommendations.

    This agent acts like a senior sell-side equity analyst who:
    - Reads IBES recommendation data, price/fundamental data, and news
    - Explains the rationale behind why an analyst gave a specific rating
    - Provides structured, professional analysis

    Returns:
        Agent: A CrewAI agent configured for explaining recommendations
    """

    # 1. Get the Gemini API key from environment variables.
    # We accept either GEMINI_API_KEY or GOOGLE_API_KEY for flexibility.
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "No Gemini API key found. Please set GEMINI_API_KEY or GOOGLE_API_KEY "
            "in your environment or .env file."
        )

    # 2. Create Gemini LLM using CrewAI's LLM wrapper.
    # Use a CURRENT supported model: gemini-2.5-flash (fast & cheap) :contentReference[oaicite:0]{index=0}
    llm = LLM(
        model="gemini-2.5-flash",  # <--- IMPORTANT: new model name
        api_key=api_key,
        temperature=0.3,
    )

    # Debug print so we can SEE what model CrewAI thinks it's using
    print(f"[DEBUG] CrewAI Gemini LLM model: {llm.model!r}")

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
