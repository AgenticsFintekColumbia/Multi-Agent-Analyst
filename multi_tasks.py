"""
multi_tasks.py

Defines CrewAI Tasks for the multi-agent Recommender pipeline:
- fundamental_task
- technical_task
- news_task
- recommender_manager_task (NEW - synthesizes all three)
"""

from crewai import Task
from multi_agents import (
    fundamental_agent,
    technical_agent,
    news_agent,
    recommender_manager,
)


# ============================================================================
# SPECIALIST ANALYST TASKS (improved with stricter output formats)
# ============================================================================

fundamental_task = Task(
    description=(
        "You are the Fundamental Analyst.\n\n"
        "Analyze the provided fundamentals dictionary strictly as given.\n\n"
        "Fundamental data:\n"
        "{{fundamentals}}\n\n"
        "Your job:\n"
        "1. Analyze earnings quality (EPS growth, stability)\n"
        "2. Assess profitability (ROE, margins)\n"
        "3. Evaluate balance sheet health (leverage, debt ratios)\n"
        "4. Review cash flow generation (FCF, OCF)\n"
        "5. Consider valuation signals if available\n\n"
        "OUTPUT FORMAT (strict):\n\n"
        "## Fundamental Analysis\n\n"
        "### Rating\n"
        "- **Fundamental Rating**: <ONE of: StrongBuy, Buy, Hold, UnderPerform, Sell>\n"
        "- **Confidence**: <High/Medium/Low>\n\n"
        "### Key Signals\n"
        "- **Positive**: <list key positive metrics>\n"
        "- **Negative**: <list key negative metrics>\n"
        "- **Neutral/Missing**: <any missing or neutral data>\n\n"
        "### Reasoning\n"
        "<2-3 sentences explaining your rating based ONLY on the data provided>\n\n"
        "CONSTRAINTS:\n"
        "- Start with '## Fundamental Analysis'\n"
        "- Use ONLY data provided in {{fundamentals}}\n"
        "- Choose ONE clear rating"
    ),
    expected_output=(
        "Markdown starting with '## Fundamental Analysis' containing "
        "rating, confidence, key signals, and reasoning."
    ),
    agent=fundamental_agent,
)


technical_task = Task(
    description=(
        "You are the Technical Analyst.\n\n"
        "Analyze the following technical indicators strictly as provided.\n\n"
        "Technical data:\n"
        "{{technicals}}\n\n"
        "Your job:\n"
        "1. Assess momentum (recent returns, trend direction)\n"
        "2. Evaluate technical indicators (RSI, MACD)\n"
        "3. Analyze volume patterns\n"
        "4. Assess volatility and risk\n\n"
        "OUTPUT FORMAT (strict):\n\n"
        "## Technical Analysis\n\n"
        "### Rating\n"
        "- **Technical Rating**: <ONE of: StrongBuy, Buy, Hold, UnderPerform, Sell>\n"
        "- **Confidence**: <High/Medium/Low>\n\n"
        "### Key Signals\n"
        "- **Bullish**: <list bullish technical signals>\n"
        "- **Bearish**: <list bearish technical signals>\n"
        "- **Neutral**: <any neutral or mixed signals>\n\n"
        "### Reasoning\n"
        "<2-3 sentences explaining your rating based on momentum, indicators, and volume>\n\n"
        "CONSTRAINTS:\n"
        "- Start with '## Technical Analysis'\n"
        "- Use ONLY data provided in {{technicals}}\n"
        "- Choose ONE clear rating"
    ),
    expected_output=(
        "Markdown starting with '## Technical Analysis' containing "
        "rating, confidence, key signals, and reasoning."
    ),
    agent=technical_agent,
)


