"""
multi_explainer_tasks.py

Defines the tasks for the multi-agent Explainer team:
- Fundamental analysis task
- Technical analysis task  
- News analysis task
- Manager synthesis task
"""

from crewai import Task


def create_fundamental_explainer_task(agent, fundamental_data: str) -> Task:
    """
    Task for the Fundamental Analyst to analyze fundamental data.
    
    Input: A structured string containing fundamental metrics.
    Output: Analysis of how fundamentals influenced the analyst's rating.
    """
    description = f"""
Analyze fundamental data to explain how it influenced a human analyst's stock recommendation.

FUNDAMENTAL DATA:
{fundamental_data}

OUTPUT FORMAT (be concise, no planning text, start immediately):

## Fundamental Analysis

**Positive Signals:**
- <metric>: <value> → <1 sentence why bullish>
- ...

**Negative Signals:**
- <metric>: <value> → <1 sentence why bearish>
- ...

**Missing Data:**
- <list missing metrics: "ROA: Not available", "D/E Ratio: Not provided">

**Summary:** <1 sentence: Do fundamentals support BUY, SELL, or NEUTRAL?>

CONSTRAINTS:
- NO planning text - start directly with "## Fundamental Analysis"
- NO "I will", "Here's my plan", or process explanations
- If data is N/A, state it explicitly
- Do NOT invent numbers
"""
    
    return Task(
        description=description,
        agent=agent,
        expected_output=(
            "Markdown starting with '## Fundamental Analysis' containing the specified sections"
        ),
    )


def create_technical_explainer_task(agent, technical_data: str) -> Task:
    """
    Task for the Technical Analyst to analyze price/technical data.
    
    Input: A structured string containing price action and technical indicators.
    Output: Analysis of how technicals influenced the analyst's rating.
    """
    description = f"""
Analyze technical/price data to explain how it influenced a human analyst's stock recommendation.

TECHNICAL DATA:
{technical_data}

OUTPUT FORMAT (be concise, no planning text, start immediately):

## Technical Analysis

**Price Momentum:** <1 sentence: recent trend, period return, direction>

**Volume:** <1 sentence: volume patterns and what they indicate>

**Indicators:**
- <indicator>: <value> → <brief interpretation>
- If none: "No technical indicators available"

**Summary:** <1 sentence: Do technicals support BUY, SELL, or NEUTRAL?>

CONSTRAINTS:
- NO planning text - start directly with "## Technical Analysis"
- NO "Here's a plan" or process explanations
- Use ONLY the data provided
- Do NOT invent price levels or indicators
"""
    
    return Task(
        description=description,
        agent=agent,
        expected_output=(
            "Markdown starting with '## Technical Analysis' containing the specified sections"
        ),
    )


def create_news_explainer_task(agent, news_data: str) -> Task:
    """
    Task for the News Analyst to analyze news headlines.
    
    Input: A structured string containing news headlines and dates.
    Output: Analysis of how news flow influenced the analyst's rating.
    """
    description = f"""
Analyze news headlines to explain how they influenced a human analyst's stock recommendation.

NEWS DATA (summarized feed of recent headlines and events):
{news_data}

OUTPUT FORMAT (be concise, no planning text, start immediately):

## News Analysis

### Sentiment Overview
- Overall news tone over the window: **Positive / Negative / Mixed / Neutral**
- 1–2 sentences summarizing how the news flow likely affected the analyst's conviction.

### Major Catalysts (3–5 bullets, no more)
- <brief description of a major catalyst and its impact on the stock, grouped by theme rather than by date>
- <only include events that clearly move sentiment or risk>
- If none: "No major catalysts identified in this window."

### Secondary Signals (Optional, at most 3 bullets)
- <other notable but less material headlines or patterns>
- If not needed: omit this section.

### Summary
- 1–2 sentences: Does news flow overall support BUY, SELL, or NEUTRAL? Mention direction and confidence.

CONSTRAINTS:
- NO planning text - start directly with "## News Analysis"
- Do NOT list every article or date individually; aggregate headlines into themes.
- Maximum of 8 bullets total across all lists.
- If no news: "No news data available for this time window."
- Analyze ONLY the news provided.
"""
    
    return Task(
        description=description,
        agent=agent,
        expected_output=(
            "Markdown starting with '## News Analysis' containing the specified sections"
        ),
    )


def create_explainer_manager_task(
    agent,
    ibes_info: str,
    fundamental_report: str,
    technical_report: str,
    news_report: str,
) -> Task:
    """
    Task for the Explainer Manager to synthesize all three analyst reports.
    
    Input: Reports from Fundamental, Technical, and News analysts.
    Output: Comprehensive explanation of why the human analyst gave their rating.
    """
    description = f"""
Synthesize reports from three specialist analysts to explain why a human analyst gave a specific stock recommendation.

IBES RECOMMENDATION INFO:
{ibes_info}

FUNDAMENTAL ANALYST REPORT:
{fundamental_report}

TECHNICAL ANALYST REPORT:
{technical_report}

NEWS ANALYST REPORT:
{news_report}

OUTPUT FORMAT (be concise, no planning text, start immediately):

## Executive Summary
<2 sentences: Why did the analyst give this rating?>

## Key Drivers

**Positive Factors:**
- <key positive>
- ...

**Negative Factors:**
- <key negative>
- ...

**Mixed/Neutral:**
- <contradictory signals or missing data>

## Analyst Perspective
<2 sentences: How would a human analyst weigh these factors?>

## Confidence
**Score:** <number>/100
**Reason:** <1 sentence>

CONSTRAINTS:
- NO planning text - start directly with "## Executive Summary"
- NO "I will" or process explanations
- Use ONLY information from the three analyst reports
- Do NOT add external information
"""
    
    return Task(
        description=description,
        agent=agent,
        expected_output=(
            "Markdown starting with '## Executive Summary' containing the specified sections"
        ),
    )