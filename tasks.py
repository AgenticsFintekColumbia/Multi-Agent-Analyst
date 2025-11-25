"""
tasks.py

Defines the CrewAI tasks for:
- Explainer agent: explain why the analyst gave a rating.
- Recommender agent: issue its own BUY/HOLD/SELL-style rating (this is now not being used, i had one there just as a placeholder
"""

from crewai import Task


def create_explainer_task(agent, context_str: str) -> Task:
    """
    Create the Explainer task for a given agent and context.

    The agent must output a structured markdown explanation of the analyst's rating.
    """

    description = f"""
Analyze the following analyst recommendation context and produce a structured
markdown explanation.

You are a senior sell-side equity analyst. You must ONLY use the information
provided in the context block and must not invent any additional data.

================== CONTEXT START ==================
{context_str}
=================== CONTEXT END ===================

Your job:

1. Examine the IBES recommendation (code/text).
2. Analyze recent price action and volume (from FUND).
3. Interpret any available fundamentals (EPS, ROE, leverage, cash-flow metrics).
   If they are missing or "N/A", explicitly say that.
4. Map each news headline to its likely impact (positive/negative/neutral) on
   the analyst's view.
5. Synthesize a coherent rationale for why the analyst likely issued this rating.
6. Assess whether the data is consistent with the rating.
7. Provide a numerical confidence score (0–100) with a one-sentence justification.

OUTPUT FORMAT (very important):

Return your answer as markdown in exactly this structure:

## Summary
<1–3 sentences explaining the overall rationale>

## Detailed Rationale
- **Positive drivers**
  - ...
- **Negative factors / risks**
  - ...
- **Valuation / price action considerations**
  - ...

## News Mapping
- "<headline 1>" → impact assessment and reasoning
- "<headline 2>" → impact assessment and reasoning
- ...

## Consistency & Confidence
- Consistency: <brief sentence on whether data aligns with the rating>
- Confidence score (0–100): <number> – <short reason>

Constraints:
- Do NOT include any preamble like "I will follow these steps" or
  "Let me analyze".
- Do NOT describe your internal process or steps.
- Start your response directly with the "## Summary" heading.
- Do NOT add extra sections or headings beyond what is specified above.
"""

    return Task(
        description=description,
        agent=agent,
        expected_output=(
            "A markdown report in the exact structure described above, "
            "starting with '## Summary' and containing only the specified sections."
        ),
    )

#this was a placeholder the multi agent approach vinod devloped is now being used
def create_recommender_task(agent, context_str: str) -> Task:
    """
    Create the Recommender task for a given agent and context.

    The agent must output its OWN rating (not just repeat IBES), chosen from
    {STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL}, plus confidence and short rationale.
    """

    description = f"""
You are a senior sell-side equity analyst issuing your OWN recommendation.

You are given contextual data about a stock (IBES info, FUND data, NEWS headlines).
The IBES section may contain an existing analyst rating, but you should form your
OWN independent view strictly based on the data in the context.

================== CONTEXT START ==================
{context_str}
=================== CONTEXT END ===================

Your job:

1. Read the entire context carefully.
2. Form your own view on whether the stock deserves a rating of:
   - STRONG_BUY
   - BUY
   - HOLD
   - SELL
   - STRONG_SELL
3. Consider price momentum, volatility, fundamentals, and news flow.
4. Balance positive drivers vs risks.
5. Assign a confidence score between 0 and 100.
6. Provide a concise rationale.

IMPORTANT:
- You MUST choose exactly ONE rating from the set above.
- You MUST output the rating in a machine-readable way for downstream parsing.
- Do NOT hedge by listing multiple ratings; pick the single best one.
- Do NOT describe your internal process or steps.

OUTPUT FORMAT (strict):

Return your answer as markdown with exactly this structure:

## Recommendation
- Model rating: <ONE of STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL>
- Confidence (0–100): <integer from 0 to 100>

## Rationale
- <bullet point 1>
- <bullet point 2>
- <bullet point 3> (optional)

Constraints:
- Start your output with the '## Recommendation' heading.
- Do NOT include any text before '## Recommendation'.
- Do NOT add extra sections beyond '## Recommendation' and '## Rationale'.
- Use only the data from the context; do not reference external information.
"""

    return Task(
        description=description,
        agent=agent,
        expected_output=(
            "Markdown starting with '## Recommendation' and containing "
            "the specified bullet points and rationale."
        ),
    )
