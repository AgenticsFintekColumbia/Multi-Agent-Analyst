# Recommender Team Architecture - Technical Documentation

## Overview

The Recommender team is a multi-agent system that generates **an independent AI rating recommendation** for a stock. Unlike the Explainer (which explains human decisions), the Recommender makes its own investment decision by intelligently synthesizing three specialist analyst ratings.

**Key Innovation:** The Portfolio Manager uses an LLM-based synthesis algorithm instead of simple voting, allowing it to weigh signals by confidence, handle contradictions, and adapt to market context.

---

## System Architecture

### Agent Hierarchy

```
                Portfolio Manager
               (Synthesis Agent)
                        |
         +--------------+--------------+
         |              |              |
   Fundamental      Technical       News
    Analyst          Analyst       Analyst
    (Agent 1)       (Agent 2)      (Agent 3)
         |              |              |
    Analyzes        Analyzes      Analyzes
   Financials      Price Data    Headlines
         |              |              |
    Returns         Returns       Returns
     RATING          RATING        RATING
   + Report        + Report      + Report
         |              |              |
         +--------------+--------------+
                        |
                        v
              Portfolio Manager
              Synthesizes Ratings
              (Intelligent Weighting)
                        |
                        v
              Final Model Rating
              + Confidence Score
              + Weighting Logic
```

### Key Design Principles

1. **Independent Ratings** - Each specialist makes their own rating decision
2. **Intelligent Synthesis** - Manager weighs ratings by confidence, not simple majority
3. **Context-Aware** - Manager adapts weighting based on market conditions
4. **Transparent Reasoning** - Explicit weighting logic and rationale

---

## Code Structure

### File Organization

```
src/recommender/
├── __init__.py          # Exports main orchestrator function
├── agents.py            # Agent definitions (4 agents)
├── tasks.py             # Task definitions for each agent
└── orchestrator.py      # Main execution flow and data extraction
```

### Module Responsibilities

- **`agents.py`**: Defines 4 CrewAI agents with roles, goals, backstories, and shared LLM instance
- **`tasks.py`**: Defines structured tasks with strict output format requirements for ratings
- **`orchestrator.py`**: Coordinates data extraction, agent execution, and result assembly

---

## Agent Definitions (`agents.py`)

All agents share a **single LLM instance** (Google Gemini 2.5 Flash) configured once for consistency.

### LLM Configuration

```python
def _build_gemini_llm(model: str = "gemini-2.5-flash", temperature: float = 0.2) -> LLM:
    api_key = _get_gemini_api_key()
    llm = LLM(model=model, api_key=api_key, temperature=temperature)
    return llm

_llm = _build_gemini_llm()  # Shared instance for all agents
```

**Configuration:**
- **Model:** `gemini-2.5-flash`
- **Temperature:** 0.2 (lower than Explainer for more consistent ratings)
- **Shared Instance:** All agents use same LLM instance for consistency

---

### 1. Fundamental Analyst

**File:** `src/recommender/agents.py::fundamental_agent`

**Purpose:** Makes an independent rating based solely on fundamental financial metrics.

**Configuration:**
- **Role:** "Fundamental Analyst"
- **Goal:** Strictly evaluate fundamentals (EPS, ROE, margins, revenue growth, cash flow, leverage, debt quality, liquidity, FCF, valuation ratios). Do NOT analyze technical indicators or news.
- **Temperature:** 0.2 (via shared LLM)
- **Key Constraints:**
  - Must focus ONLY on fundamentals
  - Cannot consider technical or news signals
  - Must output a clear rating (StrongBuy/Buy/Hold/UnderPerform/Sell)

**Input:** Dictionary of fundamental metrics (from orchestrator data extraction)

**Output:** Structured markdown with:
  - Rating (one of: StrongBuy, Buy, Hold, UnderPerform, Sell)
  - Confidence (High/Medium/Low)
  - Key Signals (Positive/Negative/Neutral)
  - Reasoning

**Data Focus:**
- Earnings quality (EPS growth, stability)
- Profitability (ROE, margins)
- Balance sheet health (leverage, debt ratios)
- Cash flow generation (FCF, OCF)
- Valuation signals

