# Codebase Context Documentation

This document provides comprehensive context about the codebase structure, architecture, and integration points. Use this as reference when working on frontend development or modifications.

## Table of Contents
1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Data Flow](#data-flow)
6. [API Endpoints](#api-endpoints)
7. [Data Models](#data-models)
8. [Key Integration Points](#key-integration-points)
9. [Frontend Development Guide](#frontend-development-guide)

---

## Project Overview

This is a **multi-agent AI system** for stock analysis that uses CrewAI to orchestrate specialized AI agents. The system has two main modes:

1. **Explainer Mode**: Explains why a human analyst made a specific recommendation (BUY/SELL/HOLD)
2. **Recommender Mode**: Generates new AI-powered recommendations for stocks

The system consists of:
- **Backend**: FastAPI server (Python) that runs multi-agent CrewAI workflows
- **Frontend**: React/TypeScript application (Vite) that provides a web interface
- **Data**: Three main datasets (IBES, FUND, NEWS) stored as Feather files

---

## Project Structure

```
Agentics Project/
├── backend/                    # FastAPI backend
│   ├── api/                   # API route handlers
│   │   ├── explainer.py       # Explainer endpoints
│   │   ├── recommender.py     # Recommender endpoints
│   │   ├── tickers.py         # Ticker listing endpoint
│   │   ├── recommendations.py # Recommendation listing endpoint
│   │   └── health.py          # Health check endpoint
│   ├── datasets.py            # Dataset loading/caching module
│   ├── utils.py               # Markdown parsing utilities
│   └── main.py                # FastAPI app entry point
│
├── src/                        # Core multi-agent logic
│   ├── explainer/             # Explainer team
│   │   ├── orchestrator.py    # Main explainer orchestration
│   │   ├── agents.py          # Agent definitions
│   │   └── tasks.py           # Task definitions
│   └── recommender/           # Recommender team
│       ├── orchestrator.py    # Main recommender orchestration
│       ├── agents.py          # Agent definitions
│       └── tasks.py           # Task definitions
│
├── frontend/insight-agent/    # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── AnalysisWorkspace.tsx    # Main analysis UI
│   │   │   ├── StockSelector.tsx        # Ticker/recommendation selector
│   │   │   ├── ResultsDisplay.tsx       # Results rendering
│   │   │   └── ui/                       # shadcn/ui components
│   │   ├── lib/
│   │   │   ├── api.ts                    # API client
│   │   │   └── markdown-utils.ts         # Markdown cleaning utilities
│   │   └── pages/
│   │       └── Index.tsx                 # Main page
│   └── package.json
│
├── data/                       # Data files (Feather format)
│   ├── ibes_dj30_stock_rec_2008_24.feather
│   ├── fund_tech_dj30_stocks_2008_24.feather
│   └── ciq_dj30_stock_news_2008_24.feather
│
├── data_loader.py              # Dataset loading utilities
├── start_backend.py            # Backend startup script
└── requirements.txt            # Python dependencies
```

---

## Backend Architecture

### FastAPI Application (`backend/main.py`)

The FastAPI app:
- Loads datasets at startup using `lifespan` context manager
- Configures CORS for frontend communication (ports 5173, 5174, 8080)
- Includes routers for all API endpoints
- Runs on `http://localhost:8000` by default

**Key Components:**
- `lifespan()`: Loads datasets on startup, clears on shutdown
- CORS middleware: Allows frontend to make requests
- Router inclusion: All API routes are prefixed with `/api`

### Dataset Management (`backend/datasets.py`)

**Purpose**: Centralized dataset loading to avoid circular imports.

**Functions:**
- `initialize_datasets(data_dir)`: Loads all three datasets into memory
- `get_datasets()`: Returns cached datasets tuple `(ibes_df, fund_df, news_df)`
- `clear_datasets()`: Clears the cache

**Datasets:**
1. **IBES**: Analyst recommendations with columns like `ticker`, `cusip`, `anndats`, `etext` (rating), `analyst`, `cname`
2. **FUND**: Fundamental and technical data with columns like `cusip`, `date`, `price`, `volume`, `eps_ttm`, `roe`, `rsi_14`, etc.
3. **NEWS**: Company news with columns like `cusip`, `announcedate`, `headline`, `eventtype`

### Markdown Parsing (`backend/utils.py`)

**Purpose**: Parses multi-agent output into structured format for frontend.

**Key Functions:**

1. **`split_manager_and_analysts(markdown_text)`**
   - Splits full markdown into manager report and analyst reports section
   - Looks for marker: `"# 📊 Individual Analyst Reports"`
   - Returns: `(manager_md, analysts_md)`

2. **`parse_analyst_reports(analysts_markdown)`**
   - Extracts individual reports from analyst section
   - Uses regex patterns to find:
     - `## 1️⃣ Fundamental Analyst Report`
     - `## 2️⃣ Technical Analyst Report`
     - `## 3️⃣ News & Sentiment Analyst Report`
   - Returns: `{"fundamental": str, "technical": str, "news": str}`

3. **`extract_final_rating(markdown_text)`**
   - Extracts final rating from recommender output
   - Looks for patterns like "Model Rating: Buy" or "Final Rating: StrongBuy"
   - Returns rating string or None

### API Endpoints

#### 1. Health Check (`/health`)
- **Method**: GET
- **Response**: `{"status": "ok"}`

#### 2. Get Tickers (`/api/tickers`)
- **Method**: GET
- **Response**:
  ```json
  {
    "tickers": ["AMZN", "AAPL", ...],
    "default": "AMZN"
  }
  ```
- **Logic**: Extracts unique tickers from IBES, uses `oftic` if available, falls back to `ticker`

#### 3. Get Recommendations (`/api/recommendations`)
- **Method**: GET
- **Query Params**: `ticker` (required), `mode` ("explainer" or "recommender")
- **Response**:
  ```json
  {
    "recommendations": [
      {
        "index": 123,
        "date": "2024-01-15",
        "rating": "BUY",  // Only for explainer mode
        "analyst": "John Doe",
        "ticker": "AMZN",
        "company": "Amazon.com Inc",
        "cusip": "023135106"
      },
      ...
    ]
  }
  ```
- **Note**: `rating` is `null` for recommender mode (to prevent bias)

#### 4. Run Explainer (`/api/explainer/run`)
- **Method**: POST
- **Body**:
  ```json
  {
    "rec_index": 123,
    "fund_window_days": 30,
    "news_window_days": 7
  }
  ```
- **Response**:
  ```json
  {
    "status": "processing",
    "job_id": "uuid-string",
    "message": "Explainer team is running..."
  }
  ```
- **Process**: Runs `run_multi_analyst_explainer()` in background, parses results

#### 5. Get Explainer Status (`/api/explainer/status/{job_id}`)
- **Method**: GET
- **Response**:
  ```json
  {
    "status": "completed" | "processing" | "error",
    "result": {
      "manager_report": "markdown string",
      "analyst_reports": {
        "fundamental": "markdown string",
        "technical": "markdown string",
        "news": "markdown string"
      },
      "full_markdown": "complete markdown"
    },
    "error": null | "error message"
  }
  ```

#### 6. Run Recommender (`/api/recommender/run`)
- **Method**: POST
- **Body**:
  ```json
  {
    "rec_index": 123,
    "news_window_days": 30,
    "ticker": "AMZN",
    "company": "Amazon.com Inc"
  }
  ```
- **Response**: Same format as explainer run

#### 7. Get Recommender Status (`/api/recommender/status/{job_id}`)
- **Method**: GET
- **Response**: Same format as explainer status, but includes `final_rating` field:
  ```json
  {
    "status": "completed",
    "result": {
      "manager_report": "...",
      "analyst_reports": {...},
      "full_markdown": "...",
      "final_rating": "Buy"  // Extracted rating
    },
    "error": null
  }
  ```

### Multi-Agent Orchestration

#### Explainer (`src/explainer/orchestrator.py`)

**Function**: `run_multi_analyst_explainer(ibes_df, fund_df, news_df, rec_index, fund_window_days, news_window_days)`

**Process**:
1. Extracts data for the recommendation:
   - Fundamental data (last `fund_window_days` days)
   - Technical data (price, volume, indicators)
   - News data (±`news_window_days` days)
2. Creates three specialist agents:
   - Fundamental Analyst
   - Technical Analyst
   - News & Sentiment Analyst
3. Runs agents in parallel (CrewAI `Process.sequential`)
4. Creates Manager agent to synthesize reports
5. Returns combined markdown report

**Output Format**:
```markdown
# Manager Report
[Manager's synthesis of all three analysts]

---

# 📊 Individual Analyst Reports

## 1️⃣ Fundamental Analyst Report
[Fundamental analysis content]

---

## 2️⃣ Technical Analyst Report
[Technical analysis content]

---

## 3️⃣ News & Sentiment Analyst Report
## News Analysis
[News analysis content]
```

#### Recommender (`src/recommender/orchestrator.py`)

**Function**: `run_multi_analyst_recommendation(cusip, rec_date, fund_df, news_df, news_window_days, ticker, company)`

**Process**: Similar to explainer, but:
- Doesn't have access to the human analyst's rating (to prevent bias)
- Generates a new recommendation instead of explaining an existing one
- Output includes a final rating (StrongBuy/Buy/Hold/UnderPerform/Sell)

---

## Frontend Architecture

### Tech Stack
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + shadcn/ui components
- **Markdown**: `react-markdown` for rendering
- **HTTP Client**: Native `fetch` API (wrapped in `apiClient`)

### Component Structure

#### 1. Main Page (`pages/Index.tsx`)
- Entry point with mode selection (Explainer vs Recommender)
- Routes to `AnalysisWorkspace` when mode is selected

#### 2. Analysis Workspace (`components/AnalysisWorkspace.tsx`)
- **State Management**:
  - `selectedTicker`: Currently selected stock ticker
  - `selectedRecommendation`: Selected recommendation object
  - `fundWindow`: Days for fundamental data (default: 30)
  - `newsWindow`: Days for news data (default: 7)
  - `isLoading`: Loading state during analysis
  - `results`: Analysis results object

- **Flow**:
  1. User selects ticker → loads recommendations
  2. User selects recommendation → enables generate button
  3. User clicks generate → calls API, polls for status
  4. Results displayed in `ResultsDisplay` component

#### 3. Stock Selector (`components/StockSelector.tsx`)
- **Features**:
  - Fetches tickers from `/api/tickers` on mount
  - Fetches recommendations when ticker changes
  - Shows recommendation details (date, rating, analyst)
  - Hides rating in recommender mode

- **API Calls**:
  - `apiClient.getTickers()`
  - `apiClient.getRecommendations(ticker, mode)`

#### 4. Results Display (`components/ResultsDisplay.tsx`)
- **Features**:
  - Shows manager report (main card)
  - Shows final rating comparison (recommender only)
  - Collapsible section for individual analyst reports
  - Uses `ReactMarkdown` for rendering
  - Applies `extractFormattedReport()` to clean markdown

- **Structure**:
  ```tsx
  <Card>Manager Report</Card>
  {recommender && <Card>Rating Comparison</Card>}
  <Collapsible>
    <Card>Fundamental Analyst Report</Card>
    <Card>Technical Analyst Report</Card>
    <Card>News & Sentiment Analyst Report</Card>
  </Collapsible>
  ```

### API Client (`lib/api.ts`)

**Class**: `ApiClient`

**Methods**:
- `getTickers()`: Returns `{tickers: string[], default: string}`
- `getRecommendations(ticker, mode)`: Returns `{recommendations: Recommendation[]}`
- `runExplainer(request)`: Starts explainer job, returns `{job_id, status, message}`
- `getExplainerStatus(jobId)`: Returns job status
- `runRecommender(request)`: Starts recommender job
- `getRecommenderStatus(jobId)`: Returns job status
- `pollJobStatus(jobId, mode, onProgress?)`: Polls until complete, calls `onProgress` callback

**Configuration**:
- Base URL: `import.meta.env.VITE_API_URL || 'http://localhost:8000'`
- Polling interval: 2.5 seconds
- Error handling: Network errors show user-friendly messages

### Markdown Utilities (`lib/markdown-utils.ts`)

**Functions**:

1. **`cleanMarkdown(markdown)`**
   - Removes LLM planning text (e.g., "Here's my plan:", "I need to...")
   - Removes planning sections
   - Cleans up formatting

2. **`extractFormattedReport(markdown)`**
   - Finds first `##` header (start of actual report)
   - Returns content from that point forward
   - Fallback: calls `cleanMarkdown()`

**Usage**: Applied to all markdown before rendering in `ResultsDisplay`

---

## Data Flow

### Explainer Flow

```
User selects ticker
  ↓
Frontend: GET /api/tickers → Backend returns tickers
  ↓
User selects recommendation
  ↓
Frontend: GET /api/recommendations?ticker=X&mode=explainer
  ↓
User clicks "Generate"
  ↓
Frontend: POST /api/explainer/run {rec_index, fund_window_days, news_window_days}
  ↓
Backend: Creates job_id, starts background task
  ↓
Backend: Calls run_multi_analyst_explainer()
  ├─ Extracts data (fundamental, technical, news)
  ├─ Runs 3 specialist agents (parallel)
  ├─ Runs manager agent (synthesis)
  └─ Returns markdown report
  ↓
Backend: Parses markdown
  ├─ split_manager_and_analysts() → (manager_md, analysts_md)
  └─ parse_analyst_reports() → {fundamental, technical, news}
  ↓
Backend: Stores result in _jobs[job_id]
  ↓
Frontend: Polls GET /api/explainer/status/{job_id} every 2.5s
  ↓
Frontend: When status === "completed", displays results
  ├─ Manager report (main card)
  └─ Analyst reports (collapsible section)
```

### Recommender Flow

Similar to explainer, but:
- Uses `/api/recommender/run` and `/api/recommender/status/{job_id}`
- Rating is hidden in recommendation selector
- Results include `final_rating` field
- Shows rating comparison card

---

## API Endpoints Summary

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/health` | GET | Health check | `{status: "ok"}` |
| `/api/tickers` | GET | List available tickers | `{tickers: [], default: string}` |
| `/api/recommendations` | GET | List recommendations for ticker | `{recommendations: []}` |
| `/api/explainer/run` | POST | Start explainer job | `{job_id, status, message}` |
| `/api/explainer/status/{id}` | GET | Get explainer job status | `{status, result, error}` |
| `/api/recommender/run` | POST | Start recommender job | `{job_id, status, message}` |
| `/api/recommender/status/{id}` | GET | Get recommender job status | `{status, result, error}` |

---

## Data Models

### TypeScript Interfaces (`lib/api.ts`)

```typescript
interface Ticker {
  tickers: string[];
  default: string;
}

interface Recommendation {
  index: number;
  date: string | null;
  rating: string | null;  // null for recommender mode
  analyst: string;
  ticker: string;
  company: string;
  cusip: string;
}

interface ExplainerRequest {
  rec_index: number;
  fund_window_days: number;
  news_window_days: number;
}

interface RecommenderRequest {
  rec_index: number;
  news_window_days: number;
  ticker: string;
  company: string;
}

interface JobResponse {
  status: 'processing';
  job_id: string;
  message: string;
}

interface JobStatus {
  status: 'processing' | 'completed' | 'error';
  result: {
    manager_report: string;
    analyst_reports: {
      fundamental: string;
      technical: string;
      news: string;
    };
    full_markdown: string;
    final_rating?: string;  // Only for recommender
  } | null;
  error: string | null;
}
```

### Backend Pydantic Models

```python
class ExplainerRequest(BaseModel):
    rec_index: int
    fund_window_days: int = 30
    news_window_days: int = 7

class RecommenderRequest(BaseModel):
    rec_index: int
    news_window_days: int = 30
    ticker: str = "N/A"
    company: str = "N/A"
```

---

## Key Integration Points

### 1. CORS Configuration
- **Location**: `backend/main.py`
- **Allowed Origins**: `http://localhost:5173`, `5174`, `8080` (and `127.0.0.1` variants)
- **Methods**: All (`*`)
- **Headers**: All (`*`)

### 2. Dataset Loading
- **Startup**: Datasets loaded once in `lifespan()` function
- **Access**: All API routes use `get_datasets()` from `backend.datasets`
- **Caching**: Datasets stored in global `_datasets_cache`

### 3. Job Management
- **Storage**: In-memory dictionary `_jobs: Dict[str, Dict]`
- **Job ID**: UUID string
- **States**: `"processing"`, `"completed"`, `"error"`
- **Note**: In production, use Redis or database

### 4. Markdown Parsing
- **Input**: Full markdown from CrewAI agents
- **Process**:
  1. Split manager vs analysts section
  2. Extract individual analyst reports using regex
  3. Clean up formatting
- **Output**: Structured object with `manager_report` and `analyst_reports`

### 5. Polling Mechanism
- **Implementation**: `apiClient.pollJobStatus()`
- **Interval**: 2.5 seconds
- **Stops when**: `status === "completed"` or `status === "error"`
- **Progress Callback**: Optional `onProgress` callback for UI updates

---

## Frontend Development Guide

### Adding New Components

1. **Create component file** in `src/components/`
2. **Use TypeScript** with proper interfaces
3. **Import UI components** from `@/components/ui/`
4. **Use Tailwind classes** for styling
5. **Follow existing patterns** from `AnalysisWorkspace.tsx` or `StockSelector.tsx`

### Styling Guidelines

- **Use shadcn/ui components** for consistency
- **Tailwind classes**: Follow existing patterns
- **Dark mode**: Components should support dark mode (use `dark:` variants)
- **Responsive**: Use `lg:`, `md:`, `sm:` breakpoints
- **Colors**: 
  - Explainer: `explainer` color (defined in Tailwind config)
  - Recommender: `recommender` color
  - Muted: `muted-foreground` for secondary text

### API Integration

1. **Add new endpoint** to `lib/api.ts`:
   ```typescript
   async newEndpoint(params): Promise<ResponseType> {
     return this.request<ResponseType>('/api/new-endpoint', {
       method: 'POST',
       body: JSON.stringify(params),
     });
   }
   ```

2. **Use in component**:
   ```typescript
   const data = await apiClient.newEndpoint({...});
   ```

### Markdown Rendering

1. **Import ReactMarkdown**:
   ```typescript
   import ReactMarkdown from "react-markdown";
   ```

2. **Apply cleaning**:
   ```typescript
   import { extractFormattedReport } from "@/lib/markdown-utils";
   
   <ReactMarkdown>
     {extractFormattedReport(markdownString)}
   </ReactMarkdown>
   ```

3. **Use prose classes** for styling:
   ```tsx
   <div className="prose prose-sm max-w-none dark:prose-invert">
     <ReactMarkdown>...</ReactMarkdown>
   </div>
   ```

### State Management

- **Local state**: Use `useState` for component-specific state
- **No global state**: Currently no Redux/Zustand (can be added if needed)
- **Props drilling**: Pass state down through props (consider context if it gets complex)

### Error Handling

- **API errors**: Caught in `apiClient.request()`, throw user-friendly errors
- **Component errors**: Use try-catch in async functions, show alerts or error states
- **Loading states**: Always show loading indicators during async operations

### Testing the Frontend

1. **Start backend**: `python start_backend.py`
2. **Start frontend**: `cd frontend/insight-agent && npm run dev`
3. **Open browser**: `http://localhost:5173`
4. **Check console**: For API errors or debug logs

---

## Common Patterns

### Polling Pattern
```typescript
const status = await apiClient.pollJobStatus(jobId, mode, (progress) => {
  // Optional: Update UI with progress
  console.log("Progress:", progress.status);
});
```

### Loading State Pattern
```typescript
const [isLoading, setIsLoading] = useState(false);

const handleAction = async () => {
  setIsLoading(true);
  try {
    const result = await apiClient.someAction();
    // Handle result
  } catch (error) {
    // Handle error
  } finally {
    setIsLoading(false);
  }
};
```

### Conditional Rendering Pattern
```typescript
{isLoading ? (
  <LoadingComponent />
) : results ? (
  <ResultsComponent results={results} />
) : (
  <EmptyState />
)}
```

---

## Environment Variables

### Backend
- `.env` file in project root
- Required: `GOOGLE_API_KEY` (for CrewAI/Gemini)
- Loaded via `python-dotenv` in `backend/main.py`

### Frontend
- `.env` file in `frontend/insight-agent/`
- Optional: `VITE_API_URL` (defaults to `http://localhost:8000`)

---

## Dependencies

### Backend (`requirements.txt`)
- `fastapi>=0.104.0`
- `uvicorn[standard]>=0.24.0`
- `pydantic>=2.0.0`
- `pandas`
- `pyarrow` (for Feather files)
- `python-dotenv`
- `crewai` (multi-agent framework)

### Frontend (`package.json`)
- `react`, `react-dom`
- `typescript`
- `vite`
- `tailwindcss`
- `@tailwindcss/typography` (for markdown prose)
- `react-markdown`
- `lucide-react` (icons)
- `shadcn/ui` components

---

## Notes for Frontend Development

1. **Backend must be running** on port 8000 for frontend to work
2. **CORS is configured** for localhost ports 5173, 5174, 8080
3. **Job polling** happens automatically - no manual polling needed
4. **Markdown cleaning** is important - LLM outputs often include planning text
5. **Error messages** should be user-friendly (check `apiClient` for examples)
6. **Loading states** are crucial - analysis can take 30-60 seconds
7. **Responsive design** - test on mobile/tablet views
8. **Dark mode** - ensure components work in both light and dark themes

---

## Extending the System

### Adding New Analysis Modes

1. **Backend**: Create new orchestrator in `src/`
2. **Backend**: Add API router in `backend/api/`
3. **Backend**: Add endpoint to `backend/main.py`
4. **Frontend**: Add mode to `AppMode` type
5. **Frontend**: Add UI for mode selection
6. **Frontend**: Create mode-specific components if needed

### Adding New Data Sources

1. **Load data** in `data_loader.py`
2. **Add to datasets** tuple in `backend/datasets.py`
3. **Update orchestrators** to use new data
4. **Update frontend** to display new data if needed

### Improving Markdown Parsing

- **Location**: `backend/utils.py`
- **Regex patterns**: Update patterns in `parse_analyst_reports()`
- **Testing**: Test with actual LLM outputs to ensure patterns match
- **Fallbacks**: Always include fallback patterns for robustness

---

This documentation should provide sufficient context for understanding the codebase and making frontend modifications. For specific implementation details, refer to the actual source files.

