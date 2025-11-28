# Explainer Team Architecture - Technical Documentation

## Overview

The Explainer team is a multi-agent system that explains **why a human analyst gave a specific rating** to a stock. It uses 4 specialized AI agents working together to analyze three data types (fundamental, technical, news) and synthesize them into a coherent explanation.

---

## System Architecture

### Agent Hierarchy

```
                    Explainer Manager
                    (Synthesis Agent)
                           |
         +-----------------+-----------------+
         |                 |                 |
   Fundamental         Technical          News
    Analyst             Analyst          Analyst
    (Agent 1)          (Agent 2)        (Agent 3)
         |                 |                 |
    Analyzes            Analyzes         Analyzes
   Financial            Price &          Headlines
    Metrics             Charts           & Sentiment
```

### Key Design Principles

1. **Separation of Concerns** - Each analyst sees only their data type
2. **Sequential Execution** - Analysts run first, then manager synthesizes
3. **No Cross-Communication** - Analysts don't see each other's reports until manager reads them all
4. **Specialized Expertise** - Each agent has a specific role and backstory

---

## Code Structure

### File Organization

```
src/explainer/
├── __init__.py          # Exports main orchestrator function
├── agents.py            # Agent definitions (4 agents)
├── tasks.py             # Task definitions for each agent
└── orchestrator.py      # Main execution flow and data extraction
```

### Module Responsibilities

- **`agents.py`**: Defines the 4 CrewAI agents with their roles, goals, backstories, and LLM configuration
- **`tasks.py`**: Defines what each agent should do, including input formatting and output structure requirements
- **`orchestrator.py`**: Coordinates the entire process - extracts data, creates agents/tasks, runs crews, manages flow

---

## Agent Definitions (`agents.py`)

All agents use **Google Gemini 2.5 Flash** as the underlying LLM, configured via CrewAI's LLM wrapper.

### Agent Configuration Pattern

```python
def create_[agent_name]() -> Agent:
    llm = _build_gemini_llm(temperature=0.3)
    
    agent = Agent(
        role="[Agent Role Name]",
        goal="[What they're trying to accomplish]",
        backstory="[Their expertise and constraints]",
        verbose=False,              # Avoid recursion issues
        allow_delegation=False,     # No sub-agent delegation
        llm=llm,
    )
    return agent
```

### 1. Fundamental Analyst

**File:** `src/explainer/agents.py::create_fundamental_explainer_analyst()`

**Purpose:** Analyzes financial metrics to explain how fundamentals influenced the human analyst's rating.

**Configuration:**
- **Role:** "Fundamental Data Analyst (Explainer Team)"
- **Goal:** Analyze fundamental metrics (EPS, ROE, leverage, cash flows, etc.) to explain how these influenced the human analyst's recommendation
- **Temperature:** 0.3 (more consistent, less creative)
- **Key Constraints:** 
  - Must be concise (no planning text)
  - Must state explicitly if data is missing
  - Cannot make up numbers

**Input:** Structured string with fundamental metrics (from `extract_fundamental_data()`)

**Output:** Markdown analysis report focusing on how fundamentals explain the rating

---

### 2. Technical Analyst

**File:** `src/explainer/agents.py::create_technical_explainer_analyst()`

**Purpose:** Analyzes price action, momentum, volume, and technical indicators to explain technical influence on the rating.

**Configuration:**
- **Role:** "Technical Analysis Specialist (Explainer Team)"
- **Goal:** Analyze price movements, momentum indicators, volume patterns, and technical signals to explain how these influenced the human analyst's recommendation
- **Temperature:** 0.3
- **Key Constraints:**
  - Works only with provided technical data
  - Cannot invent price levels or indicators
  - Must be concise and direct

**Input:** Structured string with technical indicators (from `extract_technical_data()`)

**Output:** Markdown analysis report focusing on how technicals explain the rating

---

### 3. News Analyst

**File:** `src/explainer/agents.py::create_news_explainer_analyst()`

**Purpose:** Analyzes news headlines and sentiment to explain how news influenced the rating.

