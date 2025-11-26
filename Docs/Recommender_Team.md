# Recommender Team Architecture



## What Does the Recommender Do?

The Recommender team answers **Question 2** from our project:

> "What rating would our AI model give this stock?"

Unlike the Explainer (which explains a human's decision), the Recommender makes its own independent recommendation: StrongBuy, Buy, Hold, UnderPerform, or Sell.

**Key difference:** We **hide the human analyst's rating** from the user until after the model decides. This prevents bias

---

## Architecture: How It Works

### The Team Structure

```
                Portfolio Manager
               (Final Decision Maker)
                        |
         +--------------+--------------+
         |              |              |
   Fundamental      Technical       News
    Analyst          Analyst       Analyst
         |              |              |
    Analyzes        Analyzes      Analyzes
   Financials      Price Data    Headlines
         |              |              |
    Returns         Returns       Returns
     RATING          RATING        RATING
   + Report        + Report      + Report
```

We have **4 AI agents** working together:

1. **Fundamental Analyst** - Makes rating based on financial metrics
2. **Technical Analyst** - Makes rating based on price/momentum
3. **News Analyst** - Makes rating based on news sentiment
4. **Portfolio Manager** - Synthesizes all three ratings into final decision

---

## Step-by-Step Flow

### Step 1: Data Extraction

When you pick a stock and date in the app:

```python
# Example: Amazon, Jan 8, 2008
cusip = "02313510"  # Amazon's ID
rec_date = "2008-01-08"

# Extract three types of data:
fundamental_metrics = extract_fundamentals(cusip, rec_date)
technical_indicators = extract_technicals(cusip, rec_date)
news_headlines = extract_news(cusip, rec_date)
```

**What each gets:**

1. **Fundamental Analyst:**
   - 30 metrics: EPS growth, ROE, debt ratios, cash flow, margins, etc.
   - Latest values before rec date

2. **Technical Analyst:**
   - 14 indicators: RSI, MACD, price returns, volume, volatility, etc.
   - 30-day window before rec date

3. **News Analyst:**
   - JSON of all news headlines
   - 30-day window around rec date (±30 days)
   - Includes event types (earnings, product, legal)

---

### Step 2: Specialist Analysis (The Three Analysts)

Each analyst makes their own independent rating based solely on their data.

**Fundamental Analyst**

**Gets:** 30 fundamental metrics (EPS, ROE, leverage, cash flow, etc.)

**Analyzes:**
- Earnings quality and growth
- Profitability (ROE, margins)
- Balance sheet health (debt, liquidity)
- Cash flow generation

**Outputs:**
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
Cannot perform fundamental analysis due to 
complete absence of data. Default to Hold 
with low confidence.
```

**Why Hold?** When data is missing, we can't say Buy or Sell. Hold = neutral.

**Technical Analyst**

**Gets:** 14 technical indicators (RSI, MACD, returns, volume, etc.)

**Analyzes:**
- Momentum (recent price trends)
- Technical indicators (RSI, MACD)
- Volume patterns (buying/selling pressure)
- Volatility (risk level)

**Outputs:**
```markdown
## Technical Analysis

### Rating
- **Technical Rating**: Sell
- **Confidence**: High

### Key Signals
- **Bullish**: RSI extremely oversold (0.15)
- **Bearish**: 
  - Negative returns (-1.06% daily, -0.99% 30-day avg)
  - MACD bearish crossover
  - Volume spike on down day (selling pressure)
- **Neutral**: Elevated volatility

### Reasoning
Stock experiencing strong bearish momentum. 
Negative MACD crossover and volume spike on 
decline indicate continued downside risk. 
While RSI oversold, overwhelming bearish 
signals support SELL.
```

**Why Sell?** Clear downtrend + bearish indicators + selling pressure = Sell

**News Analyst**

**Gets:** JSON of news headlines

**Analyzes:**
- Sentiment of each headline (positive/negative/neutral)
- Major catalysts (big events)
- Overall tone

**Outputs:**
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
Positive strategic move expanding into tax 
software and digital downloads. Diversifies 
offerings and enhances value proposition. 
Typically viewed favorably by market.
```

**Why Buy?** Positive product launches = growth = Buy

---

### Step 3: Portfolio Manager Synthesis (The Secret Sauce!)

The **Portfolio Manager** is where the magic happens. Unlike simple voting, this is an **intelligent synthesis**.

**Receives:**
1. Fundamental: HOLD (Low confidence) - no data
2. Technical: SELL (High confidence) - strong bearish signals
3. News: BUY (High confidence) - positive developments

**Thinks:**
- "Three different ratings. How do I decide?"
- "Technical has HIGH confidence with clear data"
- "News has HIGH confidence but contradicts technical"
- "Fundamental has LOW confidence and no data"
- "Which signal should I trust most?"

**Portfolio Manager's Job:**

1. **Extract ratings** from each report
2. **Assess confidence** of each analyst
3. **Identify contradictions** (Technical vs News)
4. **Apply intelligent weighting:**
   - High confidence signals get more weight
   - Clear data beats missing data
   - Technical signals often lead in crisis periods (2008!)

**Outputs:**
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
- Fundamental: 10% (low confidence, no data)
- Technical: 60% (high confidence, clear bearish signals)
- News: 30% (high confidence but contradicts dominant trend)

**Rationale:** Technical analyst has strongest conviction 
with clearest data. RSI 0.15 and MACD crossover show 
severe weakness. While news is positive, in a collapsing 
market (2008 financial crisis), positive headlines cannot 
override technical breakdown.

### Synthesis
During market turmoil, price action reflects reality 
faster than news sentiment. Technical analyst's bearish 
signals are unambiguous. News positivity acknowledged 
but insufficient to counter strong selling pressure.

### Risk Assessment
- **Primary Risk**: Missing fundamentals reduce conviction
- **Data Quality**: Technical data clear; fundamentals absent
```

---

## Why This Design?

### Intelligent Synthesis, Not Simple Voting

**Old approach (simple voting):**
```python
# Fundamental: Hold
# Technical: Sell  
# News: Buy
# All disagree → Default to Hold (arbitrary)
```

**New approach (intelligent manager):**
```python
# Manager thinks:
# - Technical has high confidence → weight 60%
# - News has high confidence but contradicts → weight 30%
# - Fundamental has no data → weight 10%
# Final: Sell (with medium confidence due to contradiction)
```

### Why This Is Better

1. **Considers confidence levels** - High confidence signals matter more
2. **Context-aware** - Understands 2008 was a crisis (technicals lead)
3. **Explains reasoning** - Shows exact weighting logic
4. **Handles contradictions** - Doesn't just pick majority
5. **Provides risk assessment** - Acknowledges uncertainty

---

## Comparison: Explainer vs Recommender

| Aspect | Explainer | Recommender |
|--------|-----------|-------------|
| **Goal** | Explain human's rating | Make own rating |
| **Outputs** | Explanation text | Rating + confidence |
| **Specialist Output** | Analysis report | Rating + report |
| **Manager Output** | Synthesis explanation | Final rating decision |
| **Shows Human Rating?** | Yes (explaining it) | No (avoiding bias) |
| **Confidence** | Explanation confidence | Rating confidence |

---

## Real Example: Amazon (Jan 2008)

### The Scenario

- **Stock:** Amazon
- **Date:** January 8, 2008
- **Context:** Financial crisis beginning
- **Human Analyst:** Gave SELL rating

### Our Model's Decision Process

**Fundamental Analyst:**
```
All data: N/A
Rating: HOLD (can't judge without data)
Confidence: LOW
```

**Technical Analyst:**
```
RSI: 0.15 (extreme fear)
Returns: -7.72% (sharp decline)
MACD: Bearish crossover
Volume: Spike on decline (selling pressure)

Rating: SELL (clear bearish trend)
Confidence: HIGH
```

**News Analyst:**
```
News: Amazon Tax Central launch, MP3 expansion
Sentiment: Positive (growth initiatives)

Rating: BUY (positive developments)
Confidence: HIGH
```

### Portfolio Manager's Synthesis

**Sees:** Technical (SELL) vs News (BUY) conflict

**Thinks:**
1. Technical has clear, unambiguous bearish signals
2. News is positive but doesn't address price collapse
3. In 2008 crisis, fear dominated fundamentals
4. RSI 0.15 = extreme market pessimism
5. Missing fundamentals means can't verify financial health

**Weighs:**
- Technical: 60% (strong signal, high confidence)
- News: 30% (positive but can't override panic)
- Fundamental: 10% (no data available)

**Decides:** SELL (Medium confidence)

**Compares to Human:** Human also said SELL ✓

---

## Key Innovation: LLM-Based Synthesis

### Why Not Just Use Python Logic?

We could have done this:

```python
def combine_ratings(fund, tech, news):
    ratings = [fund, tech, news]
    # Return most common
    return Counter(ratings).most_common()[0][0]
```

**Problems:**
- All ratings weighted equally
- Ignores confidence levels
- Can't handle ties intelligently
- No reasoning or context

### Our Approach: LLM Portfolio Manager

```python
manager = Agent(
    role="Portfolio Manager",
    goal="Synthesize three analyst ratings intelligently",
    backstory="25+ years managing portfolios..."
)
```

**Benefits:**
- Adaptive weighting based on confidence
- Considers market context (crisis vs normal)
- Explains reasoning transparently
- Provides risk assessment
- Can handle complex scenarios

**This is the key differentiator of our project!**

---

## Technical Details

### Files Involved

```
src/recommender/
├── agents.py          # Defines 4 agents
├── tasks.py           # Defines their tasks
└── orchestrator.py    # Runs the process
```

### Agent Definitions

Each agent has:
- **Role:** Specialist area
- **Goal:** Make a rating
- **Backstory:** Expertise (fundamental/technical/news/management)
- **LLM:** Google Gemini (gemini-2.5-flash)
- **Temperature:** 0.2 (more consistent)

### Task Structure

Each specialist task:
- Gets their specific data only
- Must output structured markdown with:
  - Rating (StrongBuy/Buy/Hold/UnderPerform/Sell)
  - Confidence (High/Medium/Low)
  - Key signals (Positive/Negative/Neutral)
  - Reasoning (2-3 sentences)

Manager task:
- Gets all three specialist reports
- Must output:
  - Final rating
  - Analyst summary
  - Signal alignment
  - Weighting logic
  - Synthesis
  - Risk assessment

### Orchestration Flow

```python
def run_multi_analyst_recommendation(...):
    # 1. Extract data
    fundamentals = get_fund_data(cusip, date)
    technicals = get_tech_data(cusip, date)
    news = get_news_data(cusip, date)
    
    # 2. Run three specialists (30 seconds each)
    fund_report = fundamental_analyst.run(fundamentals)
    tech_report = technical_analyst.run(technicals)
    news_report = news_analyst.run(news)
    
    # 3. Manager synthesizes (20 seconds)
    final_rec = portfolio_manager.run(
        fund_report, tech_report, news_report
    )
    
    # 4. Return complete report
    return final_rec
```

**Total runtime:** 60-90 seconds

---

## Why This Matters for Our Project

This demonstrates:

1. **Advanced Multi-Agent Systems** - Not just independent agents, but coordinated team
2. **Intelligent Synthesis** - LLM manager beats simple algorithms
3. **Real-World Application** - Actual investment decision-making
4. **Transparency** - Explainable AI with clear reasoning
5. **Handling Uncertainty** - Gracefully manages missing data and contradictions

Plus it makes actual stock recommendations. And we can compare them to human analysts.

---


