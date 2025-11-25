"""
multi_tasks.py

Defines CrewAI Tasks for the multi-agent Recommender pipeline:
- fundamental_task
- technical_task
- news_task

There is no Portfolio Manager LLM anymore, combination is done in Python.
"""

from crewai import Task
from multi_agents import fundamental_agent, technical_agent, news_agent

# Fundamental Task
fundamental_task = Task(
    description=(
        "You are the Fundamental Analyst.\n\n"
        "Analyze the provided fundamentals dictionary strictly as given.\n\n"
        "Fundamental data:\n"
        "{{fundamentals}}\n\n"
        "Output:\n"
        "- A fundamentals rating: StrongBuy / Buy / Hold / UnderPerform / Sell\n"
        "- Brief reasoning tied directly to the data provided."
    ),
    expected_output="Fundamental rating + reasoning.",
    agent=fundamental_agent,
)

# Technical Task
technical_task = Task(
    description=(
        "You are the Technical Analyst.\n\n"
        "Analyze the following technical indicators strictly as provided.\n\n"
        "Technical data:\n"
        "{{technicals}}\n\n"
        "Output:\n"
        "- Technical rating: StrongBuy / Buy / Hold / UnderPerform / Sell\n"
        "- Short reasoning referencing momentum, trend, MACD, RSI, volume, etc."
    ),
    expected_output="Technical rating + reasoning.",
    agent=technical_agent,
)

# News Task
news_task = Task(
    description=(
        "You are the News & Sentiment Analyst.\n\n"
        "Analyze the following news JSON:\n\n"
        "{{news}}\n\n"
        "Output:\n"
        "- News sentiment classification\n"
        "- 2–4 bullet points summarizing key events\n"
        "- A news-based rating: StrongBuy / Buy / Hold / UnderPerform / Sell"
    ),
    expected_output="News sentiment rating + reasoning.",
    agent=news_agent,
)