**Configuration:**
- **Role:** "News & Sentiment Analyst (Explainer Team)"
- **Goal:** Analyze news headlines and sentiment to explain how these influenced the human analyst's recommendation
- **Temperature:** 0.3
- **Key Constraints:**
  - Focuses only on sentiment and catalysts
  - Must assess positive/negative impact of each headline
  - Cannot speculate beyond provided news

**Input:** JSON-formatted news headlines (from `extract_news_data()`)

**Output:** Markdown analysis report focusing on how news explains the rating

---

### 4. Explainer Manager

**File:** `src/explainer/agents.py::create_explainer_manager()`

**Purpose:** Synthesizes all three analyst reports into a coherent explanation of why the human analyst gave their rating.

**Configuration:**
- **Role:** "Senior Equity Research Director (Explainer Team)"
- **Goal:** Synthesize three specialist reports into a comprehensive explanation of why the human analyst gave their specific rating
- **Temperature:** 0.3
- **Key Constraints:**
  - Must be concise (no planning text)
  - Must start directly with "## Executive Summary"
  - Can only use information from the three analyst reports
  - Cannot add external data or speculation

**Input:** All three analyst reports + IBES recommendation info

**Output:** Structured markdown explanation with:
  - Executive Summary
  - Key Drivers (Positive/Negative/Mixed)
  - Analyst Perspective
  - Confidence Score (0-100)

---

## Task Definitions (`tasks.py`)

Tasks define **what** each agent should do, including:
- Input format expectations
- Output structure requirements
- Constraints and instructions

### Task Creation Pattern

```python
def create_[agent]_task(agent, data: str) -> Task:
    description = f"""
    [Detailed instructions for the agent]
    
    INPUT DATA:
    {data}
    
    OUTPUT FORMAT:
    [Expected markdown structure]
    
    CONSTRAINTS:
    [What they cannot do]
    """
    
    return Task(
        description=description,
        agent=agent,
        expected_output="[Brief description of expected output]",
    )
```

### Task Flow

1. **Fundamental Task** (`create_fundamental_explainer_task`)
   - Receives: Fundamental data string
   - Expected Output: Markdown with positive/negative/neutral signals

2. **Technical Task** (`create_technical_explainer_task`)
   - Receives: Technical data string
   - Expected Output: Markdown with momentum, volume, indicator analysis

3. **News Task** (`create_news_explainer_task`)
   - Receives: JSON news headlines
   - Expected Output: Markdown with sentiment breakdown and catalysts

4. **Manager Task** (`create_explainer_manager_task`)
   - Receives: IBES info + all three analyst reports
   - Expected Output: Structured explanation with confidence score

---

## Orchestration Flow (`orchestrator.py`)

The orchestrator is the main entry point: `run_multi_analyst_explainer()`

### Execution Steps

#### Step 1: Data Extraction

```python
# Extract recommendation from IBES dataset
rec_series = ibes_df.iloc[rec_index]

# Extract data for each analyst
fundamental_data = extract_fundamental_data(rec_series, fund_df, fund_window_days)
technical_data = extract_technical_data(rec_series, fund_df, fund_window_days)
news_data = extract_news_data(rec_series, news_df, news_window_days)
ibes_info = extract_ibes_info(rec_series)
```

**Data Extraction Functions:**

1. **`extract_fundamental_data()`**
   - Filters FUND dataframe by CUSIP and date window
   - Extracts latest fundamental metrics (EPS, ROE, leverage, cash flow)
   - Formats as structured string
   - **Window:** `fund_window_days` before recommendation date

2. **`extract_technical_data()`**
   - Filters FUND dataframe for same company/window
   - Extracts price movements, RSI, MACD, volume patterns
   - Calculates returns, volatility
   - **Window:** `fund_window_days` before recommendation date

3. **`extract_news_data()`**
   - Filters NEWS dataframe by CUSIP and date window
   - Extracts headlines, dates, event types
   - Formats as JSON array
   - **Window:** `news_window_days` around recommendation date (typically ±7 days)

4. **`extract_ibes_info()`**
   - Extracts the human analyst's recommendation details
   - Includes: ticker, company, date, rating, analyst name
   - Provides context for the manager

#### Step 2: Agent Creation

```python
fundamental_analyst = create_fundamental_explainer_analyst()
technical_analyst = create_technical_explainer_analyst()
news_analyst = create_news_explainer_analyst()
explainer_manager = create_explainer_manager()
```

