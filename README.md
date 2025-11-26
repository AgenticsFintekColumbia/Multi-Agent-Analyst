# Agentic Recommendation Explainer & Recommender

**Team Project for Agentic AI, The Data Economy & Fintech**

This project uses multi-agent AI systems to analyze stock analyst recommendations. We built two teams:

1. **Explainer Team** - Explains why a human analyst gave a specific rating
2. **Recommender Team** - Makes its own independent rating recommendation

Everything runs on Google Gemini (free API) + CrewAI (agent framework), with a Streamlit web interface.

---

## What This Does

### Question 1: Explainer (Why did the analyst rate it this way?)
- Takes an IBES analyst recommendation (e.g., "SELL" for Amazon on Jan 8, 2008)
- Analyzes fundamental data (earnings, cash flow, etc.)
- Analyzes technical data (price trends, RSI, volume)
- Analyzes news headlines around that date
- **Output:** A detailed explanation of why the analyst likely gave that rating

### Question 2: Recommender (What should the rating be?)
- Takes the same stock and date
- Runs 3 specialist analysts (Fundamental, Technical, News)
- Portfolio Manager synthesizes all three views
- **Output:** An independent model rating (StrongBuy/Buy/Hold/UnderPerform/Sell)

---

## Getting Started from GitHub

You've received an invitation to the `agentics-project` repository. Here's what to do:

### Step 1: Accept the GitHub Invitation

1. Check your email for the GitHub invitation
2. Click "Accept invitation"
3. You'll be taken to the repository page at: `github.com/[username]/agentics-project`

### Step 2: Download the Project

**Method A: Download ZIP (Easiest - No Git Required)**

1. On the repository page, click the green **Code** button
2. Select **Download ZIP**
3. Save it somewhere easy to find (like your Desktop or Downloads folder)
4. Unzip the file
5. Open the unzipped folder

**Method B: Using Git Clone (If you have Git installed)**

```bash
git clone https://github.com/[username]/agentics-project.git
cd agentics-project
```

Note: Replace `[username]` with the actual GitHub username.

### Step 3: Open Terminal in the Project Folder

**On Windows:**
- Open the unzipped folder
- Hold Shift and right-click in the folder
- Select "Open PowerShell window here" or "Open command window here"

**On Mac:**
- Open the unzipped folder
- Right-click and select "New Terminal at Folder"
- Or drag the folder to Terminal

**On Linux:**
- Navigate to the folder in your file manager
- Right-click and select "Open in Terminal"

---

## Project Structure

```
our-project/
├── data/                          # Stock data (IBES, FUND, NEWS)
│   ├── ciq_dj30_stock_news_2008_24.feather
│   ├── fund_tech_dj30_stocks_2008_24.feather
│   └── ibes_dj30_stock_rec_2008_24.feather
│
├── src/                           # Our code
│   ├── explainer/                 # Explainer team (Question 1)
│   │   ├── agents.py              # 3 analysts + manager
│   │   ├── tasks.py               # What each agent does
│   │   └── orchestrator.py        # Runs the whole team
│   │
│   └── recommender/               # Recommender team (Question 2)
│       ├── agents.py              # 3 analysts + portfolio manager
│       ├── tasks.py               # What each agent does
│       └── orchestrator.py        # Runs the whole team
│
├── docs/                          # Documentation (architecture docs)
│
├── tests/                         # Test scripts
│   ├── test_explainer.py
│   └── test_recommender.py
│
├── data_loader.py                 # Loads data from .feather files
├── gui_app.py                     # Main web app (run this!)
├── .env                           # Your Gemini API key (SECRET!)
├── requirements.txt               # Python packages needed
└── README.md                      # This file
```

---

## Installation (First Time Only)

### Step 1: Check Python Version

You need Python 3.10 or newer. Check if you have it:

```bash
python --version
```

If you don't have Python, download it from [python.org](https://www.python.org/downloads/) and install it. Make sure to check "Add Python to PATH" during installation.

---

### Step 2: Install Required Packages

Open your terminal/command prompt in the project folder and run:

**On Mac/Linux:**
```bash
python3 -m pip install -r requirements.txt
```

**On Windows:**
```bash
python -m pip install -r requirements.txt
```

This installs:
- `streamlit` - Web interface
- `crewai` - Agent framework
- `pandas` - Data handling
- `python-dotenv` - Environment variables
- Other dependencies

This takes 2-3 minutes. Wait until it finishes.

---

### Step 3: Get Your Gemini API Key

We use Google's Gemini AI (it's free!).

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key (looks like: `AIzaSyD...`)

---

### Step 4: Create .env File

In the project folder, create a file called `.env` (the name literally starts with a dot)

**On Windows:** Right-click → New → Text Document → Name it `.env` (remove the .txt)

**On Mac/Linux:** Use a text editor to create `.env`

Put this inside the `.env` file:

```
GEMINI_API_KEY=paste_your_key_here
```

Replace `paste_your_key_here` with your actual API key from Step 3.

**IMPORTANT:** Never share this file or upload it anywhere. It contains your secret key. The `.gitignore` file is already set up to prevent accidentally committing it.

---

## Running the App

### Running the Web Interface (Recommended)

In your terminal, from the project folder:

**On Mac/Linux:**
```bash
python3 -m streamlit run gui_app.py
```

**On Windows:**
```bash
python -m streamlit run gui_app.py
```

Your browser will open automatically to `http://localhost:8501`

**If it doesn't open:**
- Manually open your browser
- Go to `http://localhost:8501`

---

### Using the App