---

### 2. Technical Analyst

**File:** `src/recommender/agents.py::technical_agent`

**Purpose:** Makes an independent rating based solely on technical indicators and price action.

**Configuration:**
- **Role:** "Technical Analyst"
- **Goal:** Strictly analyze technical indicators such as RSI, MACD, SMA/EMA, momentum, ATR, volatility, and price patterns. Ignore all fundamentals and news.
- **Temperature:** 0.2
- **Key Constraints:**
  - Must focus ONLY on technicals
  - Cannot consider fundamental or news signals
  - Must output a clear rating

**Input:** Dictionary of technical indicators (from orchestrator data extraction)

**Output:** Structured markdown with:
  - Rating
  - Confidence
  - Key Signals (Bullish/Bearish/Neutral)
  - Reasoning

**Data Focus:**
- Momentum (recent returns, trend direction)
- Technical indicators (RSI, MACD)
- Volume patterns
- Volatility and risk

---

### 3. News Analyst

**File:** `src/recommender/agents.py::news_agent`

**Purpose:** Makes an independent rating based solely on news sentiment and catalysts.

**Configuration:**
- **Role:** "News & Sentiment Analyst"
- **Goal:** Strictly analyze sentiment from historical news articles. Assess tone, impact, risk, and market-moving implications. Do NOT evaluate fundamentals or technical indicators.
- **Temperature:** 0.2
- **Key Constraints:**
  - Must focus ONLY on news sentiment
  - Cannot consider fundamental or technical signals
  - Must output a clear rating (defaults to Hold if no news)

**Input:** JSON array of news headlines (from orchestrator data extraction)

**Output:** Structured markdown with:
  - Rating
  - Confidence
  - Sentiment Breakdown (Positive/Negative/Neutral counts)
  - Major Catalysts
  - Reasoning

**Data Focus:**
- Sentiment mapping (positive/negative/neutral per headline)
- Major catalysts (earnings, product launches, legal issues)
- Overall sentiment tone
- Market impact assessment

---

### 4. Portfolio Manager

**File:** `src/recommender/agents.py::recommender_manager`

**Purpose:** Synthesizes all three specialist ratings into a final model recommendation using intelligent weighting.

**Configuration:**
- **Role:** "Portfolio Manager & Rating Synthesizer"
- **Goal:** Synthesize ratings from three specialists into a single coherent model recommendation with explicit weighting logic.
- **Temperature:** 0.2
- **Backstory:** Veteran portfolio manager with 25+ years experience. Understands:
  - Different market regimes favor different signals
  - Must weigh strength of each analyst's conviction
  - Identifies and resolves contradictions
  - Prioritizes risk management
  - Provides confidence scores

**Key Capabilities:**
- **Adaptive Weighting:** Adjusts weights based on confidence levels
- **Context-Aware:** Understands market conditions (e.g., crisis periods favor technicals)
- **Transparent Logic:** Explicitly explains weighting decisions
- **Risk-Aware:** Acknowledges uncertainties and data quality

**Input:** All three analyst reports + stock context

**Output:** Structured markdown with:
  - Final Model Rating
  - Overall Confidence (High/Medium/Low)
  - Analyst Ratings Summary
  - Signal Alignment (Agreement Level)
  - Weighting Logic (explicit percentages)
  - Synthesis (rationale)
  - Risk Assessment

**This is the key innovation:** Instead of simple voting, the manager intelligently weighs conflicting signals.

---

## Task Definitions (`tasks.py`)

Tasks enforce **strict output formats** to ensure ratings can be reliably parsed.

### Task Structure

All specialist tasks follow this pattern:

```python
task = Task(
    description="[Detailed instructions with output format]",
    expected_output="[Brief description]",
    agent=[agent_instance],
)
```

### 1. Fundamental Task

**File:** `src/recommender/tasks.py::fundamental_task`

**Input Format:** Dictionary of fundamental metrics (injected via `{{fundamentals}}` placeholder)

