# Agentic Recommendation System

> A multi-agent AI system that analyzes stock analyst recommendations using specialized AI agents and LLM orchestration.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)

**Team Project for Agentic AI, The Data Economy & Fintech**

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [Detailed Setup](#detailed-setup)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Testing](#testing)

---

## Overview

This system leverages specialized AI agents to provide two distinct analytical capabilities for stock recommendations:

### System Architecture

Both Explainer and Recommender follow this multi-agent pattern:

```
                    ┌─────────────────┐
                    │  Manager Agent  │
                    │  (Synthesizes)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ Fundamental │  │  Technical  │  │    News     │
    │   Analyst   │  │   Analyst   │  │   Analyst   │
    └─────────────┘  └─────────────┘  └─────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
    Financial Data   Price/Volume Data  News Headlines
```

**Execution Flow:**
1. **Data Extraction** - Each analyst receives domain-specific filtered data
2. **Parallel Analysis** - Analysts independently evaluate their data sources
3. **Synthesis** - Manager reads all reports and creates final output
4. **Result Delivery** - Comprehensive report with reasoning and confidence

### 🔍 Explainer Mode
**Goal:** Understand *why* a human analyst made their recommendation

Given a historical analyst recommendation (e.g., "SELL" for AMZN on 2008-01-08), the system:
- Analyzes historical data from the period *before* the recommendation
- Deploys three specialist analysts (Fundamental, Technical, News)
- Synthesizes findings to explain the analyst's reasoning
- Provides confidence assessment and key signal identification

### 💡 Recommender Mode
**Goal:** Generate an *independent* AI-driven recommendation

For the same stock and date:
- Three specialist analysts independently evaluate the situation
- Each provides their own rating with confidence levels
- A Portfolio Manager intelligently synthesizes (not just votes!) the ratings
- Outputs a final recommendation with detailed reasoning

**Key Distinction:** Explainer *interprets* human decisions; Recommender *makes* independent decisions.

---

## Key Features

- ✅ **Multi-Agent Architecture** - Specialized agents with distinct expertise domains
- ✅ **Real Financial Data** - IBES analyst recommendations, fundamental metrics, technical indicators, news sentiment
- ✅ **LLM-Based Synthesis** - Intelligent decision-making that considers confidence levels and market context
- ✅ **Transparent Reasoning** - Full visibility into each agent's analysis and the final synthesis
- ✅ **Graceful Degradation** - Handles missing or incomplete data appropriately
- ✅ **Modern Web Interface** - Responsive React UI with real-time status updates

**Tech Stack:**
- Backend: FastAPI, CrewAI, Google Gemini, Pandas
- Frontend: React, TypeScript, Vite, Tailwind CSS, Shadcn UI
- Data: Feather format for efficient DataFrame storage

---

## Quick Start

### Prerequisites Checklist

Before proceeding, ensure you have:

- [ ] Python 3.10 or higher ([Download](https://www.python.org/downloads/))
- [ ] Node.js 18+ and npm ([Download](https://nodejs.org/))
- [ ] Google Gemini API key ([Get one free](https://aistudio.google.com/app/apikey))
- [ ] Git (optional, for cloning)

**Verify installations:**
```bash
python --version  # Should show 3.10 or higher
node --version    # Should show 18 or higher
npm --version     # Should show 9 or higher
```

### Installation (5 Minutes)

1. **Get the code:**
   ```bash
   git clone <repository-url>
   cd agentics-project
   ```

2. **Set up Python environment:**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   
   # Install dependencies
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure API key:**
   
   Create a `.env` file in the project root:
   ```bash
   # Windows PowerShell
   New-Item -Path .env -ItemType File
   
   # Mac/Linux
   touch .env
   ```
   
   Add your API key to `.env`:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

4. **Launch the application:**
   ```bash
   python run.py
   ```
   
   **Wait ~30-60 seconds** for the system to start. You'll see output like:
   ```
   ✓ Loaded 7804 IBES recommendations
   ✓ Loaded 128317 FUND rows
   ✓ Loaded 141418 NEWS items
   SUCCESS: Backend is ready!
   
   VITE v5.4.19  ready in 2236 ms
   ➜  Local:   http://localhost:8080/
   ```
   
   **Open the Local URL** shown in your terminal (usually `http://localhost:8080/` or `http://localhost:5173/`)

**That's it!** The script handles frontend dependency installation automatically.

> **Note:** The frontend port may vary (5173, 8080, 5174, etc.). Always use the URL shown in your terminal output under "Local:"

---

## Technical Deep Dive

**For detailed technical architecture and implementation details, see:**
- [Explainer Team Documentation](Docs/Explainer_Team.md) - Data flow, agent prompts, synthesis logic
- [Recommender Team Documentation](Docs/Recommender_Team.md) - Rating methodology, weighting strategy

---

## Detailed Setup

### Python Environment Setup

#### Option A: Virtual Environment (Recommended)

Virtual environments isolate project dependencies and prevent conflicts.

**Windows:**
```powershell
# Create environment
python -m venv venv

# Activate
venv\Scripts\activate

# You'll see (venv) in your prompt
```

**Mac/Linux:**
```bash
# Create environment
python3 -m venv venv

# Activate
source venv/bin/activate

# You'll see (venv) in your prompt
```

**Install packages:**
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

⚠️ **Important:** Activate the virtual environment every time you open a new terminal.

#### Option B: Global Installation

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

⚠️ **Warning:** Global installation may cause conflicts with other Python projects.

### API Key Configuration

The application requires a Google Gemini API key for LLM access.

**Step 1: Obtain API Key**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key

**Step 2: Create Configuration File**

Create `.env` in the project root (same directory as `run.py`):

```bash
# Unix-based systems (Mac/Linux)
touch .env

# Windows PowerShell
New-Item -Path .env -ItemType File

# Windows Command Prompt
echo. > .env
```

**Step 3: Add API Key**

Open `.env` in any text editor and add:
```
GEMINI_API_KEY=your_actual_api_key_here
```

Replace `your_actual_api_key_here` with your actual key.

🔒 **Security Note:** The `.env` file is in `.gitignore` and will never be committed to version control.

### Verify Installation

Test that everything is configured correctly:

```bash
# Test Explainer team
python tests/test_explainer.py

# Test Recommender team
python tests/test_recommender.py
```

Both tests should complete in 60-90 seconds without errors.

---

## Usage Guide

### Starting the Application

**Standard Launch (Recommended):**
```bash
python run.py
```

This single command:
- Checks Node.js installation
- Installs frontend dependencies (first run only)
- Starts the backend API (port 8000)
- Starts the frontend dev server (port 5173)
- Shows you the access URLs

**Manual Launch (Alternative):**

If you prefer to run components separately or `run.py` doesn't work:

```bash
# Terminal 1 - Backend
python start_backend.py

# Terminal 2 - Frontend
cd frontend/insight-agent
npm install  # First time only
npm run dev
```

**Important:** Always check the terminal output for the actual URLs. The frontend URL may be different from the defaults shown here.

### Using the Web Interface

**Open your browser** to the Local URL shown in the terminal (e.g., `http://localhost:8080/`).

Once the app is loaded:

**1. Select Analysis Mode**
   - **Explainer:** Understand why a human analyst gave their rating
   - **Recommender:** Get an independent AI-generated rating

**2. Choose Stock and Date**
   - Select ticker from dropdown (default: AMZN)
   - Pick a recommendation date (grouped by year)
   - Explainer shows: date + rating (e.g., "Jan 25 - BUY")
   - Recommender shows: date only (to avoid bias)

**3. Adjust Time Windows (Optional)**
   - **FUND Window:** Days of historical fundamental data (default: 30)
   - **NEWS Window:** Days of news to analyze (default: 7 for Explainer, 30 for Recommender)

**4. Run Analysis**
   - Click "Run Explainer Team" or "Run Recommender Team"
   - Wait 30-90 seconds for AI processing
   - Progress indicators show current agent activity

**5. Review Results**
   - **Explainer:** Comprehensive explanation of analyst reasoning
   - **Recommender:** AI rating vs. human rating (click to reveal) + detailed reasoning
   - Expand "View detailed work from the 3 analysts" for individual reports

### API Endpoints

For programmatic access or integration:

**Backend API:** `http://localhost:8000`
**API Documentation:** `http://localhost:8000/docs` (interactive Swagger UI)

**Key Endpoints:**
- `GET /tickers` - List available stock tickers
- `GET /recommendations/{ticker}` - Get recommendation dates for a ticker
- `POST /explainer` - Run Explainer analysis
- `POST /recommender` - Run Recommender analysis
- `GET /job/{job_id}` - Check analysis job status

### Understanding Output

**Explainer Report Structure:**
- **Key Signals:** Most important indicators from each analyst
- **Consistency Check:** How well the signals align with the rating
- **Confidence Assessment:** How certain we are about the explanation
- **Individual Reports:** Full analysis from each specialist

**Recommender Report Structure:**
- **Final Rating:** AI's recommendation (StrongBuy/Buy/Hold/UnderPerform/Sell)
- **Rating Comparison:** AI vs. Human (after reveal)
- **Synthesis Rationale:** Why the Portfolio Manager chose this rating
- **Confidence Levels:** How certain each analyst was
- **Individual Reports:** Full analysis from each specialist

---

## Troubleshooting

### Common Issues and Solutions

#### Python Issues

**"python: command not found" or "python is not recognized"**

- **Windows:** 
  - Reinstall Python and check "Add Python to PATH"
  - Try `py` instead: `py -m pip install -r requirements.txt`
  - Use full path: `C:\Python310\python.exe`
  
- **Mac/Linux:**
  - Try `python3` instead: `python3 -m pip install -r requirements.txt`
  - Install via homebrew: `brew install python3`

**"No module named 'xyz'"**

- Ensure virtual environment is activated (look for `(venv)` in prompt)
- Reinstall dependencies: `pip install -r requirements.txt`
- Upgrade pip first: `pip install --upgrade pip`

#### Node.js Issues

**"node is not recognized" or "npm is not recognized"**

1. Install Node.js from [nodejs.org](https://nodejs.org/) (LTS version)
2. **Close and reopen your terminal** (very important!)
3. Verify: `node --version` and `npm --version`
4. If still failing, restart your computer

**Windows-specific:**
- Check if Node.js is in PATH: `C:\Program Files\nodejs`
- Close and reopen VS Code if using its terminal

#### API Key Issues

**"No Gemini API key found"**

1. Verify `.env` exists in project root (same folder as `run.py`)
2. Check filename is exactly `.env` (not `.env.txt`)
3. Ensure content is: `GEMINI_API_KEY=your_key` (no spaces around `=`)
4. Virtual environment must be activated when running

**Windows Note:** Notepad may save as `.env.txt`. Use "Save As" → "All Files" type.

**"API rate limit exceeded"**

The free Gemini API has rate limits. Wait 1-2 minutes and retry.

#### Port Conflicts

**"Port 8000 already in use"**

Find and kill the process:
```powershell
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9
```

**"Port 5173 already in use"**

Vite automatically uses the next available port (5174, 5175, etc.). Check terminal output for the actual URL.

#### Data Issues

**"FileNotFoundError: data/..."**

You're not in the project root directory. Navigate there:
```bash
# Check current directory
pwd  # Mac/Linux
Get-Location  # Windows PowerShell

# Should end with your project folder name
cd /path/to/agentics-project
```

#### Virtual Environment Issues

**"venv: command not found" (Mac/Linux)**

Try: `python3 -m venv venv`

**PowerShell execution policy error (Windows)**

Run PowerShell as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or use Command Prompt instead of PowerShell.

#### Performance Issues

**"Analysis is taking too long"**

This is normal! Each analysis:
- Takes 60-90 seconds (LLM inference is slow)
- First run loads datasets (adds 10-20 seconds)
- Involves 4 agents making sequential LLM calls

**Be patient and let it complete.**

### Getting Additional Help

1. Check error messages carefully - they usually indicate the problem
2. Review this README's troubleshooting section
3. Read the technical documentation in `Docs/`
4. Search for the error message online
5. Verify all prerequisites are correctly installed

---

## Project Structure

```
agentics-project/
│
├── backend/                           # FastAPI backend server
│   ├── api/                          # API route handlers
│   │   ├── explainer.py              # Explainer endpoint
│   │   ├── recommender.py            # Recommender endpoint
│   │   └── tickers.py                # Data retrieval endpoints
│   ├── datasets.py                   # Data loading and caching
│   ├── utils.py                      # Helper utilities
│   └── main.py                       # FastAPI application entry
│
├── src/                              # Core agent orchestration logic
│   ├── explainer/                    # Explainer team implementation
│   │   ├── agents.py                 # 4 agent definitions + prompts
│   │   ├── tasks.py                  # CrewAI task definitions
│   │   └── orchestrator.py           # Execution coordinator
│   └── recommender/                  # Recommender team implementation
│       ├── agents.py                 # 4 agent definitions + prompts
│       ├── tasks.py                  # CrewAI task definitions
│       └── orchestrator.py           # Execution coordinator
│
├── frontend/                         # React web interface
│   └── insight-agent/                # Vite + React + TypeScript app
│       ├── src/
│       │   ├── components/           # React components
│       │   ├── lib/                  # Utilities
│       │   └── App.tsx               # Main application
│       ├── package.json              # Node dependencies
│       └── vite.config.ts            # Vite configuration
│
├── data/                             # Stock market datasets
│   ├── ibes_dj30_stock_rec_2008_24.feather    # Analyst recommendations
│   ├── fund_tech_dj30_stocks_2008_24.feather  # Fundamental + technical data
│   └── ciq_dj30_stock_news_2008_24.feather    # News headlines + sentiment
│
├── Docs/                             # Technical documentation
│   ├── Explainer_Team.md             # Explainer architecture deep dive
│   └── Recommender_Team.md           # Recommender architecture deep dive
│
├── tests/                            # Test scripts
│   ├── test_explainer.py             # Explainer integration test
│   └── test_recommender.py           # Recommender integration test
│
├── run.py                            # One-command launcher (recommended)
├── start_backend.py                  # Backend server script
├── requirements.txt                  # Python dependencies
├── .env                              # API keys (create this, not in repo)
├── .gitignore                        # Git exclusions
└── README.md                         # This file
```

---

## Documentation

- **[README.md](README.md)** - Setup guide, usage instructions, troubleshooting (this file)
- **[Docs/Explainer_Team.md](Docs/Explainer_Team.md)** - Technical deep dive: architecture, data flow, prompts, synthesis logic
- **[Docs/Recommender_Team.md](Docs/Recommender_Team.md)** - Technical deep dive: rating methodology, weighting strategy, decision-making

---

## Testing

### Integration Tests

Verify the complete agent pipeline:

```bash
# Test Explainer workflow
python tests/test_explainer.py

# Test Recommender workflow  
python tests/test_recommender.py
```

Expected results:
- No errors or exceptions
- Completion in 60-90 seconds
- Output showing agent reasoning and final report

### Manual Testing

Use the web interface to test various scenarios:

1. **Different stocks:** Try multiple tickers to see varied analyses
2. **Different time periods:** Test dates across different market conditions
3. **Window adjustments:** Modify FUND and NEWS windows to see impact
4. **Edge cases:** Try dates with limited data availability

---

## Development Notes

### For Contributors

**Security:**
- Never commit `.env` file (already in `.gitignore`)
- Never commit API keys in code or documentation
- Review `.gitignore` before committing large files

**Data Files:**
- Dataset files are in `.gitignore` (too large for repo)
- Datasets are cached after first load (10-20 second startup time)

**Code Style:**
- Python: Follow PEP 8 guidelines
- TypeScript: ESLint configuration in frontend
- Use type hints in Python code
- Use TypeScript interfaces for data structures

**Performance Considerations:**
- Each LLM call takes 5-15 seconds
- 4 agents per analysis = ~60-90 seconds total
- Consider batch processing for multiple analyses
- Datasets are loaded once at startup, then cached in memory

### Technology Decisions

**Why CrewAI?**
- Provides agent orchestration framework
- Handles task sequencing and memory management
- Integrates well with various LLM providers

**Why Google Gemini?**
- Free tier for development
- Good performance for analytical tasks
- Reliable API availability

**Why FastAPI?**
- Modern async Python framework
- Automatic API documentation
- Excellent performance for I/O-bound tasks

**Why React + Vite?**
- Fast development experience
- Modern build tooling
- Great TypeScript support

---

## License



---

## Acknowledgments



---

## Support

For issues, questions, or contributions:
- Review this README and troubleshooting section
- Check the technical documentation in `Docs/`
- Search existing issues (if using GitHub)
- Create a new issue with detailed error information

---
