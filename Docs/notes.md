Press the preview button on the top right corner to see the markdown (its better formatting)

## 1. Big-picture story (what this system does)

* Goal of the project:

  * Use **IBES analyst recommendations + FUND data + NEWS headlines** to:

    1. Build a **context snapshot** around a specific recommendation.
    2. Ask an **LLM agent** (Gemini via CrewAI) to explain *why* the analyst likely gave that rating.
* Current status:

  * Backend pipeline is working.
  * Explainer agent is working.
  * Simple GUI lets you explore recommendations and trigger explanations.

**One-liner you can say:**

> “Given any IBES recommendation, we pull the last 30 days of price/fundamentals and the surrounding news, bundle that into a text context, and send it to a Gemini-based agent that explains the analyst’s SELL/BUY/HOLD decision.”

---

## 2. Repo / file structure (talk through this once)

You can sketch this on the board:

```text
project/
  data/
    ibes_dj30_stock_rec_2008_24.feather
    fund_tech_dj30_stocks_2008_24.feather
    ciq_dj30_stock_news_2008_24.feather
  data_loader.py
  agents.py
  tasks.py
  crew_config.py
  main.py
  gui_app.py
  requirements.txt
```

**What each core file does:**

* `data_loader.py`

  * Loads the three `.feather` files with pandas.
  * Parses date columns.
  * Standardizes `cusip` so joins work.
  * Provides:

    * `load_datasets(data_dir="data/")`
    * `build_context_for_rec(...)` → returns `(context_str, rec_row)`.

* `agents.py`

  * Defines the **Explainer agent** using `crewai.Agent` and `LLM` (Gemini).
  * Contains `create_explainer_agent()`.

* `tasks.py`

  * Defines the **Explainer task** – what we actually ask the agent to do and what the output format should look like.
  * Contains `create_explainer_task(agent, context_str)`.

* `crew_config.py`

  * Wires the agent + task into a `Crew` object.
  * Contains `create_explainer_crew(context_str)`.

* `main.py`

  * CLI entry point.
  * Loads data, builds context for a single rec, runs the Explainer crew, prints the explanation.

* `gui_app.py`

  * Streamlit web UI:

    * pick ticker & recommendation
    * see the context
    * click a button to run the Explainer and view markdown output.

---

## 3. Data → context pipeline (how the finance part works)

**Datasets:**

* **IBES** (recommendations):

  * Key cols: `['ticker', 'cusip', 'cname', 'analyst', 'anndats', 'ereccd', 'etext', 'ireccd', 'itext']`
  * `anndats` = recommendation / announcement date.

* **FUND** (price + fundamentals):

  * Key cols you actually show: `['date', 'price', 'daily_return_adjusted', 'volume', 'eps_ttm', 'roe', 'leverage']`.
  * `date` is trading date.

* **NEWS**:

  * Key cols: `['cusip', 'headline', 'eventtype', 'situation', 'sourcetypename', 'announcedate']`.

**Joining logic:**

All joins are by **`cusip`**.

For a selected IBES row:

1. Get `cusip` and `rec_date = anndats`.
2. **FUND window**:

   * Filter FUND where:

     * same `cusip`
     * `date` in `[rec_date - fund_window_days, rec_date - 1]`.
3. **NEWS window**:

   * Filter NEWS where:

     * same `cusip`
     * `announcedate` in `[rec_date - news_window_days, rec_date + news_window_days]`.

**`build_context_for_rec(...)` outputs a text block with three sections:**

1. **IBES Recommendation**

   * Ticker, company, CUSIP, dates, analyst name.
   * `ereccd/etext` and `ireccd/itext` (expected vs investment recommendation text/codes).

2. **Recent price & fundamentals (FUND)**

   * Bullet list of rows like:

     * `* 2008-01-02: price=96.25, daily_return_adj=0.03897, volume=13,866,390, eps_ttm=..., roe=..., leverage=...`

3. **Company news (NEWS)**

   * Bullet list of headlines:

     * `* 2008-01-07: Amazon.com Inc. Launches Amazon Tax Central (eventtype=Product-Related Announcements, ...)`

This entire string is what you feed into the agent as “context”.

**Simple way to explain this:**

> “For each recommendation we basically reconstruct the local market environment: recent price moves, fundamentals, and news headlines, all keyed on the same CUSIP and aligned around the recommendation date.”

---

## 4. Agentic layer (CrewAI + Gemini)

### Explainer agent (`agents.py`)

* Uses `crewai.LLM` with `model="gemini-2.5-flash"` and your Gemini API key.
* Agent role: **“Sell-Side Equity Analyst Explainer.”**
* Backstory:

  * 15+ years on Wall Street.
  * Knows how to reason from price action, fundamentals, and news.
