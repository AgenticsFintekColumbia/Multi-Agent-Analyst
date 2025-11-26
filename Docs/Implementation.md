# Implementation Summary

Our Team's Agentic AI Project

---

## Project Overview

We built a **multi-agent AI system** that analyzes stock analyst recommendations using two teams:

1. **Explainer Team** - Explains why a human analyst gave a rating
2. **Recommender Team** - Makes its own independent rating

**Tech Stack:**
- Google Gemini (LLM)
- CrewAI (agent framework)
- Streamlit (web interface)
- Python + Pandas (data handling)

**Data:**
- 7,804 analyst recommendations (IBES)
- 128,317 stock price records (FUND)
- 141,418 news articles (NEWS)
- Timeframe: 2008-2024, Dow Jones 30 stocks

---

## What We Built

### High-Level Architecture

```
        User Interface (Streamlit)
                 |
        +--------+--------+
        |                 |
   Explainer          Recommender
     Team               Team
        |                 |
    Manager           Portfolio
        |              Manager
   +----+----+       +----+----+
   |    |    |       |    |    |
  Fund Tech News    Fund Tech News
```

Both teams follow the same pattern:
- 3 specialist analysts (Fundamental, Technical, News)
- 1 manager to synthesize their outputs
- **Total: 8 AI agents** (4 per team)

---

## Implementation Details

### Team 1: Explainer

**Purpose:** Explain why human analyst gave specific rating

**Architecture:**
```
Explainer Manager (synthesizes explanation)
├── Fundamental Analyst (analyzes financials)
├── Technical Analyst (analyzes price/charts)
└── News Analyst (analyzes headlines)
```

**Input:** IBES recommendation + context (FUND + NEWS)

**Process:**
1. Split data into three parts (fundamental, technical, news)
2. Each analyst analyzes their data independently
3. Manager reads all three reports
4. Manager synthesizes coherent explanation

**Output:**
- Executive summary
- Key drivers (positive/negative)
- Consistency check
- Confidence score (0-100)

**Runtime:** ~60-90 seconds

**Files:**
```
src/explainer/
├── agents.py       # 4 agent definitions
├── tasks.py        # 4 task definitions
└── orchestrator.py # Runs the team
```

---

### Team 2: Recommender

**Purpose:** Make independent model recommendation

**Architecture:**
```
Portfolio Manager (makes final rating)
├── Fundamental Analyst (→ rating)
├── Technical Analyst (→ rating)
└── News Analyst (→ rating)
```

**Input:** Stock + date (human rating HIDDEN to prevent bias)

**Process:**
1. Extract latest data before rec date
2. Each analyst makes rating (StrongBuy/Buy/Hold/UnderPerform/Sell)
3. Portfolio Manager intelligently synthesizes ratings
4. Manager weighs signals by confidence level

**Output:**
- Final model rating
- Analyst ratings summary
- Signal alignment analysis
- Weighting logic (% weights)
- Synthesis explanation
- Risk assessment

**Runtime:** ~60-90 seconds

**Files:**
```
src/recommender/
├── agents.py       # 4 agent definitions
├── tasks.py        # 4 task definitions
└── orchestrator.py # Runs the team
```

---

## User Interface

### Streamlit Web App

**Flow:**
1. **Mode Selection** - Choose Explainer or Recommender
2. **Stock Selection** - Pick ticker and recommendation date
3. **Context Windows** - Adjust time windows (optional)
4. **Generate** - Click button to run agents
5. **View Results** - See final output + detailed reports (expandable)

**Key UX Features:**
- Clean, modern design with gradient background
- Mode badges and visual indicators
- Info badge for Recommender (explains hidden rating)
- Expandable sections for detailed analyst reports
- Side-by-side comparison (Model vs Human)

