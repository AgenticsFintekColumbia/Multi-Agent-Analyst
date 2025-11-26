# Explainer Team Architecture




## What Does the Explainer Do?

The Explainer team answers **Question 1** from our project:

> "Why did the human analyst give this specific rating?"

For example, if a Lehman Brothers analyst gave Amazon a **SELL** rating on January 8, 2008, our Explainer figures out what data drove that decision.

---

## Architecture: How It Works

### The Team Structure

```
                    Explainer Manager
                    (Senior Director)
                           |
         +-----------------+-----------------+
         |                 |                 |
   Fundamental         Technical          News
    Analyst             Analyst          Analyst
         |                 |                 |
    Analyzes            Analyzes         Analyzes
   Financial            Price &          Headlines
    Metrics             Charts           & Sentiment
```

We have **4 AI agents** working together:

1. **Fundamental Analyst** - Looks at financial data (EPS, revenue, cash flow)
2. **Technical Analyst** - Looks at price charts and indicators (RSI, MACD)
3. **News Analyst** - Looks at company news around the recommendation date
4. **Explainer Manager** - Reads all three reports and synthesizes the explanation

---

## Step-by-Step Flow

### Step 1: Data Extraction

When you pick a recommendation in the app, the system:

```python
# Example: Amazon, Jan 8, 2008, SELL rating
rec = ibes.loc[selected_index]

# Extract three types of data:
fundamental_data = extract_fundamental_data(rec)
technical_data = extract_technical_data(rec)
news_data = extract_news_data(rec)
```

**What each gets:**

1. **Fundamental Data:**
   - EPS (earnings per share)
   - ROE (return on equity)
   - Leverage (debt ratios)
   - Cash flow metrics
   - Latest stock price

2. **Technical Data:**
   - Recent price movements (last 30 days)
   - Daily returns
   - Volume patterns
   - RSI (Relative Strength Index)
   - MACD (momentum indicator)
   - Volatility

3. **News Data:**
   - Headlines from ±7 days around rec date
   - Event types (product launch, earnings, legal)
   - Announcement dates

---

### Step 2: Specialist Analysis (The Three Analysts)

Each analyst receives ONLY their specific data and analyzes it independently.

**Fundamental Analyst**

**Gets:** Financial metrics

**Analyzes:**
- Are earnings growing or declining?
- Is profitability strong (ROE)?
- Is debt manageable (leverage)?
- Is cash flow healthy?

**Outputs:**
```markdown
## Fundamental Analysis

### Positive Signals
- (none found, or lists them)

### Negative Signals
- (lists any bearish fundamentals)

### Neutral/Missing Data
- EPS: N/A
- ROE: N/A
(etc.)

### Overall Assessment
Due to missing fundamental data, cannot assess 
financial health. Neutral rating.
```

**Technical Analyst**

**Gets:** Price and volume data

**Analyzes:**
- Is price trending up or down?
- Are momentum indicators bullish or bearish?
- Is RSI oversold (too low) or overbought (too high)?
- Are there volume spikes on price declines?

**Outputs:**
```markdown
## Technical Analysis

### Price Momentum
Stock down -7.72% over period. Clear downtrend.

### Volume Analysis
Volume spike (1.1x average) on decline = selling pressure

### Technical Indicators
- RSI: 0.15 (extremely oversold)
- MACD: Negative crossover (bearish)

### Overall Assessment
Strong bearish momentum. Severe selling pressure.
Technical signals support SELL rating.
```

**News Analyst**

**Gets:** News headlines

**Analyzes:**
- Are headlines positive or negative?
- Any major catalysts (earnings, lawsuits, launches)?
- What's the overall sentiment?

**Outputs:**
```markdown
## News Analysis

### Individual News Impact
- "Amazon launches Tax Central" → POSITIVE (new product)
- "Amazon expands MP3 store" → POSITIVE (growth)
- "French court ruling on pricing" → NEGATIVE (legal risk)

### Major Catalysts
- Product innovation (Tax Central, MP3)
- Minor legal headwind (France)

### Overall Sentiment
Predominantly positive news flow. Growth initiatives.
News supports BUY/HOLD, not SELL.
```

---

### Step 3: Manager Synthesis

The **Explainer Manager** receives all three reports and:

1. **Identifies dominant signal** - Which factor mattered most?
2. **Checks consistency** - Do all three agree?
3. **Explains contradictions** - If not, why?
4. **Assesses confidence** - How reliable is this explanation?

**Example Output:**

