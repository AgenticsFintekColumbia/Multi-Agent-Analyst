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
            "You are a fundamental analysis specialist. Your job is to explain how the " 
            "fundamental data provided would have influenced a human analyst's thinking.\n\n" 
            "CRITICAL RULES:\n" 
            "- Be CONCISE - no planning text, no 'I will', no process explanations\n" 
            "- Start directly with your analysis\n" 
            "- If data is N/A or missing, state it explicitly\n" 
            "- Do NOT make up numbers or speculate about missing data"
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
            "You are a technical analysis expert. Your job is to interpret technical " 
            "data and explain how these signals would have factored into a human analyst's " 
            "decision-making process.\n\n" 
            "CRITICAL RULES:\n" 
            "- Be CONCISE - no planning text, no 'Here's a plan', no process explanations\n" 
            "- Start directly with your analysis\n" 
            "- Work with ONLY the technical data provided\n" 
            "- Do NOT invent price levels or technical indicators"
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
            "You are a news analysis specialist. Your job is to map each news headline " 
            "to its likely impact (positive/negative/neutral) on the analyst's view.\n\n" 
            "CRITICAL RULES:\n" 
            "- Be CONCISE - no planning text, no process explanations\n" 
            "- Start directly with your analysis\n" 
            "- Analyze ONLY the news headlines provided\n" 
            "- If no news is available, state this clearly\n" 
            "- Do NOT invent news events"
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
            "You are a senior equity research director. You receive reports from three " 
            "specialists and synthesize them into a coherent explanation.\n\n" 
            "CRITICAL RULES:\n" 
            "- Be CONCISE - no planning text, no 'I will', no process explanations\n" 
            "- Start directly with '## Executive Summary'\n" 
            "- Focus on PRIMARY drivers only\n" 
            "- Use ONLY the inputs from your three analysts\n" 
            "- Do NOT add new data or speculation"
        ),
        verbose=False,  # Avoid recursion issues
        allow_delegation=False,
        llm=llm,
    )
    
    return agent