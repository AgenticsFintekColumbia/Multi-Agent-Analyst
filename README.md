# Agentic Recommendation System

**Team Project for Agentic AI, The Data Economy & Fintech**

A multi-agent AI system that analyzes stock analyst recommendations using specialized AI agents. Built with Google Gemini, CrewAI, FastAPI, and React.

---

## What This Project Does

This project uses teams of specialized AI agents to analyze stock recommendations in two ways:

### 1. **Explainer Team** - "Why did the analyst rate it this way?"
Given a specific analyst recommendation (e.g., "SELL" for Amazon on Jan 8, 2008), the Explainer team:
- Extracts relevant data from the time period before the recommendation
- **Fundamental Analyst** examines financial metrics (earnings, profitability, debt, cash flow)
- **Technical Analyst** evaluates price action (momentum, RSI, MACD, volume patterns)
- **News Analyst** assesses sentiment from headlines (positive/negative catalysts)
- **Explainer Manager** synthesizes all three perspectives to explain why the analyst likely gave that rating
- **Output:** A comprehensive explanation with key signals, consistency analysis, and confidence score

### 2. **Recommender Team** - "What should the rating be?"
Takes the same stock and date, runs three specialist analysts, and a Portfolio Manager synthesizes their independent ratings into a final recommendation:
- **Fundamental Analyst** makes a rating based on financial metrics
- **Technical Analyst** makes a rating based on price/momentum
- **News Analyst** makes a rating based on news sentiment
- **Portfolio Manager** intelligently weighs all three ratings (not just voting!) considering confidence levels and market context
- **Output:** An independent model rating (StrongBuy/Buy/Hold/UnderPerform/Sell) with detailed reasoning

---

## Quick Start

### Prerequisites