```markdown
## Executive Summary
The SELL rating is primarily driven by overwhelmingly 
negative technical signals (RSI 0.15, -7.72% decline). 
This overrode positive news flow and absent fundamental 
data.

## Key Drivers

### Primary Negative Factors
- Technical: Extreme downtrend, oversold RSI, bearish MACD
- Volume spike on decline = strong selling pressure

### Primary Positive Factors
- News: Product launches, business expansion

### Mixed/Neutral Factors
- Fundamentals: All data missing (N/A)

## Consistency Check
- Technical: STRONG SELL ✓
- News: SLIGHT BUY ✗
- Fundamentals: NEUTRAL (no data)

**Verdict:** Signals contradict. Analyst prioritized 
technicals over news.

## Confidence Score: 70/100
Moderate confidence. Technical signal is clear and 
strong, but contradicts news and lacks fundamental 
support.
```

---

## Why This Design?

### Separation of Concerns

Each analyst focuses on ONE thing:
- Fundamental analyst never looks at price charts
- Technical analyst never reads news
- News analyst never analyzes financials

**Why?** Just like real analysts specialize. A fundamental analyst and technical analyst see the world differently.

### Manager Provides Context

The manager understands:
- How analysts weigh different signals
- When to prioritize technicals over fundamentals
- That missing data reduces confidence

**Why?** One AI trying to do everything would get confused. The manager's job is synthesis, not analysis.

### Transparency

Every step is visible:
- See what each analyst found
- See how manager weighted them
- See where signals conflict

**Why?** We want to understand WHY the explanation makes sense, not just accept it blindly.

---

## Real Example: Amazon SELL (Jan 2008)

Let's walk through a real case:

### Input
- **Stock:** Amazon (AMZN)
- **Date:** January 8, 2008
- **Human Rating:** SELL
- **Analyst:** Boyd T

### What Each Analyst Found

**Fundamental Analyst:**
- All metrics = N/A (missing)
- Cannot assess financial health
- **Verdict:** NEUTRAL (no data)

**Technical Analyst:**
- Price down -7.72% in 30 days
- RSI at 0.15 (extremely oversold)
- MACD crossover (bearish)
- Volume spike on decline
- **Verdict:** STRONG SELL

**News Analyst:**
- Amazon Tax Central launch (POSITIVE)
- MP3 store expansion (POSITIVE)
- French legal ruling (NEGATIVE)
- Overall: Positive developments
- **Verdict:** SLIGHT BUY

### Manager's Synthesis

**Observation:** Technical says SELL, News says BUY, Fundamentals say nothing.

**Analysis:**
- Technical signal is strongest (high conviction)
- RSI 0.15 = extreme fear in market
- Price action shows clear downtrend
- News is positive but not strong enough to override severe technical weakness

**Conclusion:**
Analyst heavily weighted technical signals. In a severe downtrend (RSI 0.15), even positive news can't save the stock. Missing fundamentals meant analyst relied purely on price action.

**Confidence:** 70% - Technical logic is sound, but contradicts news and lacks fundamental validation.

---

## Key Takeaways

### What Makes This Special?

1. **Multi-Agent System** - Not one AI trying to do everything
2. **Specialization** - Each agent is an expert in their domain
3. **Hierarchical** - Specialists → Manager (like real analyst teams)
4. **Transparent** - Can see exactly what drove the explanation
5. **Handles Contradictions** - Explicitly identifies when signals disagree

### What We Learned

- **Missing data is common** - Fundamental data often unavailable
- **Technicals can dominate** - Especially in volatile markets (2008 financial crisis!)
- **News isn't always enough** - Positive headlines don't override price collapse
- **Synthesis is hard** - Weighing contradictory signals requires judgment

### For the Presentation

Key points:
- "We built a 4-agent system that specializes like real analysts"
- "Each agent focuses on one data type - no overlap"
- "Manager synthesizes everything and explains contradictions"
- "System handles missing data gracefully"
- "Provides confidence scores based on signal alignment"

---

## Technical Details

### Files Involved

```
src/explainer/
├── agents.py          # Defines the 4 agents
├── tasks.py           # Defines what each agent does
└── orchestrator.py    # Runs the whole process
```

### Agent Definitions (agents.py)

Each agent has:
- **Role:** "Fundamental Analyst", "Technical Analyst", etc.
- **Goal:** What they're trying to accomplish
- **Backstory:** Their expertise and how they think
- **LLM:** Google Gemini (gemini-2.5-flash)

### Task Definitions (tasks.py)

Each task specifies:
- **Input format:** What data the agent receives
- **Output format:** Exact markdown structure expected
- **Constraints:** What they can/cannot do

### Orchestration (orchestrator.py)

The main function `run_multi_analyst_explainer()`:

1. Extracts data for each analyst
2. Creates 3 specialist crews (one agent + one task each)
3. Runs them sequentially (30 seconds each)
4. Passes all outputs to manager
5. Manager synthesizes final explanation
6. Returns complete markdown report



---



Agentic AI Project Documentation