#### Step 1: Choose Mode
- **Explainer** - Explain why analyst gave their rating
- **Recommender** - Get model's own rating

#### Step 2: Select Stock
- Pick a ticker (default: AMZN)
- Pick a specific recommendation date
- Adjust time windows if needed (default: 30 days fund, 7 days news)

#### Step 3: Generate
- Click "Generate Explanation" or "Generate Model Recommendation"
- Wait 30-60 seconds (AI is thinking!)
- Read the output

---

### Running Tests (Optional)

To verify everything works:

**Test Explainer:**
```bash
python tests/test_explainer.py
```

**Test Recommender:**
```bash
python tests/test_recommender.py
```

Both should complete without errors in about 60-90 seconds.

---

## How It Works

### Architecture Overview

Both teams use the same pattern:

```
           Manager
          /    |    \
         /     |     \
    Fund    Tech    News
   Analyst Analyst Analyst
```

### Explainer Team (Question 1)

1. **Data Extraction**
   - Gets fundamental data (EPS, ROE, etc.)
   - Gets technical data (price, RSI, MACD)
   - Gets news headlines

2. **Specialist Analysis**
   - **Fundamental Analyst** analyzes financial metrics
   - **Technical Analyst** analyzes price movements
   - **News Analyst** analyzes headlines and sentiment

3. **Manager Synthesis**
   - **Explainer Manager** reads all three reports
   - Identifies what drove the analyst's rating
   - Checks if signals are consistent
   - Outputs confidence score

### Recommender Team (Question 2)

1. **Data Extraction** (same as Explainer)

2. **Specialist Analysis**
   - **Fundamental Analyst** → gives rating based on fundamentals
   - **Technical Analyst** → gives rating based on technicals
   - **News Analyst** → gives rating based on news

3. **Portfolio Manager Synthesis**
   - Reads all three ratings
   - Weighs them intelligently (not just majority vote!)
   - Considers confidence levels
   - Makes final rating decision
   - Explains reasoning

---

## Example Output

### Explainer Example
```
Stock: AMZN (Amazon)
Date: 2008-01-08
Human Rating: SELL

Executive Summary:
The SELL rating is primarily driven by overwhelmingly negative 
technical signals. RSI at 0.15 shows extreme overselling, while 
MACD indicates strong downtrend. Despite positive news about 
product launches, technicals dominated the decision.

Confidence: 70/100 (Moderate - fundamentals missing, news contradicts)
```

### Recommender Example
```
Stock: AMZN (Amazon)
Date: 2008-01-08

Final Model Rating: SELL
Confidence: Medium

Analyst Ratings:
- Fundamental: HOLD (Low confidence - no data)
- Technical: SELL (High confidence - strong bearish signals)
- News: BUY (High confidence - positive developments)

Manager Decision:
Technical analyst has highest confidence and clearest signal.
Weight: 60% Technical, 30% News, 10% Fundamental
→ Final Rating: SELL
```

---

## Troubleshooting

### "No module named 'streamlit'"
**Fix:** You didn't install packages. Run:
```bash
pip install -r requirements.txt
```

### "No Gemini API key found"
**Fix:** Create the `.env` file with your API key (see Step 5 above)

### "FileNotFoundError: data/..."
**Fix:** Make sure you're running from the project root folder, not inside a subfolder

### "RecursionError" or "maximum recursion depth"
**Fix:** This is already fixed in our code. If you see it, make sure you have the latest version.

### App won't open in browser
**Fix:** Manually go to `http://localhost:8501` in your browser

### API Error / Rate Limit
**Fix:** Wait a minute and try again. Free tier has limits.

---

## Important Notes

### For Team Members

1. **Never commit `.env` file** - It contains your secret API key
2. **Data files are large** - Already in `.gitignore`
3. **Tests take time** - Be patient, AI needs 30-60 seconds per run
4. **Free API limits** - If you get rate limited, wait a few minutes

### What's What

- `gui_app.py` - Main app, start here
- `data_loader.py` - Loads our stock data
- `src/explainer/` - All Explainer code
- `src/recommender/` - All Recommender code
- `tests/` - Test scripts to verify everything works
- `docs/` - Detailed architecture documentation

---

## For the Presentation

### Key Points to Mention

1. **Multi-Agent Architecture**
   - Not just one AI, but teams of specialized AIs
   - Each agent focuses on one type of data
   - Manager synthesizes everything

2. **Real Data**
   - IBES: Analyst recommendations (7,804 records)
   - FUND: Stock prices + fundamentals (128,317 records)
   - NEWS: Company news headlines (141,418 records)

3. **Smart Synthesis**
   - Recommender uses LLM manager (not simple voting)
   - Considers confidence levels
   - Adapts to market context
   - Explains reasoning transparently

4. **Production-Quality**
   - Error handling
   - Clean architecture
   - Separated concerns
   - Extensible design

---

## Team Roles

**Everyone should be able to:**
- Run the app
- Explain what Explainer does
- Explain what Recommender does
- Show a demo

**For deeper questions:**
- Architecture details → See `docs/` folder
- Code structure → See `src/` folders
- How agents work → See `agents.py` files

---

## Getting Help

If something isn't working:

1. **Check this README** - Most issues are covered here
2. **Check the error message** - It usually tells you what's wrong
3. **Google the error** - Someone else probably had the same issue
4. **Ask the team** - We're all learning together!

---

## You're Ready

To run the app:
```bash
python -m streamlit run gui_app.py
```

The system will analyze stock recommendations using our multi-agent AI teams.

---

**Agentic AI, The Data Economy & Fintech Project**