You'll need:
- **Python 3.10 or newer** ([Download here](https://www.python.org/downloads/))
- **Node.js 18+ and npm** ([Download here](https://nodejs.org/) - choose LTS version)
- **Google Gemini API Key** ([Get one here](https://aistudio.google.com/app/apikey) - it's free!)

### Installation

1. **Download the project** from GitHub (click Code → Download ZIP, or clone if you have Git)

2. **Open a terminal/command prompt** in the project folder:
   - **VS Code**: Open folder → Terminal → New Terminal
   - **Windows**: Shift+Right-click in folder → "Open PowerShell window here"
   - **Mac/Linux**: Right-click folder → "New Terminal at Folder"

3. **Install Python packages:**
   ```bash
   python -m pip install -r requirements.txt
   ```
   This takes 3-5 minutes. Wait until it finishes.

4. **Set up your API key:**
   - Create a file named `.env` in the project root (copy from `.env.example`)
   - Open `.env` and add your Gemini API key:
     ```
     GEMINI_API_KEY=your_actual_api_key_here
     ```

5. **Run the application:**
   ```bash
   python run.py
   ```
   This automatically:
   - Starts the backend API server
   - Installs frontend dependencies if needed
   - Starts the frontend web app
   - Shows you the URLs to access

6. **Open your browser** to `http://localhost:5173` and start using the app!

**To stop:** Press `Ctrl+C` in the terminal

---

## Project Structure

```
agentics-project/
├── backend/                    # FastAPI backend server
│   ├── api/                   # API endpoints (explainer, recommender, tickers)
│   ├── datasets.py            # Data loading functions
│   ├── utils.py               # Helper functions
│   └── main.py                # FastAPI app entry point
│
├── src/                       # Core agent logic
│   ├── explainer/             # Explainer team
│   │   ├── agents.py          # Agent definitions (4 agents)
│   │   ├── tasks.py           # Task definitions
│   │   └── orchestrator.py    # Main execution flow
│   └── recommender/           # Recommender team
│       ├── agents.py          # Agent definitions (4 agents)
│       ├── tasks.py           # Task definitions
│       └── orchestrator.py    # Main execution flow
│
├── frontend/                  # React web interface
│   └── insight-agent/         # Vite + React + TypeScript app
│
├── data/                      # Stock data (IBES, FUND, NEWS)
│   ├── ibes_dj30_stock_rec_2008_24.feather
│   ├── fund_tech_dj30_stocks_2008_24.feather
│   └── ciq_dj30_stock_news_2008_24.feather
│
├── Docs/                      # Detailed technical documentation
│   ├── Explainer_Team.md      # Explainer architecture deep dive
│   └── Recommender_Team.md    # Recommender architecture deep dive
│
├── tests/                     # Test scripts
├── run.py                     # Single command launcher (starts everything)
├── start_backend.py           # Backend server script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## Using the Application

Once you run `python run.py` and open `http://localhost:5173`:

### Step 1: Choose Mode
- **Explainer** - Explain why a human analyst gave their rating
- **Recommender** - Get the model's own independent rating

### Step 2: Select Stock and Date
- Pick a ticker from the dropdown (default: AMZN)
- Select a specific recommendation date (grouped by year for easy browsing)
- For Explainer: You'll see date + rating (e.g., "January 25 - BUY")
- For Recommender: You'll see only dates (to avoid bias)

### Step 3: Adjust Time Windows (Optional)
- **FUND Window**: Historical fundamental data lookback period (default: 30 days)
- **NEWS Window**: News and sentiment analysis period (default: 7 days for Explainer, 30 days for Recommender)

### Step 4: Generate Analysis
- Click "Run Explainer Team" or "Run Recommender Team"
- Wait 30-90 seconds (AI is thinking!)
- Read the comprehensive analysis output

### Step 5: View Results
- **Explainer**: Manager report explaining why the analyst gave their rating
- **Recommender**: Rating comparison (AI vs Human - click to reveal human rating) + Manager report with final recommendation
- Expand "View detailed work from the 3 analysts" to see individual specialist reports

---

## How It Works (High-Level)

Both teams follow the same multi-agent pattern:

```
           Manager
          /   |   \
         /    |    \
    Fund    Tech    News
   Analyst Analyst Analyst
```

1. **Data Extraction** - Each analyst gets their specific data type
2. **Specialist Analysis** - Each analyst independently analyzes their data
3. **Manager Synthesis** - Manager reads all reports and synthesizes the final output

**Key Difference:**
- **Explainer**: Managers explain WHY a human gave a rating
- **Recommender**: Managers make their OWN rating decision by intelligently weighing all three specialist ratings

For detailed technical architecture, see:
- [Explainer Team Documentation](Docs/Explainer_Team.md)
- [Recommender Team Documentation](Docs/Recommender_Team.md)

---

## Troubleshooting

### "No module named 'xyz'"
**Fix:** Install Python packages:
```bash
python -m pip install -r requirements.txt
```

### "No Gemini API key found"
**Fix:** Create a `.env` file in the project root with:
```
GEMINI_API_KEY=your_key_here
```

### "node is not recognized" or "npm is not recognized"
**Fix:** 
1. Install Node.js from [nodejs.org](https://nodejs.org/) (choose LTS version)
2. **Important:** Close and reopen your terminal after installing
3. If it still doesn't work, restart your computer
4. Verify with: `node --version` and `npm --version`

### "FileNotFoundError: data/..."
**Fix:** Make sure you're running from the project root folder (where `run.py` is located)

### Backend won't start
**Fix:** Check that port 8000 is not already in use. You can change the port in `start_backend.py` if needed.

### Frontend won't start
**Fix:** Check that port 5173 is not already in use. Vite will automatically try the next available port.

### "API Error" or Rate Limit
**Fix:** The free Gemini API has rate limits. Wait a minute and try again.

### App is slow / taking forever
**Fix:** 
- Each analysis takes 60-90 seconds (AI needs time to think!)
- First run loads all datasets (takes 10-20 seconds)
- Subsequent runs are faster

---

## Manual Setup (Alternative)

If you prefer to run components separately:

### Terminal 1 - Backend:
```bash
python start_backend.py
```
Backend runs on: `http://localhost:8000`

### Terminal 2 - Frontend:
```bash
cd frontend/insight-agent
npm install  # Only needed first time
npm run dev
```
Frontend runs on: `http://localhost:5173`

---

## Running Tests

To verify everything works:

**Test Explainer:**
```bash
python tests/test_explainer.py
```

**Test Recommender:**
```bash
python tests/test_recommender.py
```

Both should complete in 60-90 seconds without errors.

---

## Important Notes

### For Developers

1. **Never commit `.env` file** - It contains your secret API key (already in `.gitignore`)

2. **Data files are large** - Already in `.gitignore`, don't commit them

3. **API Key Security** - The `.env` file is local only. Never share it or commit it to Git.

4. **First run is slow** - Datasets load once at backend startup (10-20 seconds)

### Technology Stack

- **Backend:** FastAPI (Python), CrewAI (agent framework), Google Gemini (LLM)
- **Frontend:** React + TypeScript + Vite, Tailwind CSS, Shadcn UI
- **Data:** Pandas DataFrames loaded from Feather files
- **API Communication:** RESTful API with polling for job status

---

## Documentation

- **[README.md](README.md)** - This file (setup and usage)
- **[Docs/Explainer_Team.md](Docs/Explainer_Team.md)** - Technical deep dive: Explainer architecture, code structure, data flow
- **[Docs/Recommender_Team.md](Docs/Recommender_Team.md)** - Technical deep dive: Recommender architecture, code structure, data flow

---

## Key Features

✅ **Multi-Agent Architecture** - Specialized agents, not one AI trying to do everything  
✅ **Real Data** - IBES analyst recommendations, FUND fundamentals/technical data, NEWS headlines  
✅ **Intelligent Synthesis** - LLM-based manager (not simple voting) considers confidence and context  
✅ **Transparent Reasoning** - See exactly what drove each decision  
✅ **Handles Missing Data** - Gracefully manages incomplete information  
✅ **Modern UI** - Beautiful, responsive web interface  

---

## Getting Help

If something isn't working:

1. **Check this README** - Most issues are covered here
2. **Check the error message** - It usually tells you what's wrong
3. **Read the technical docs** - `Docs/Explainer_Team.md` and `Docs/Recommender_Team.md`
4. **Google the error** - Someone else probably had the same issue

---

**Agentic AI, The Data Economy & Fintech Project**