**Output Format:**
```markdown
## Fundamental Analysis

### Rating
- **Fundamental Rating**: <StrongBuy/Buy/Hold/UnderPerform/Sell>
- **Confidence**: <High/Medium/Low>

### Key Signals
- **Positive**: <list>
- **Negative**: <list>
- **Neutral/Missing**: <list>

### Reasoning
<2-3 sentences>
```

**Constraints:**
- Must start with "## Fundamental Analysis"
- Must use ONLY provided data
- Must choose ONE clear rating

---

### 2. Technical Task

**File:** `src/recommender/tasks.py::technical_task`

**Input Format:** Dictionary of technical indicators (injected via `{{technicals}}` placeholder)

**Output Format:**
```markdown
## Technical Analysis

### Rating
- **Technical Rating**: <StrongBuy/Buy/Hold/UnderPerform/Sell>
- **Confidence**: <High/Medium/Low>

### Key Signals
- **Bullish**: <list>
- **Bearish**: <list>
- **Neutral**: <list>

### Reasoning
<2-3 sentences>
```

**Constraints:**
- Must start with "## Technical Analysis"
- Must use ONLY provided technical data
- Must choose ONE clear rating

---

### 3. News Task

**File:** `src/recommender/tasks.py::news_task`

**Input Format:** JSON array of news items (injected via `{{news}}` placeholder)

**Output Format:**
```markdown
## News & Sentiment Analysis

### Rating
- **News-Based Rating**: <StrongBuy/Buy/Hold/UnderPerform/Sell>
- **Confidence**: <High/Medium/Low>

### Sentiment Breakdown
- **Positive News**: <count and description>
- **Negative News**: <count and description>
- **Neutral News**: <count and description>

### Major Catalysts
- <list 2-3 significant items>

### Reasoning
<2-3 sentences>
```

**Constraints:**
- Must start with "## News & Sentiment Analysis"
- If no news provided, defaults to Hold
- Must choose ONE clear rating

---

### 4. Manager Task

**File:** `src/recommender/tasks.py::create_recommender_manager_task()`

**Input:** All three analyst reports + stock info (passed as function arguments)

**Output Format:**
```markdown
## Model Recommendation (Final)

### Final Rating
- **Model Rating**: <StrongBuy/Buy/Hold/UnderPerform/Sell>
- **Overall Confidence**: <High/Medium/Low>

### Analyst Ratings Summary
- **Fundamental**: <Rating> (<Confidence>)
- **Technical**: <Rating> (<Confidence>)
- **News**: <Rating> (<Confidence>)

### Signal Alignment
- **Agreement Level**: <Strong Agreement/Agreement/Split/Strong Disagreement>
- **Dominant Signal**: <which analyst's view dominates>

### Weighting Logic
- **Fundamental**: X% - <reasoning>
- **Technical**: Y% - <reasoning>
- **News**: Z% - <reasoning>
(Note: X + Y + Z = 100%)

### Synthesis
<Detailed rationale for final decision, considering confidence levels and market context>

### Risk Assessment
- **Primary Risk**: <main risk factor>
- **Data Quality**: <assessment of data completeness>
```

**Constraints:**
- Must extract ratings from each analyst report
- Must provide explicit weighting percentages
- Must explain synthesis logic
- Must acknowledge uncertainties

---

## Orchestration Flow (`orchestrator.py`)

The orchestrator is the main entry point: `run_multi_analyst_recommendation()`

### Execution Steps

#### Step 1: Data Extraction

```python
# Extract recommendation from IBES
rec = ibes.iloc[rec_index]
cusip = rec.get("cusip")
rec_date = rec.get("anndats")

# Extract FUND data (fundamentals + technicals)
fund_stock_rows = fund_df[
    (fund_df["cusip"] == cusip) & 
    (fund_df["date"] <= rec_date)
].sort_values("date")

latest_row = fund_stock_rows.iloc[-1]

# Split into fundamental and technical columns
fundamental_prompt = latest_row[FUNDAMENTAL_COLS].to_dict()
technical_prompt = latest_row[TECHNICAL_COLS].to_dict()

# Extract NEWS data
news_filtered = news_df[
    (news_df["cusip"] == cusip) &
    (news_df["announcedate"] >= start_date) &
    (news_df["announcedate"] <= rec_date)
]

news_prompt = news_filtered.to_json(orient="records")
```