* Critical rules baked into the prompt:

  * Only use the provided context (IBES/FUND/NEWS).
  * Don’t invent events or numbers.
  * Acknowledge missing data (N/A).
  * Explain the rating, not predict future performance.

### Explainer task (`tasks.py`)

* Description includes:

  * Context string (IBES + FUND + NEWS).
  * Step-by-step instructions: examine rating, analyze price, review fundamentals, map news, synthesize rationale, assess consistency, assign confidence score.

* **Output format is strictly specified:**

  ```markdown
  ## Summary
  ...

  ## Detailed Rationale
  - **Positive drivers**
    - ...
  - **Negative factors / risks**
    - ...
  - **Valuation / price action considerations**
    - ...

  ## News Mapping
  - "<headline 1>" → ...

  ## Consistency & Confidence
  - Consistency: ...
  - Confidence score (0–100): <number> – <reason>
  ```

* The task explicitly tells the LLM:

  * “Do NOT include preambles like ‘I will follow these steps.’ Start directly with `## Summary`.”

### Crew (`crew_config.py`)

* `create_explainer_crew(context_str)`:

  * Instantiates the Explainer agent.
  * Instantiates the Explainer task with that context.
  * Wraps both in a `Crew(process=Process.sequential, verbose=True)`.
* `crew.kickoff()` returns the markdown explanation string.

**One-sentence explanation for your group:**

> “CrewAI just gives us a clean way to define an agent, define a task, and then run them together; the heavy lifting is still done by Gemini with our custom prompt and context.”

---

## 5. CLI vs GUI flows

### CLI (`main.py`)

1. Load `.env` to get the Gemini key.
2. Check that `GEMINI_API_KEY` or `GOOGLE_API_KEY` is present.
3. `load_datasets("data/")`
4. Choose a `rec_index` (currently 0).
5. `build_context_for_rec(...)`.
6. Print:

   * Selected IBES row summary.
   * Context string.
7. Build crew with `create_explainer_crew(context_str)` and call `kickoff()`.
8. Print the markdown explanation.

**Run it like:**

```bash
python main.py
```

---

### GUI (`gui_app.py` using Streamlit)

Workflow:

1. On startup:

   * Load env vars and check API key.
   * Call `get_datasets()` (cached) → loads IBES, FUND, NEWS once.

2. Sidebar:

   * Show dataset sizes.
   * **Ticker selectbox**: choose ticker (default AMZN).
   * Filter IBES to that ticker.
   * **Recommendation selectbox**: choose a specific IBES row, labeled as:

     * `"global_index | date | rating | analyst"`
   * Sliders for:

     * FUND window days (before rec date).
     * NEWS window days (±).

3. Main panel:

   * “Selected IBES Recommendation”:

     * `st.metric` for Ticker, Company, Recommendation Date (string), IBES Rating.
     * Expander to show full IBES row as a dict.
   * “Context”:

     * Calls `build_context_for_rec(...)` with chosen index and windows.
     * Expander to view raw text context.
   * “Run Explainer Agent”:

     * Button → on click:

       * Create crew with `create_explainer_crew(context_str)`.
       * Run `kickoff()`.
       * Show markdown explanation.

**You can say:**

> “The GUI is just a thin Streamlit wrapper: it lets you pick a recommendation, view the reconstructed context, and then trigger the Explainer agent and view its markdown output.”

---

## 6. Talking points for the meeting

If they ask…

**“What’s agentic about this?”**

* The system is organized around an **agent** with a specific role, backstory, and constraints.
* It performs a **task** defined in code and uses the context we build, rather than just a one-off prompt.
* We can easily extend to multiple agents (e.g., Recommender, Critic) coordinated by a Crew.

**“What’s the main design decision?”**

* The choice to **center everything on the context builder**:

  * Clean separation:

    * Data engineering (`data_loader.py`)
    * Reasoning (`agents.py` / `tasks.py`)
    * Orchestration (`crew_config.py`, `main.py`, `gui_app.py`)
  * Means we can swap models, tweak prompts, or change windows without touching the core logic.

**“How will we extend this?”**

* Add a **Recommender agent** that outputs its own BUY/HOLD/SELL.
* Run batch evaluations over many IBES rows and compare:

  * LLM vs analyst,
  * LLM vs simple baselines (majority, momentum).
* Add ablations: remove news / remove fundamentals and see how performance changes.

---

If you want, next I can draft:

* A short slide-friendly diagram of the pipeline, or
* A 1-paragraph project abstract you can drop into a doc or slide 1.