Creates all 4 agents with their configured roles and backstories.

#### Step 3: Task Creation

```python
fundamental_task = create_fundamental_explainer_task(fundamental_analyst, fundamental_data)
technical_task = create_technical_explainer_task(technical_analyst, technical_data)
news_task = create_news_explainer_task(news_analyst, news_data)
```

Creates tasks with their specific data inputs.

#### Step 4: Run Specialist Analysts (Sequential)

Each analyst runs in a separate Crew (one agent + one task):

```python
# Fundamental Analyst
fundamental_crew = Crew(
    agents=[fundamental_analyst],
    tasks=[fundamental_task],
    process=Process.sequential,
    verbose=False,  # Avoid recursion issues
)
fundamental_report = fundamental_crew.kickoff()
fundamental_text = str(fundamental_report).strip()
```

This pattern repeats for technical and news analysts.

**Why Sequential?**
- CrewAI runs agents sequentially by default
- Even if we set up parallel crews, each crew runs its agent sequentially
- Total time: ~30 seconds per analyst = ~90 seconds for all three

#### Step 5: Manager Synthesis

```python
manager_task = create_explainer_manager_task(
    explainer_manager,
    ibes_info,
    fundamental_text,
    technical_text,
    news_text,
)

manager_crew = Crew(
    agents=[explainer_manager],
    tasks=[manager_task],
    process=Process.sequential,
    verbose=False,
)

final_explanation = manager_crew.kickoff()
```

Manager receives all three reports and synthesizes them.

#### Step 6: Return Results

The orchestrator returns the complete markdown explanation string, which includes:
- Manager's synthesis (executive summary, key drivers, confidence)
- All three analyst reports (for detailed view)

---

## Data Flow Diagram

```
User Request
    |
    v
[Backend API: /api/explainer/run]
    |
    v
run_multi_analyst_explainer()
    |
    +---> Extract IBES Recommendation
    |         |
    |         +---> Extract Fundamental Data (FUND dataset)
    |         +---> Extract Technical Data (FUND dataset)
    |         +---> Extract News Data (NEWS dataset)
    |         +---> Extract IBES Info
    |
    +---> Create Agents (4 agents)
    |
    +---> Create Tasks (4 tasks with data)
    |
    +---> Run Fundamental Crew
    |         |
    |         +---> [Gemini API Call]
    |         |
    |         +---> Fundamental Report (markdown)
    |
    +---> Run Technical Crew
    |         |
    |         +---> [Gemini API Call]
    |         |
    |         +---> Technical Report (markdown)
    |
    +---> Run News Crew
    |         |
    |         +---> [Gemini API Call]
    |         |
    |         +---> News Report (markdown)
    |
    +---> Run Manager Crew
    |         |
    |         +---> [Gemini API Call with all 3 reports]
    |         |
    |         +---> Final Explanation (markdown)
    |
    +---> Return Complete Report
    |
    v
[Backend parses and returns JSON]
    |
    v
[Frontend displays results]
```

---

## Example Execution

### Input
- **Ticker:** AMZN (Amazon)
- **Date:** 2008-01-08
- **Human Rating:** SELL
- **Fund Window:** 30 days
- **News Window:** 7 days

### Data Extraction Results

**Fundamental Data:**
- EPS: N/A
- ROE: N/A
- All metrics missing

**Technical Data:**
- Price down -7.72% over 30 days
- RSI: 0.15 (extremely oversold)
- MACD: Bearish crossover
- Volume spike on decline

**News Data:**
- Amazon Tax Central launch (positive)
- MP3 store expansion (positive)
- French legal ruling (negative)

### Agent Outputs

**Fundamental Analyst:**
```
## Fundamental Analysis
- All metrics: N/A
- Cannot assess financial health
- Verdict: NEUTRAL (no data)
```

**Technical Analyst:**
```
## Technical Analysis
- Strong bearish momentum
- RSI 0.15 = extreme oversold
- MACD bearish crossover
- Volume spike indicates selling pressure
- Verdict: STRONG SELL signals
```

**News Analyst:**
```
## News Analysis
- Positive product launches
- Minor legal headwind
- Overall: Positive sentiment
- Verdict: SLIGHT BUY (positive developments)
```