**Data Extraction Details:**

1. **Fundamental Data Extraction:**
   - Filters FUND dataframe by CUSIP and date ≤ rec_date
   - Gets latest available row (most recent data before recommendation)
   - Extracts 30 fundamental columns (defined in `FUNDAMENTAL_COLS`)
   - Includes: EPS, ROE, leverage, cash flow, margins, etc.
   - Converts to dictionary for agent input

2. **Technical Data Extraction:**
   - Same FUND dataframe, same row
   - Extracts 14 technical columns (defined in `TECHNICAL_COLS`)
   - Includes: RSI, MACD, returns, volume, volatility, etc.
   - Converts to dictionary for agent input

3. **News Data Extraction:**
   - Filters NEWS dataframe by CUSIP and date window
   - Window: `news_window_days` before rec_date (default: 30 days)
   - Converts to JSON array format
   - Includes: headlines, dates, event types

**Column Definitions:**

```python
FUNDAMENTAL_COLS = [
    "epsfxq_ffill", "eps_yoy_growth", "eps_ttm", "niq_ffill", "ceqq_ffill",
    "roe", "atq_ffill", "ltq_ffill", "dlttq_ffill", "lctq_ffill",
    "leverage", "longterm_debt_ratio", "debt_to_equity", ...  # 30 total
]

TECHNICAL_COLS = [
    "price_adjusted", "volume_adjusted", "daily_return_adjusted",
    "mean_30d_returns", "rsi_14", "macd_line", "macd_signal", ...  # 14 total
]
```

#### Step 2: Agent Creation

Agents are created as module-level instances in `agents.py` (not per-request):

```python
# From agents.py (already defined):
fundamental_agent  # Already instantiated
technical_agent    # Already instantiated
news_agent         # Already instantiated
recommender_manager # Already instantiated
```

**Why Module-Level?**
- Agents are stateless (no memory between runs)
- Shared LLM instance for consistency
- More efficient (no re-creation per request)

#### Step 3: Task Creation

Tasks are defined in `tasks.py`. The manager task is created per-request:

```python
# Specialist tasks (already defined in tasks.py):
fundamental_task  # Module-level, uses {{fundamentals}} placeholder
technical_task    # Module-level, uses {{technicals}} placeholder
news_task         # Module-level, uses {{news}} placeholder

# Manager task (created per-request):
manager_task = create_recommender_manager_task(
    fundamental_report=fundamental_text,
    technical_report=technical_text,
    news_report=news_text,
    stock_info=stock_info,
)
```

**Input Injection:**
Specialist tasks use CrewAI's `inputs` parameter to inject data:

```python
fundamental_output = fund_crew.kickoff(inputs={"fundamentals": fundamental_prompt})
technical_output = tech_crew.kickoff(inputs={"technicals": technical_prompt})
news_output = news_crew.kickoff(inputs={"news": news_prompt})
```

The `{{fundamentals}}`, `{{technicals}}`, and `{{news}}` placeholders in task descriptions are replaced with actual data.

#### Step 4: Run Specialist Analysts (Sequential)

Each analyst runs in a separate Crew:

```python
# Fundamental Analyst
fund_crew = Crew(
    agents=[fundamental_agent],
    tasks=[fundamental_task],
    process=Process.sequential,
    verbose=False,
)
fundamental_output = fund_crew.kickoff(inputs={"fundamentals": fundamental_prompt})
fundamental_text = str(fundamental_output)
```

This repeats for technical and news analysts. Each takes ~30 seconds.

#### Step 5: Manager Synthesis

```python
manager_task = create_recommender_manager_task(
    fundamental_report=fundamental_text,
    technical_report=technical_text,
    news_report=news_text,
    stock_info=stock_info,
)

manager_crew = Crew(
    agents=[recommender_manager],
    tasks=[manager_task],
    process=Process.sequential,
    verbose=False,
)

final_recommendation = manager_crew.kickoff()
final_text = str(final_recommendation)
```

Manager receives all three reports and synthesizes them. Takes ~20 seconds.

#### Step 6: Build Final Report