**Smart Design:**
- **Explainer mode:** Shows human rating (we're explaining it)
- **Recommender mode:** Hides human rating (prevents bias)

---

## Data Pipeline

### Data Loading

```python
# data_loader.py
def load_datasets():
    ibes = pd.read_feather("data/ibes_...")
    fund = pd.read_feather("data/fund_...")
    news = pd.read_feather("data/ciq_...")
    return ibes, fund, news
```

### Context Building

```python
def build_context_for_rec(ibes, fund, news, rec_index):
    # 1. Get IBES recommendation
    rec = ibes.iloc[rec_index]
    
    # 2. Get FUND data (30 days before)
    fund_data = fund[fund['date'] < rec_date]
    
    # 3. Get NEWS data (±7 days around)
    news_data = news[news['date'].between(
        rec_date - 7days, rec_date + 7days
    )]
    
    # 4. Format as human-readable text
    return context_string
```

---

## Technical Implementation

### Agent Creation

```python
# Example: Fundamental Analyst
agent = Agent(
    role="Fundamental Analyst",
    goal="Analyze fundamental metrics...",
    backstory="Senior analyst with expertise in...",
    llm=gemini_llm,
    verbose=False,  # Avoid console spam
)
```

### Task Creation

```python
task = Task(
    description="Analyze fundamentals...",
    expected_output="Markdown with rating + reasoning",
    agent=fundamental_analyst,
)
```

### Crew Execution

```python
crew = Crew(
    agents=[analyst],
    tasks=[task],
    process=Process.sequential,
    verbose=False,
)

output = crew.kickoff(inputs={"data": data})
```

### Orchestration

```python
# Run three specialists
fund_report = fund_crew.kickoff()
tech_report = tech_crew.kickoff()
news_report = news_crew.kickoff()

# Run manager
final = manager_crew.kickoff(inputs={
    "fund": fund_report,
    "tech": tech_report,
    "news": news_report,
})
```

---

## Key Innovations

### 1. Hierarchical Multi-Agent Architecture

**What:** Specialists report to managers (like real teams)

**Why:** Better than single agent trying to do everything

**Benefit:** Clear separation of concerns, specialized expertise

---

### 2. Intelligent Synthesis (Not Simple Voting)

**Old approach:**
```python
# Just count votes
ratings = [fund_rating, tech_rating, news_rating]
final = most_common(ratings)
```

**Our approach:**
```python
# LLM-based intelligent weighting
manager = Agent(role="Portfolio Manager", ...)
final = manager.synthesize(
    ratings, confidences, context
)
```

**Why better:**
- Considers confidence levels
- Context-aware (market regime)
- Explains reasoning
- Handles contradictions intelligently

---

### 3. Bias Prevention

**Problem:** Seeing human rating could bias model

**Solution:** Hide human rating in Recommender mode

**Implementation:**
```python
if mode == "explainer":
    show_human_rating()  # We're explaining it
else:
    hide_human_rating()  # Make independent decision
    
# Only show comparison AFTER model decides
```

---

### 4. Structured Outputs

Every agent outputs strict markdown format:

```markdown
## [Section Name]

### Rating
- **[Type] Rating**: [Value]
- **Confidence**: [Level]

### Key Signals
- **Positive**: [list]
- **Negative**: [list]
- **Neutral**: [list]

### Reasoning
[2-3 sentences]
```

**Why:** Parseable, consistent, professional

---

### 5. Graceful Degradation

**Problem:** Data is often missing (especially fundamentals)

**Solution:** Agents acknowledge missing data explicitly

```markdown
### Neutral/Missing Data
- EPS: N/A
- ROE: N/A
(etc.)

Rating: HOLD (Low confidence - cannot assess without data)
```

**Benefit:** System works even with incomplete data

---

## Results & Learnings

### What Works Well

✅ **Architecture is solid**
- Clean separation between teams
- Specialists focus on one thing
- Managers provide synthesis

✅ **LLM synthesis is powerful**
- Much better than simple voting
- Considers nuance and context
- Transparent reasoning

✅ **Handles real complexity**
- Missing data common → system adapts
- Contradictory signals → manager resolves
- Market context matters → system understands



---


## Project Structure

```
our-project/
├── src/
│   ├── explainer/         # Team 1
│   │   ├── agents.py
│   │   ├── tasks.py
│   │   └── orchestrator.py
│   └── recommender/       # Team 2
│       ├── agents.py
│       ├── tasks.py
│       └── orchestrator.py
├── data/                  # Stock data
├── docs/                  # Documentation
├── tests/                 # Test scripts
├── data_loader.py        # Data utilities
├── gui_app.py            # Main app
└── requirements.txt      # Dependencies
```

**Total Lines of Code:** ~2,500

**Agent Definitions:** 8

**Task Definitions:** 8

**Documentation Pages:** 4

---

## Future Enhancements

If we had more time:

1. **Backtesting** - Test model on all 7,804 recommendations
2. **Performance Metrics** - Accuracy vs human analysts
3. **More Analysts** - Add Valuation, Risk, Macro specialists
4. **Ensemble Methods** - Multiple managers voting
5. **Real-time Data** - Connect to live market feeds
6. **Portfolio Optimization** - Multi-stock recommendations
7. **Parallel Execution** - Run specialists simultaneously
8. **Caching** - Store analyst reports for same stock/date

---

## Acknowledgments

**Built for:** Agentic AI, The Data Economy & Fintech

**Technologies:**
- Google Gemini API (LLM)
- CrewAI (agent framework)
- Streamlit (web app)
- Python + Pandas (data)

**Data Sources:**
- IBES (analyst recommendations)
- CRSP (stock prices & fundamentals)
- Compustat Capital IQ (news)

**Special Thanks:** Professor and TAs for guidance on this project.

---
