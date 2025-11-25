"""
tasks.py

Defines the specific tasks that agents will perform.

What's a task?
A task is a specific job with clear instructions, expected input, and desired output format.
It's like giving detailed instructions to an employee.
"""

from crewai import Task


def create_explainer_task(agent, context_str: str):
    """
    Create a task for the Explainer agent to analyze a recommendation.
    
    Args:
        agent: The Explainer agent who will perform this task
        context_str: The formatted context string with IBES, FUND, and NEWS data
        
    Returns:
        Task: A CrewAI task that produces a structured explanation
    """
    
    task = Task(
        description=f"""
Analyze the following analyst recommendation context and provide a comprehensive explanation 
for why the analyst likely issued this rating (BUY/HOLD/SELL/etc.).

===== CONTEXT TO ANALYZE =====
{context_str}
===============================

Your task is to:

1. **Examine the recommendation**: What rating did the analyst give? (BUY/SELL/HOLD/etc.)

2. **Analyze price action**: Look at recent price movements, returns, and volume patterns. 
   Did the stock show momentum, reversal, volatility spikes, or unusual volume?

3. **Review fundamentals**: Examine any available EPS, ROE, leverage, or cash flow metrics. 
   Are they strong, weak, improving, or deteriorating?

4. **Map news to rating**: For each news headline, assess whether it's positive, negative, 
   or neutral, and how it might influence the analyst's view.

5. **Synthesize the rationale**: Explain the most likely reasons the analyst gave this rating, 
   citing specific data points from the context.

6. **Assess consistency**: Does the data support the rating, or are there contradictions?

7. **Provide a confidence score**: Rate your confidence (0-100) in this explanation based on 
   data completeness and consistency.

CRITICAL INSTRUCTIONS:
- Use ONLY the data provided above—do not invent facts or reference external events
- If data is missing or marked as "N/A", explicitly acknowledge this limitation
- Be specific: cite actual numbers (prices, returns, dates) from the context
- If you're uncertain about something, say so clearly
- Do not predict future performance—focus only on explaining the rating
        """,
        
        expected_output="""
A structured markdown explanation with the following sections:

## Summary
<1-2 sentences: what rating was given and the primary reason>

## Detailed Rationale

### Positive Drivers
<Bullet points of factors supporting a positive view>

### Negative Factors / Risks
<Bullet points of concerns or headwinds>

### Valuation & Price Action
<Analysis of recent price movements and what they suggest>

### Fundamental Analysis
<Discussion of EPS, ROE, leverage, cash flows if available>

## News Mapping
<For each news item, explain its likely impact: positive/negative/neutral>

## Consistency Assessment
- **Rating-Data Alignment**: <Does the available data support this rating?>
- **Confidence Score**: <0-100> - <Brief reasoning for this confidence level>
- **Data Limitations**: <What key information is missing?>

## Conclusion
<Final 2-3 sentence synthesis of why this rating makes sense given the data>
        """,
        
        agent=agent,
    )
    
    return task