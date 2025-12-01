# Live Demo Script: Explainer & Recommender
**Total Time: ~70 seconds (35 seconds each)**

---

## Explainer Demo (35 seconds)

### Script:

"Let me start with the Explainer, which answers a specific question: why did a human analyst give this rating?"

**[Click: Select "Explainer" mode]**

**[Click: Select ticker "MSFT" (or another stock)]**

**[Click: Select date with a visible rating, e.g. "Mar 20, 2012 - SELL"]**

"Notice that in Explainer mode, the human rating is visible upfront—that's what we're trying to explain. Here we have a SELL rating from March 2012."

**[Click: Click "Run Explainer Team" button]**

"The Explainer analyzes the data that was available *before* this recommendation date, then synthesizes an explanation of the analyst's reasoning."

**[Wait 2-3 seconds, then show results:]**

"The output shows the Manager's explanation: key drivers, positive and negative factors, and a confidence assessment. In this case, it identifies declining fundamentals, negative technical momentum, and concerning news as the likely reasons for the SELL rating."

**[Click: Expand analyst reports if needed]**

"Each specialist's report is available for detail. The Explainer also includes confidence scores—here it's 75 out of 100, indicating moderate confidence in the explanation."

"The system acknowledges when data is missing and doesn't hallucinate numbers, which is crucial for trustworthiness."

---

## Recommender Demo (35 seconds)

### Script:

"Now let's switch to Recommender mode, which makes an independent AI rating decision."

**[Click: Select "Recommender" mode]**

**[Click: Select ticker "AAPL" from dropdown]**

**[Click: Select date "Jan 15, 2010" from date picker]**

"Notice that in Recommender mode, the human analyst's rating is hidden—we don't want the AI to be biased by what humans said."

**[Click: Click "Run Recommender Team" button]**

"Once I click run, the system processes this through our four-agent pipeline. The three specialists analyze fundamentals, technicals, and news, then the Portfolio Manager synthesizes their ratings."

**[Wait 2-3 seconds, then click to show results if pre-run, OR explain:]**

"Here we see the model's final rating—in this case, it's recommending a **Buy** with high confidence. The Manager explains its weighting logic: why it gave fundamentals 60% weight versus technicals at 30%, based on the signal strength and market context."

**[Click: Expand "View detailed work from the 3 analysts" if needed]**

"You can see each specialist's individual analysis and their confidence levels. And if I reveal the human rating..."

**[Click: Click to reveal human rating if available]**

"...we can compare. The model said Buy, and the human analyst also said Buy—they agreed in this case."

---

## Demo Tips & Notes

### Pre-Demo Setup:
- **Option 1 (Recommended):** Pre-run both analyses before the presentation, then just show results
- **Option 2:** Start analyses during demo and explain what's happening (acknowledge the 60-90 second wait)
- **Option 3:** Use pre-recorded screen capture if timing is critical

### Key UI Elements to Highlight:
- **Mode selection toggle** - Shows the two different use cases
- **Stock/date picker** - Demonstrates historical data access
- **Rating visibility difference** - Hidden in Recommender, visible in Explainer
- **Progress indicators** - Show multi-agent processing
- **Manager report** - The synthesized output
- **Analyst reports** - Expandable detail
- **Confidence scores** - Quantitative uncertainty

### Timing Breakdown:

**Explainer (35s):**
- Setup & explanation: 10s
- Run & show results: 20s
- Highlight confidence & data handling: 5s

**Recommender (35s):**
- Setup & explanation: 10s
- Run & show results: 20s
- Compare with human: 5s

### Backup Plan:
If the demo fails or takes too long, have screenshots ready to show the key outputs and explain what the system would produce.