### Manager Synthesis

```
## Executive Summary
The SELL rating is primarily driven by overwhelmingly negative technical 
signals (RSI 0.15, -7.72% decline). This overrode positive news flow and 
absent fundamental data.

## Key Drivers

**Positive Factors:**
- News: Product launches, business expansion

**Negative Factors:**
- Technical: Extreme downtrend, oversold RSI, bearish MACD
- Volume spike on decline = strong selling pressure

**Mixed/Neutral:**
- Fundamentals: All data missing (N/A)

## Consistency Check
- Technical: STRONG SELL ✓
- News: SLIGHT BUY ✗
- Fundamentals: NEUTRAL (no data)

Verdict: Signals contradict. Analyst prioritized technicals over news.

## Confidence Score: 70/100
Moderate confidence. Technical signal is clear and strong, but contradicts 
news and lacks fundamental support.
```

---

## Key Implementation Details

### CrewAI Configuration

- **Process:** `Process.sequential` - Each agent completes before next starts
- **Verbose:** `False` - Avoids Rich console recursion issues with multiple crews
- **Delegation:** `False` - Agents don't create sub-agents

### LLM Configuration

- **Model:** `gemini-2.5-flash` (Google Gemini)
- **Temperature:** 0.3 (more consistent, less creative)
- **API Key:** Loaded from `GEMINI_API_KEY` environment variable

### Error Handling

- Missing data is explicitly stated (agents return "N/A" sections)
- Empty data windows return warning messages
- Agent failures would cause orchestrator to raise exception

### Performance

- **Total Runtime:** ~60-90 seconds
  - Fundamental Analyst: ~30 seconds
  - Technical Analyst: ~30 seconds
  - News Analyst: ~30 seconds
  - Manager: ~20 seconds
- **API Calls:** 4 total (one per agent)
- **Sequential Execution:** No parallelization currently

---

## Integration Points

### Backend API (`backend/api/explainer.py`)

The orchestrator is called from the FastAPI endpoint:

```python
explanation_md = run_multi_analyst_explainer(
    ibes_df=ibes,
    fund_df=fund,
    news_df=news,
    rec_index=rec_index,
    fund_window_days=fund_window_days,
    news_window_days=news_window_days,
)
```

The backend then:
1. Parses the markdown to separate manager and analyst reports
2. Returns structured JSON with:
   - `manager_report`: Manager's synthesis
   - `analyst_reports`: Dict with fundamental/technical/news reports
   - `full_markdown`: Complete original markdown

### Frontend (`frontend/insight-agent/src/components/ResultsDisplay.tsx`)

The frontend:
1. Polls the API for job status
2. Displays manager report prominently
3. Shows analyst reports in collapsible sections
4. Renders markdown using `react-markdown`

---

## Design Decisions

### Why Sequential Agents?

- **Simplicity:** Easier to debug and trace execution
- **Dependency:** Manager needs all three reports before it can synthesize
- **Resource Management:** Sequential execution avoids overwhelming API rate limits

### Why Separate Data Extraction?

- **Clear Separation:** Each analyst only sees their domain data
- **Reusability:** Extraction functions can be tested independently
- **Flexibility:** Easy to change extraction logic without affecting agents

### Why CrewAI Instead of Direct LLM Calls?

- **Agent Framework:** Provides structure for multi-agent systems
- **Task Management:** Handles prompt engineering, context management
- **Future Extensibility:** Easy to add agents, change workflows
- **Consistency:** Standardized agent/task pattern across teams

---

## Future Enhancements

Potential improvements:
- **Parallel Execution:** Run three specialists concurrently (requires async orchestration)
- **Caching:** Cache analyst reports if same data requested multiple times
- **Streaming:** Stream partial results to frontend as each analyst completes
- **Error Recovery:** Retry failed agents automatically
- **Validation:** Validate agent outputs before passing to manager

---

## Summary

The Explainer team demonstrates a clean multi-agent architecture:
- **4 specialized agents** with distinct roles
- **Clear separation** of data domains
- **Hierarchical synthesis** via manager agent
- **Transparent reasoning** with detailed reports
- **Robust error handling** for missing data

This architecture makes it easy to understand why explanations are generated and allows for independent improvement of each agent's expertise.
