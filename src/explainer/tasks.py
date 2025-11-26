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
You are analyzing fundamental data to explain how it influenced a human analyst's 
stock recommendation.

FUNDAMENTAL DATA:
{fundamental_data}

Your job:
1. Analyze the fundamental metrics provided (EPS, ROE, leverage, cash flows, etc.)
2. Identify which metrics are POSITIVE signals (support a BUY/STRONG_BUY)
3. Identify which metrics are NEGATIVE signals (support a SELL/STRONG_SELL)
4. Identify which metrics are NEUTRAL or missing
5. Explain how these metrics would logically influence an analyst's rating

OUTPUT FORMAT (strict):

Return markdown with this structure:

## Fundamental Analysis

### Positive Signals
- <metric>: <value> → <explanation of why this supports a bullish view>
- ...

### Negative Signals  
- <metric>: <value> → <explanation of why this supports a bearish view>
- ...

### Neutral/Missing Data
- <what data is missing or neutral>

### Overall Fundamental Assessment
<2-3 sentences summarizing whether fundamentals support a positive, negative, or neutral rating>

CONSTRAINTS:
- Use ONLY the data provided above
- If a metric is N/A or missing, say so explicitly
- Do NOT invent numbers
- Start your response with "## Fundamental Analysis"
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
You are analyzing technical/price data to explain how it influenced a human analyst's 
stock recommendation.

TECHNICAL DATA:
{technical_data}

Your job:
1. Analyze recent price movements and trends
2. Identify momentum signals (positive/negative)
3. Analyze volume patterns (unusual activity, confirmation signals)
4. Interpret any technical indicators provided (RSI, moving averages, etc.)
5. Explain how these technical factors would influence an analyst's rating

OUTPUT FORMAT (strict):

Return markdown with this structure:

## Technical Analysis

### Price Momentum
- <analysis of recent price trends, returns, and momentum>

### Volume Analysis
- <analysis of volume patterns and what they signal>

### Technical Indicators
- <analysis of any technical indicators provided>
- If no indicators provided, state: "No technical indicators available in data"

### Overall Technical Assessment
<2-3 sentences summarizing whether technicals support a positive, negative, or neutral rating>

CONSTRAINTS:
- Use ONLY the data provided above
- Do NOT invent price levels or indicators
- Start your response with "## Technical Analysis"
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
You are analyzing news headlines to explain how they influenced a human analyst's 
stock recommendation.

NEWS DATA:
{news_data}

Your job:
1. Map each news headline to its likely sentiment impact (POSITIVE/NEGATIVE/NEUTRAL)
2. Identify major catalysts (earnings, product launches, legal issues, etc.)
3. Assess the overall news tone around the recommendation date
4. Explain how this news flow would influence an analyst's rating decision

OUTPUT FORMAT (strict):

Return markdown with this structure:

## News Analysis

### Individual News Impact
- **[Date]** "<headline>" → POSITIVE/NEGATIVE/NEUTRAL: <brief explanation>
- **[Date]** "<headline>" → POSITIVE/NEGATIVE/NEUTRAL: <brief explanation>
- ...

### Major Catalysts
- <identify any major news events that would significantly impact the rating>
- If none, state: "No major catalysts identified in the news window"

### Overall News Sentiment
<2-3 sentences summarizing whether the news flow supports a positive, negative, or neutral rating>

CONSTRAINTS:
- Analyze ONLY the news headlines provided above
- Do NOT invent news events
- If no news is available, state this clearly
- Start your response with "## News Analysis"
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
You are synthesizing reports from three specialist analysts to explain why a human 
analyst gave a specific stock recommendation.

IBES RECOMMENDATION INFO:
{ibes_info}

FUNDAMENTAL ANALYST REPORT:
{fundamental_report}

TECHNICAL ANALYST REPORT:
{technical_report}

NEWS ANALYST REPORT:
{news_report}

Your job:
1. Read all three specialist reports carefully
2. Identify the PRIMARY drivers of the analyst's rating
3. Synthesize fundamental, technical, and news factors into a coherent narrative
4. Assess whether all three factors point in the same direction (consistency check)
5. Provide an overall confidence score for the explanation

OUTPUT FORMAT (strict):

Return markdown with this structure:

## Executive Summary
<2-3 sentences explaining the overall rationale for the analyst's rating>

## Key Drivers of the Rating

### Primary Positive Factors
- <synthesize positive signals from all three reports>

### Primary Negative Factors
- <synthesize negative signals from all three reports>

### Mixed/Neutral Factors
- <any contradictory or neutral signals>

## Analyst Perspective Synthesis
<3-4 sentences explaining how a human analyst would weigh fundamental vs technical vs news factors for THIS specific rating>

## Consistency Check
- **Data Alignment**: <Do fundamental, technical, and news all point the same direction?>
- **Internal Logic**: <Does the rating make sense given the data?>
- **Data Quality**: <Any missing or unreliable data that weakens the explanation?>

## Confidence Assessment
- **Confidence Score (0-100)**: <number>
- **Justification**: <1-2 sentences explaining the confidence level>

CONSTRAINTS:
- Use ONLY the information from the three analyst reports above
- Do NOT add new data or external information
- Start your response with "## Executive Summary"
"""
    
    return Task(
        description=description,
        agent=agent,
        expected_output=(
            "Markdown starting with '## Executive Summary' containing the specified sections"
        ),
    )