The orchestrator builds a complete markdown report:

```python
lines = []
lines.append("# 🤖 Multi-Agent Model Recommendation")
lines.append(f"**Stock**: {ticker} ({company})")
lines.append(f"**Analysis Date**: {rec_date.date()}")
lines.append("")
lines.append(final_text)  # Manager's synthesis
lines.append("")
lines.append("---")
lines.append("# 📊 Analyst Reports")
lines.append("")
lines.append(fundamental_text)
lines.append("")
lines.append(technical_text)
lines.append("")
lines.append(news_text)

return "\n".join(lines)
```

Returns complete markdown with manager synthesis + all analyst reports.

---

## Data Flow Diagram

```
User Request
    |
    v
[Backend API: /api/recommender/run]
    |
    v
run_multi_analyst_recommendation()
    |
    +---> Extract CUSIP and Date from IBES
    |         |
    |         +---> Extract Latest FUND Row
    |         |         |
    |         |         +---> Split into Fundamental Dict (30 cols)
    |         |         +---> Split into Technical Dict (14 cols)
    |         |
    |         +---> Extract NEWS Window (30 days)
    |                   |
    |                   +---> Convert to JSON Array
    |
    +---> Use Module-Level Agents (already instantiated)
    |
    +---> Run Fundamental Crew
    |         |
    |         +---> Inject Fundamental Dict via inputs={}
    |         +---> [Gemini API Call]
    |         |
    |         +---> Fundamental Report (markdown with Rating)
    |
    +---> Run Technical Crew
    |         |
    |         +---> Inject Technical Dict via inputs={}
    |         +---> [Gemini API Call]
    |         |
    |         +---> Technical Report (markdown with Rating)
    |
    +---> Run News Crew
    |         |
    |         +---> Inject News JSON via inputs={}
    |         +---> [Gemini API Call]
    |         |
    |         +---> News Report (markdown with Rating)
    |
    +---> Run Manager Crew
    |         |
    |         +---> Inject All 3 Reports + Stock Info
    |         +---> [Gemini API Call]
    |         |
    |         +---> Final Synthesis (markdown with Final Rating + Weighting)
    |
    +---> Build Complete Report (Manager + All Analyst Reports)
    |
    +---> Return Markdown
    |
    v
[Backend parses and extracts final_rating]
    |
    v
[Frontend displays: Rating Comparison + Manager Report]
```

---

## Example Execution

### Input
- **Ticker:** AMZN (Amazon)
- **Date:** 2008-01-08
- **CUSIP:** "02313510"
- **News Window:** 30 days

### Data Extraction Results

**Fundamental Data (30 metrics):**
- EPS: N/A (missing)
- ROE: N/A (missing)
- All metrics: N/A

**Technical Data (14 indicators):**
- Price: $92.50
- Daily Return: -1.06%
- 30-day Return: -0.99%
- RSI: 0.15 (extremely oversold)
- MACD: Bearish crossover
- Volume: Spike on decline

**News Data:**
- 1 news item in 30-day window:
  - "Amazon launches Tax Central" (positive)

### Agent Outputs

**Fundamental Analyst:**
```markdown
## Fundamental Analysis

### Rating
- **Fundamental Rating**: Hold
- **Confidence**: Low

### Key Signals
- **Positive**: (none)
- **Negative**: (none)
- **Neutral/Missing**: All metrics are N/A

### Reasoning
Cannot perform fundamental analysis due to complete absence of data. 
Default to Hold with low confidence.
```

**Technical Analyst:**
```markdown
## Technical Analysis

### Rating
- **Technical Rating**: Sell
- **Confidence**: High

### Key Signals
- **Bullish**: RSI extremely oversold (0.15) - potential bounce
- **Bearish**: 
  - Negative returns (-1.06% daily, -0.99% 30-day avg)
  - MACD bearish crossover
  - Volume spike on down day (selling pressure)
- **Neutral**: Elevated volatility

### Reasoning
Stock experiencing strong bearish momentum. Negative MACD crossover and 
volume spike on decline indicate continued downside risk. While RSI 
oversold, overwhelming bearish signals support SELL.
```

