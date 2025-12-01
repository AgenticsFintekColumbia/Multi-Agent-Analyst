# Live Demo Script: Explainer & Recommender
**Total Time: 2 minutes (1 minute each)**

---

## Explainer Demo (1 minute)

Let me start with the Explainer, which answers a specific question: why did a human analyst give this rating?

Notice that in Explainer mode, the human rating is visible upfront—that's what we're trying to explain. Here we have a Hold rating from October 21.

The Explainer analyzes the data that was available *before* this recommendation date. It runs three specialist agents—Fundamental, Technical, and News—each analyzing their domain, then the Manager synthesizes an explanation of the analyst's reasoning.

Here's the output. The Manager's explanation identifies key drivers: declining fundamentals, negative technical momentum, and concerning news as the likely reasons for the SELL rating.

It includes confidence scores—here it's 75 out of 100—and explicitly acknowledges when data is missing rather than hallucinating numbers.

You can see each specialist's individual analysis. The system is transparent about its reasoning process.

---

## Recommender Demo (1 minute)

Now let's switch to Recommender mode, which makes an independent AI rating decision.

Notice that in Recommender mode, the human analyst's rating is hidden—we don't want the AI to be biased by what humans said.

The Recommender follows the same four-agent pipeline, but with a different goal: making its own rating decision. The three specialists each provide their own rating with confidence levels, then the Portfolio Manager synthesizes them using intelligent weighting.

Here we see the model's final rating—in this case, it's recommending a **Buy** with high confidence.

The Manager explains its weighting logic: why it gave fundamentals 60% weight versus technicals at 30%, based on signal strength and market context. This isn't just voting—it's an intelligent synthesis.

You can see each specialist's individual rating and confidence. And if I reveal the human rating, we can compare. The model said Buy, and the human analyst also said Buy—they agreed in this case. This demonstrates how the Recommender can provide independent analysis that sometimes aligns with human judgment.


