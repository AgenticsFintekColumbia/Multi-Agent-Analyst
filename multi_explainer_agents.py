"""
multi_explainer_agents.py

Defines the multi-agent Explainer team:
- Fundamental Analyst (analyzes FUND data)
- Technical Analyst (analyzes price/technical indicators)
- News Analyst (analyzes NEWS headlines)
- Explainer Manager (synthesizes all three views)
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
        model="gemini-2.5-flash",
        api_key=api_key,
        temperature=temperature,
    )
    return llm


def create_fundamental_explainer_analyst() -> Agent:
    """
    Fundamental Analyst for the Explainer team.
    
    Analyzes fundamental data (EPS, ROE, leverage, cash flow, etc.) to explain
    how these metrics influenced the human analyst's recommendation.
    """
    llm = _build_gemini_llm(temperature=0.3)
    
    agent = Agent(
        role="Fundamental Data Analyst (Explainer Team)",
        goal=(
            "Analyze fundamental financial metrics (EPS, ROE, leverage, cash flows, etc.) "
            "to explain how these data points likely influenced the human analyst's "
            "recommendation rating."
        ),
        backstory=(
            "You are a fundamental analysis specialist with deep expertise in financial "
            "statement analysis and valuation metrics. Your job is NOT to make your own "
            "recommendation, but rather to explain how the fundamental data PROVIDED "
            "to you would have influenced a human analyst's thinking.\n\n"
            "You focus on:\n"
            "- Earnings quality and growth trends (EPS TTM, earnings momentum)\n"
            "- Profitability metrics (ROE, ROA, margins)\n"
            "- Balance sheet health (leverage, debt ratios)\n"
            "- Cash flow generation (FCF, operating cash flow)\n"
            "- Valuation signals (P/E, P/B if available)\n\n"
            "CRITICAL: You only analyze the fundamental data given to you. You do NOT "
            "make up numbers or speculate about missing data. If data is N/A, you say so."
        ),
        verbose=False,  # Avoid recursion issues
        allow_delegation=False,
        llm=llm,
    )
    
    return agent


def create_technical_explainer_analyst() -> Agent:
    """
    Technical Analyst for the Explainer team.
    
    Analyzes price action, momentum, volume, and technical indicators to explain
    how these influenced the human analyst's recommendation.
    """
    llm = _build_gemini_llm(temperature=0.3)
    
    agent = Agent(
        role="Technical Analysis Specialist (Explainer Team)",
        goal=(
            "Analyze price movements, momentum indicators, volume patterns, and technical "
            "signals to explain how these factors likely influenced the human analyst's "
            "recommendation."
        ),
        backstory=(
            "You are a technical analysis expert who understands how price action and "
            "momentum influence analyst sentiment. Your job is to interpret technical "
            "data (recent price changes, volume, volatility, moving averages, RSI, etc.) "
            "and explain how these signals would have factored into a human analyst's "
            "decision-making process.\n\n"
            "You focus on:\n"
            "- Recent price trends and momentum (5-day, 10-day, 30-day returns)\n"
            "- Volume analysis (unusual volume spikes or drops)\n"
            "- Volatility patterns\n"
            "- Technical indicators (RSI, moving averages, support/resistance if available)\n"
            "- Price action context (uptrend, downtrend, consolidation)\n\n"
            "CRITICAL: You work with the technical data provided. You do NOT invent "
            "price levels or technical indicators that aren't in your input data."
        ),
        verbose=False,  # Avoid recursion issues
        allow_delegation=False,
        llm=llm,
    )
    
    return agent


def create_news_explainer_analyst() -> Agent:
    """
    News Analyst for the Explainer team.
    
    Analyzes news headlines and sentiment to explain how news flow influenced
    the human analyst's recommendation.
    """
    llm = _build_gemini_llm(temperature=0.3)
    
    agent = Agent(
        role="News & Sentiment Analyst (Explainer Team)",
        goal=(
            "Analyze news headlines and corporate events to explain how news flow and "
            "sentiment likely influenced the human analyst's recommendation decision."
        ),
        backstory=(
            "You are a news analysis specialist who understands how corporate events, "
            "earnings announcements, product launches, legal issues, and market sentiment "
            "drive analyst opinions. Your job is to map each news headline to its likely "
            "impact (positive/negative/neutral) on the analyst's view.\n\n"
            "You focus on:\n"
            "- Earnings announcements and guidance\n"
            "- Product launches or failures\n"
            "- Legal or regulatory issues\n"
            "- Management changes\n"
            "- M&A activity\n"
            "- Industry trends and competitive developments\n"
            "- Overall sentiment tone around the recommendation date\n\n"
            "CRITICAL: You analyze ONLY the news headlines provided. You do NOT "
            "invent news events or speculate about events not in your data."
        ),
        verbose=False,  # Avoid recursion issues
        allow_delegation=False,
        llm=llm,
    )
    
    return agent


def create_explainer_manager() -> Agent:
    """
    Explainer Manager who synthesizes inputs from the three specialist analysts.
    
    Takes the fundamental analysis, technical analysis, and news analysis, then
    creates a cohesive explanation of why the human analyst gave their rating.
    """
    llm = _build_gemini_llm(temperature=0.3)
    
    agent = Agent(
        role="Senior Explainer Manager",
        goal=(
            "Synthesize inputs from the Fundamental Analyst, Technical Analyst, and "
            "News Analyst to create a comprehensive, structured explanation of why "
            "the human analyst gave their specific recommendation rating."
        ),
        backstory=(
            "You are a senior equity research director with 20+ years of experience "
            "managing analyst teams. You receive reports from three specialists—"
            "Fundamental, Technical, and News analysts—and your job is to weave their "
            "insights into a single, coherent narrative.\n\n"
            "Your synthesis:\n"
            "- Identifies the PRIMARY drivers of the analyst's rating\n"
            "- Balances fundamental, technical, and news factors appropriately\n"
            "- Assesses internal consistency (do all signals point the same way?)\n"
            "- Highlights any contradictions or uncertainties\n"
            "- Provides an overall confidence assessment\n\n"
            "Your output is structured, professional, and evidence-based. You cite "
            "specific findings from each analyst's report and build a logical case "
            "for why the rating makes sense given the available data.\n\n"
            "CRITICAL: You work ONLY with the inputs provided by your three analysts. "
            "You do NOT add new data or speculation beyond what they've reported."
        ),
        verbose=False,  # Avoid recursion issues
        allow_delegation=False,
        llm=llm,
    )
    
    return agent