**News Analyst:**
```markdown
## News & Sentiment Analysis

### Rating
- **News-Based Rating**: Buy
- **Confidence**: High

### Sentiment Breakdown
- **Positive News**: 1 (Amazon Tax Central launch)
- **Negative News**: 0
- **Neutral News**: 0

### Major Catalysts
- Launch of Amazon Tax Central
- Introduction of Amazon Software Downloads Service

### Reasoning
Positive strategic move expanding into tax software and digital downloads. 
Diversifies offerings and enhances value proposition. Typically viewed 
favorably by market.
```

### Manager Synthesis

```markdown
## Model Recommendation (Final)

### Final Rating
- **Model Rating**: Sell
- **Overall Confidence**: Medium

### Analyst Ratings Summary
- **Fundamental**: Hold (Low confidence)
- **Technical**: Sell (High confidence)
- **News**: Buy (High confidence)

### Signal Alignment
- **Agreement Level**: Split
- **Dominant Signal**: Technical

### Weighting Logic
- **Fundamental**: 10% - Low confidence, no data available. Cannot provide 
  meaningful input. Minimal weight assigned.

- **Technical**: 60% - High confidence with clear, unambiguous bearish 
  signals (RSI 0.15, MACD crossover, volume spike on decline). In a market 
  exhibiting such strong negative technicals, these are crucial for 
  immediate risk management and capital preservation.

- **News**: 30% - High confidence and positive strategic catalysts, but 
  contradicts dominant technical trend. Positive headlines cannot override 
  severe technical breakdown in crisis environment (2008 financial crisis).

### Synthesis
During market turmoil, price action reflects reality faster than news 
sentiment. Technical analyst's bearish signals are unambiguous. News 
positivity acknowledged but insufficient to counter strong selling pressure. 
Final rating: SELL with medium confidence due to contradictory signals 
between high-confidence technical and news views.

### Risk Assessment
- **Primary Risk**: Missing fundamentals reduce conviction. Cannot verify 
  financial health independently.
- **Data Quality**: Technical data clear and reliable; fundamentals absent; 
  news limited but positive.
```

**Human Rating (hidden until after):** SELL ✓ (Match!)

---

## Key Innovation: LLM-Based Synthesis

### Why Not Simple Voting?

**Traditional Approach:**
```python
def combine_ratings(fund, tech, news):
    ratings = [fund, tech, news]
    return Counter(ratings).most_common()[0][0]  # Majority vote
```

**Problems:**
- All ratings weighted equally
- Ignores confidence levels
- Can't handle ties intelligently
- No reasoning or context
- Doesn't adapt to market conditions

### Our Approach: Intelligent LLM Manager

**Benefits:**
1. **Adaptive Weighting** - Weighs by confidence (High > Medium > Low)
2. **Context-Aware** - Understands market conditions (crisis favors technicals)
3. **Handles Contradictions** - Explicitly resolves conflicts with logic
4. **Transparent** - Shows exact weighting percentages and reasoning
5. **Risk-Aware** - Acknowledges uncertainties and missing data

**Example Weighting Logic:**
- Technical: 60% (high confidence, clear signals)
- News: 30% (high confidence but contradicts dominant trend)
- Fundamental: 10% (low confidence, no data)

This produces more nuanced decisions than simple majority voting.

---

## Integration Points

### Backend API (`backend/api/recommender.py`)

The orchestrator is called from the FastAPI endpoint:

```python
reco_md = run_multi_analyst_recommendation(
    cusip=str(cusip),
    rec_date=rec_date,
    fund_df=fund,
    news_df=news,
    news_window_days=news_window_days,
    ticker=ticker,
    company=company,
)
```

The backend then:
1. Parses markdown to separate manager and analyst reports
2. Extracts final rating using regex
3. Extracts human rating from IBES (for comparison, but hidden initially)
4. Returns structured JSON with:
   - `manager_report`: Manager's synthesis
   - `analyst_reports`: Dict with fundamental/technical/news reports
   - `full_markdown`: Complete original markdown
   - `final_rating`: Extracted model rating
   - `human_rating`: Human analyst rating (for comparison)