news_task = Task(
    description=(
        "You are the News & Sentiment Analyst.\n\n"
        "Analyze the following news JSON:\n\n"
        "{{news}}\n\n"
        "Your job:\n"
        "1. Map each news item to sentiment (positive/negative/neutral)\n"
        "2. Identify major catalysts\n"
        "3. Assess overall sentiment tone\n"
        "4. Consider market impact\n\n"
        "OUTPUT FORMAT (strict):\n\n"
        "## News & Sentiment Analysis\n\n"
        "### Rating\n"
        "- **News-Based Rating**: <ONE of: StrongBuy, Buy, Hold, UnderPerform, Sell>\n"
        "- **Confidence**: <High/Medium/Low>\n\n"
        "### Sentiment Breakdown\n"
        "- **Positive News**: <count and brief description>\n"
        "- **Negative News**: <count and brief description>\n"
        "- **Neutral News**: <count and brief description>\n\n"
        "### Major Catalysts\n"
        "- <list 2-3 most significant news items if any>\n\n"
        "### Reasoning\n"
        "<2-3 sentences explaining your rating based on overall sentiment and catalysts>\n\n"
        "CONSTRAINTS:\n"
        "- Start with '## News & Sentiment Analysis'\n"
        "- If no news provided, state this and default to Hold\n"
        "- Choose ONE clear rating"
    ),
    expected_output=(
        "Markdown starting with '## News & Sentiment Analysis' containing "
        "rating, confidence, sentiment breakdown, and reasoning."
    ),
    agent=news_agent,
)


# ============================================================================
# MANAGER TASK (NEW)
# ============================================================================

def create_recommender_manager_task(
    fundamental_report: str,
    technical_report: str,
    news_report: str,
    stock_info: str = "",
) -> Task:
    """
    Create the Recommender Manager task to synthesize all three analyst reports.
    
    Args:
        fundamental_report: Output from fundamental_task
        technical_report: Output from technical_task
        news_report: Output from news_task
        stock_info: Optional context about the stock (ticker, date, etc.)
    
    Returns:
        Task for the recommender_manager agent
    """
    
    description = f"""
You are the Portfolio Manager synthesizing three analyst reports into a final 
investment recommendation.

{stock_info}

FUNDAMENTAL ANALYST REPORT:
{fundamental_report}

TECHNICAL ANALYST REPORT:
{technical_report}

NEWS ANALYST REPORT:
{news_report}

Your job:
1. Extract the rating from each analyst: StrongBuy/Buy/Hold/UnderPerform/Sell
2. Assess the confidence level from each analyst
3. Identify signal alignment (do they agree or disagree?)
4. Apply your weighting logic based on:
   - Signal strength (high confidence signals get more weight)
   - Data quality (missing data reduces weight)
   - Market context (which signals are most relevant?)
5. Make your final decision: ONE rating from {{StrongBuy, Buy, Hold, UnderPerform, Sell}}
6. Explain your weighting and synthesis logic clearly

OUTPUT FORMAT (strict):

## Model Recommendation (Final)

### Final Rating
- **Model Rating**: <ONE of: StrongBuy, Buy, Hold, UnderPerform, Sell>
- **Overall Confidence**: <High/Medium/Low>

### Analyst Ratings Summary
- **Fundamental**: <rating> (confidence: <level>)
- **Technical**: <rating> (confidence: <level>)
- **News**: <rating> (confidence: <level>)

### Signal Alignment
- **Agreement Level**: <All Agree / Majority Agree / Split / All Disagree>
- **Dominant Signal**: <Which analyst's view is most compelling and why>

### Weighting Logic
<Explain how you weighted each analyst's input. For example:>
- Fundamental: <weight>% because <reason>
- Technical: <weight>% because <reason>
- News: <weight>% because <reason>

### Synthesis
<3-4 sentences explaining your final decision. Address:>
- Why this rating makes sense given all three inputs
- How you resolved any contradictions
- What risk factors or uncertainties remain

### Risk Assessment
- **Primary Risk**: <biggest downside risk>
- **Data Quality**: <any missing or unreliable data that affects confidence>

CONSTRAINTS:
- Start with '## Model Recommendation (Final)'
- Choose ONE clear final rating
- Be explicit about your weighting logic
- Use ONLY information from the three analyst reports provided
"""
    
    return Task(
        description=description,
        agent=recommender_manager,
        expected_output=(
            "Markdown starting with '## Model Recommendation (Final)' containing "
            "final rating, analyst summary, alignment analysis, weighting logic, "
            "synthesis, and risk assessment."
        ),
    )