### Frontend (`frontend/insight-agent/src/components/ResultsDisplay.tsx`)

The frontend:
1. Polls the API for job status
2. Shows rating comparison card first (AI vs Human - human blurred until clicked)
3. Displays manager report with truncated content (first 5 sections)
4. Shows analyst reports in collapsible sections
5. Renders markdown using `react-markdown`

**UI Features:**
- Rating comparison with click-to-reveal human rating
- Truncated manager report (more concise)
- Expandable analyst reports
- Mode-specific styling (explainer vs recommender colors)

---

## Key Implementation Details

### Agent Configuration

- **Shared LLM Instance:** All agents use same `_llm` for consistency
- **Temperature:** 0.2 (lower than Explainer for more consistent ratings)
- **No Memory:** Agents are stateless (no memory between runs)
- **No Delegation:** Agents don't create sub-agents

### Task Input Injection

CrewAI's `inputs` parameter allows dynamic data injection:

```python
crew.kickoff(inputs={"fundamentals": data_dict})
```

The `{{fundamentals}}` placeholder in task description is replaced with actual data.

### Rating Extraction

The backend uses regex to extract the final rating from manager report:

```python
def extract_final_rating(markdown: str) -> str:
    # Looks for patterns like "Model Rating: Sell"
    match = re.search(r"Model Rating[:\s]+(\w+)", markdown, re.IGNORECASE)
    return match.group(1) if match else None
```

### Performance

- **Total Runtime:** ~60-90 seconds
  - Fundamental Analyst: ~30 seconds
  - Technical Analyst: ~30 seconds
  - News Analyst: ~30 seconds
  - Manager: ~20 seconds
- **API Calls:** 4 total (one per agent)
- **Sequential Execution:** No parallelization currently

---

## Comparison: Explainer vs Recommender

| Aspect | Explainer | Recommender |
|--------|-----------|-------------|
| **Goal** | Explain human's rating | Make own rating |
| **Specialist Output** | Analysis report | Rating + report |
| **Manager Output** | Explanation synthesis | Rating decision + weighting |
| **Shows Human Rating?** | Yes (explaining it) | No (hidden until after) |
| **Confidence** | Explanation confidence (0-100) | Rating confidence (High/Med/Low) |
| **Temperature** | 0.3 | 0.2 (more consistent) |
| **Key Innovation** | Multi-perspective explanation | Intelligent rating synthesis |

---

## Design Decisions

### Why Module-Level Agents?

- **Efficiency:** No re-creation per request
- **Consistency:** Shared LLM instance
- **Stateless:** Agents don't maintain memory anyway

### Why Structured Output Format?

- **Reliability:** Strict format enables parsing
- **Validation:** Can verify agent outputs
- **Consistency:** Ensures all agents produce comparable reports

### Why LLM Manager Instead of Rules?

- **Adaptability:** Handles edge cases and contradictions
- **Context-Aware:** Understands market conditions
- **Transparency:** Explains reasoning in natural language
- **Flexibility:** Can adjust weighting logic dynamically

### Why Lower Temperature?

- **Consistency:** More reproducible ratings
- **Reliability:** Less creative variation
- **Decision-Making:** Investment decisions should be more deterministic

---

## Future Enhancements

Potential improvements:
- **Confidence Calibration:** Use historical performance to calibrate confidence scores
- **Ensemble Methods:** Run manager multiple times, average ratings
- **Feature Importance:** Extract which signals most influenced each decision
- **Backtesting:** Compare model ratings to actual stock performance
- **Parallel Execution:** Run three specialists concurrently
- **Caching:** Cache analyst reports for repeated requests

---

## Summary

The Recommender team demonstrates advanced multi-agent decision-making:

- **4 specialized agents** making independent ratings
- **Intelligent synthesis** via LLM-based manager (not simple voting)
- **Adaptive weighting** based on confidence and context
- **Transparent reasoning** with explicit weighting logic
- **Handles contradictions** intelligently

The key innovation is the Portfolio Manager's ability to intelligently weigh conflicting signals, adapt to market conditions, and provide transparent reasoning—capabilities that simple voting algorithms cannot match.
