# Industry News Scanner - Beginner Learning Guide

Welcome! This guide will help you understand the codebase step-by-step, from architecture overview to detailed file explanations.

## 📐 Architecture Overview

### High-Level Flow

```
User clicks "Start Scan" (Frontend)
    ↓
POST /api/scan (Backend API)
    ↓
Stage 1: Collect News
    ├─ RSS Feeds → NewsItem[]
    └─ OR Web Search → NewsItem[]
    ↓
Stage 2: AI Analysis
    ├─ Load background.md (strategic context)
    ├─ For each NewsItem:
    │   ├─ Call AI API with context
    │   └─ Parse response → AnalyzedReportItem
    └─ Sort by importance (High > Medium > Low)
    ↓
Return ScanReport (JSON)
    ↓
Frontend displays results
```

### Technology Stack

- **Backend**: Python + FastAPI (web framework)
- **Frontend**: Vanilla JavaScript (no frameworks)
- **Data Validation**: Pydantic (type-safe models)
- **AI Integration**: Custom AI client (supports OpenAI, Anthropic, custom APIs)
- **RSS Parsing**: feedparser library
- **Web Search**: Custom search client (supports multiple providers)

---

## 🗺️ Learning Path: File-by-File Guide

Follow this order to understand the codebase from simple to complex:

### Phase 1: Foundation (Start Here!)

#### 1. `backend/models.py` ⭐ **START HERE**
**Why**: This defines the data structures used throughout the app. Understanding this first helps you understand everything else.

**What to focus on**:
- `NewsItem`: Raw news data from RSS/web search
  - Fields: `title`, `url`, `source`, `published_date`, `description`, `content`
  - This is what Stage 1 produces
  
- `AnalyzedReportItem`: News after AI analysis
  - Fields: `importance`, `confidence`, `why_it_matters`, `evidence`, `recommended_actions`
  - This is what Stage 2 produces
  
- `ScanReport`: Final output combining all analyzed items
  - Contains summary counts and list of `AnalyzedReportItem`s

**Key concepts**:
- **Pydantic models**: Type-safe data validation (Python will check types automatically)
- **Enum**: `Importance` is an enum (HIGH, MEDIUM, LOW) - prevents typos
- **Optional fields**: Fields marked `Optional[str]` can be `None`

**Learning exercise**: 
- Try creating a `NewsItem` object in Python: `NewsItem(title="Test", url="http://test.com", source="Test")`
- Notice how Pydantic validates the data automatically

---

#### 2. `backend/config.py` ⭐ **IMPORTANT**
**Why**: Central configuration management. All settings (API keys, file paths, time windows) are loaded here.

**What to focus on**:
- **Environment variables**: Reads from `.env` file using `python-dotenv`
- **File paths**: Defines where `background.md` and `rss_feeds.json` are located
- **Auto-detection**: Automatically detects which AI provider you're using
- **Helper functions**: 
  - `load_rss_feeds()`: Loads RSS feed list
  - `load_background_md()`: Loads strategic context
  - `validate_config()`: Checks if everything is set up correctly

**Key concepts**:
- **Environment variables**: Sensitive data (API keys) stored in `.env` file (not in code)
- **Path management**: Uses `pathlib.Path` for cross-platform file paths
- **Configuration pattern**: Single source of truth for all settings

**Learning exercise**:
- Check your `.env` file (if exists) - see what variables are set
- Try calling `validate_config()` to see what's configured

---

### Phase 2: Core Business Logic

#### 3. `backend/scanner.py` ⭐⭐⭐ **CORE LOGIC**
**Why**: This is the heart of the application - implements the Two-Stage Scan workflow.

**What to focus on**:

**Stage 1 Functions**:
- `stage1_collect_rss()`: 
  - Reads RSS feeds from config
  - Parses each feed using `feedparser`
  - Filters by time window (last 48 hours)
  - Deduplicates by title+URL
  - Returns `List[NewsItem]`
  
- `stage1_collect_web()`:
  - Generates search keywords using AI
  - Performs web searches
  - Converts results to `NewsItem` format
  - Filters by date (last 30 days)
  - Deduplicates

- `generate_search_keywords()`:
  - Uses AI to generate keywords based on `background.md`
  - Prioritizes high-effectiveness keywords from past searches
  - Falls back to hardcoded keywords if AI fails

**Stage 2 Function**:
- `stage2_analyze_with_ai()`:
  - Takes `List[NewsItem]` from Stage 1
  - Loads `background.md` for context
  - For each news item:
    - Calls AI API with news + context
    - Parses AI response
    - Creates `AnalyzedReportItem`
  - Sorts by importance (High > Medium > Low)
  - Updates keyword statistics (for web search)
  - Returns `List[AnalyzedReportItem]`

**Key concepts**:
- **Deduplication**: Uses `Set[str]` with `title|url` as key to avoid duplicates
- **Time filtering**: Only processes recent items (configurable window)
- **Error handling**: Continues processing even if one item fails
- **Rate limiting**: Adds delays between AI API calls to avoid overwhelming the API
- **Retry logic**: Retries on connection errors (SSL/EOF issues)

**Learning exercise**:
- Trace through `stage1_collect_rss()` step by step
- Understand how deduplication works (line 53-56)
- See how time filtering works (line 64-66)

---

#### 4. `backend/ai_client.py` ⭐⭐
**Why**: Handles all AI API communication. Abstracts away the complexity of different AI providers.

**What to focus on**:
- **`AIClient` class**: 
  - Auto-detects provider (OpenAI, Anthropic, custom)
  - Handles different API formats
  - Manages API keys and endpoints
  
- **`analyze_news_item()`**: 
  - Builds prompt with `background.md` context
  - Calls AI API
  - Parses JSON response (with robust error handling)
  - Returns structured data
  
- **`generate_search_keywords()`**: 
  - Generates search keywords based on strategic context
  - Returns list of keyword strings

**Key concepts**:
- **Abstraction**: Hides complexity of different AI providers behind one interface
- **Prompt engineering**: Carefully constructs prompts to get desired output format
- **JSON parsing**: Robust parsing handles malformed AI responses
- **Error handling**: Graceful fallbacks if API calls fail

**Learning exercise**:
- Look at how the prompt is constructed (search for `build_analysis_prompt`)
- Understand the JSON parsing fallback logic (`_parse_json_response`)

---

#### 5. `backend/web_search.py` ⭐
**Why**: Handles web search functionality (alternative to RSS feeds).

**What to focus on**:
- **`WebSearchClient` class**: 
  - Supports multiple providers (Tavily, Perplexity, Bing, AI Builders)
  - Auto-detects provider from config
  - Abstracts search API differences
  
- **`search()` method**: 
  - Takes keyword, returns list of search results
  - Each result has: `title`, `url`, `description`, `source`

**Key concepts**:
- **Provider abstraction**: Same interface for different search APIs
- **Auto-detection**: Automatically uses available API keys

---

### Phase 3: API Layer

#### 6. `backend/main.py` ⭐⭐ **API ENTRY POINT**
**Why**: This is the web server - handles HTTP requests and coordinates the workflow.

**What to focus on**:

**FastAPI Setup**:
- Creates FastAPI app instance
- Configures CORS (allows frontend to call backend)
- Serves static files (frontend HTML/CSS/JS)

**Endpoints**:
- `GET /health`: Health check - verifies configuration
- `GET /api`: API information
- `POST /api/scan`: **Main endpoint** - triggers Two-Stage Scan
  - Accepts `ScanRequest` (with `search_source`: "rss" or "web")
  - Calls Stage 1 (RSS or web search)
  - Calls Stage 2 (AI analysis)
  - Returns `ScanReport`

**Key concepts**:
- **FastAPI**: Modern Python web framework (like Flask but faster)
- **Request/Response models**: Uses Pydantic for automatic validation
- **Async functions**: `async def` allows handling multiple requests concurrently
- **Error handling**: Catches exceptions and returns HTTP error responses
- **CORS**: Cross-Origin Resource Sharing - allows frontend on different port to call API

**Learning exercise**:
- Start the server: `python3 -m uvicorn backend.main:app --reload`
- Visit `http://localhost:8000/docs` to see auto-generated API documentation
- Try calling `/health` endpoint

---

### Phase 4: Frontend

#### 7. `frontend/app.js` ⭐
**Why**: Client-side JavaScript that handles user interaction and displays results.

**What to focus on**:

**Main Functions**:
- `startScan()`: 
  - Gets selected search source (RSS or web)
  - Calls `POST /api/scan`
  - Shows loading state
  - Handles errors
  - Displays results
  
- `displayReport()`: 
  - Groups items by importance (High/Medium/Low)
  - Renders HTML for each group
  - Creates expandable/collapsible items
  
- `createReportItem()`: 
  - Creates DOM elements for each news item
  - Handles click to expand/collapse details
  - Shows importance badges, confidence, source link

**Key concepts**:
- **DOM manipulation**: Creates HTML elements dynamically
- **Event listeners**: Responds to button clicks
- **Async/await**: Handles asynchronous API calls
- **Error handling**: Shows user-friendly error messages
- **State management**: Tracks current report, loading state

**Learning exercise**:
- Open `frontend/index.html` in browser
- Open browser DevTools (F12) → Console tab
- Click "Start Scan" and watch console logs
- Inspect the DOM to see how elements are created

---

#### 8. `frontend/index.html` & `frontend/styles.css`
**Why**: HTML structure and styling.

**What to focus on**:
- **HTML structure**: Basic layout with buttons, containers, loading indicators
- **CSS classes**: Used by JavaScript to show/hide elements
- **Responsive design**: Works on mobile and desktop

---

### Phase 5: Supporting Files

#### 9. `backend/keyword_manager.py` ⭐
**Why**: Manages keyword effectiveness tracking for web search.

**What to focus on**:
- Tracks which keywords find high/medium/low importance items
- Calculates effectiveness scores
- Prioritizes high-effectiveness keywords for future searches

**Key concepts**:
- **Learning system**: Improves over time by tracking what works
- **JSON persistence**: Saves statistics to `search_keywords.json`

---

#### 10. `background.md` ⭐⭐ **BUSINESS LOGIC**
**Why**: This is the "brain" - defines what's important and how to analyze news.

**What to focus on**:
- **Strategic context**: Defines the business goals (OKRs)
- **Importance criteria**: Rules for High/Medium/Low classification
- **Filtering rules**: What to exclude (noise)
- **Monitoring scope**: What topics to track
- **Output format**: How AI should structure responses

**Key concepts**:
- This file is loaded and sent to AI as context
- AI uses this to determine importance and generate analysis
- Changing this file changes how the system behaves

---

## 🔗 How Everything Connects

### Request Flow Example

1. **User clicks "Start Scan"** (`frontend/app.js`)
   ```javascript
   startScan() → fetch('/api/scan', {search_source: 'rss'})
   ```

2. **Backend receives request** (`backend/main.py`)
   ```python
   @app.post("/api/scan")
   async def scan_news(request: ScanRequest)
   ```

3. **Stage 1: Collect News** (`backend/scanner.py`)
   ```python
   news_items = stage1_collect_rss()  # Returns List[NewsItem]
   ```

4. **Stage 2: Analyze** (`backend/scanner.py`)
   ```python
   analyzed_items = stage2_analyze_with_ai(news_items)  # Returns List[AnalyzedReportItem]
   ```

5. **Create Report** (`backend/main.py`)
   ```python
   report = ScanReport(items=analyzed_items, ...)  # Returns ScanReport
   ```

6. **Frontend displays** (`frontend/app.js`)
   ```javascript
   displayReport(report)  # Renders HTML
   ```

---

## 🎯 Key Concepts to Master

### 1. **Data Flow**
```
RSS/Web → NewsItem → AI Analysis → AnalyzedReportItem → ScanReport → Frontend Display
```

### 2. **Two-Stage Architecture**
- **Stage 1**: Collection (gathers raw news)
- **Stage 2**: Analysis (adds strategic context via AI)

### 3. **Type Safety with Pydantic**
- Models validate data automatically
- Prevents bugs from wrong data types
- Auto-generates API documentation

### 4. **Error Handling Patterns**
- Try/except blocks catch errors
- Continue processing even if one item fails
- User-friendly error messages

### 5. **Configuration Management**
- Environment variables for secrets
- JSON files for data (RSS feeds, keywords)
- Markdown file for business logic (background.md)

---

## 📚 Learning Exercises

### Beginner Level
1. **Read `models.py`** and create a `NewsItem` object manually
2. **Run `test_setup_verification.py`** to verify your environment
3. **Start the server** and visit `/docs` to explore the API
4. **Read `background.md`** to understand the business logic

### Intermediate Level
1. **Trace a request** from frontend click to backend response
2. **Modify `stage1_collect_rss()`** to add a new field to `NewsItem`
3. **Add a new endpoint** in `main.py` (e.g., `/api/stats`)
4. **Modify the frontend** to display a new field

### Advanced Level
1. **Add a new search provider** to `web_search.py`
2. **Implement caching** to avoid re-analyzing same news items
3. **Add authentication** to protect the API
4. **Optimize AI prompts** to improve analysis quality

---

## 🐛 Common Patterns You'll See

### 1. **Deduplication Pattern**
```python
seen_items: Set[str] = set()
dedupe_key = f"{title.lower()}|{url}"
if dedupe_key in seen_items:
    continue  # Skip duplicate
seen_items.add(dedupe_key)
```

### 2. **Error Handling Pattern**
```python
try:
    # Do something risky
    result = risky_operation()
except Exception as e:
    print(f"Error: {e}")
    continue  # Skip and continue processing
```

### 3. **Configuration Loading Pattern**
```python
# Load from environment
value = os.getenv("KEY", "default")

# Load from JSON
with open("file.json") as f:
    data = json.load(f)
```

### 4. **API Call Pattern**
```python
response = requests.post(url, json=data, headers=headers)
if response.status_code == 200:
    result = response.json()
else:
    raise Exception(f"API error: {response.status_code}")
```

---

## 🎓 Next Steps

1. **Read the files in order** (Phase 1 → Phase 5)
2. **Run the tests** to see how things work:
   ```bash
   python3 backend/tests/test_setup_verification.py
   python3 backend/tests/test_rss_collection.py
   ```
3. **Start the server** and try the API:
   ```bash
   python3 -m uvicorn backend.main:app --reload
   ```
4. **Make a small change** and see what happens (e.g., change a print statement)
5. **Read the code comments** - they explain why, not just what

---

## 💡 Tips for Learning

- **Don't try to understand everything at once** - focus on one file at a time
- **Run the code** - seeing it work helps understanding
- **Make small changes** - modify something and see what breaks
- **Read error messages** - they often point to the problem
- **Use print statements** - add `print()` to see what values variables have
- **Read the tests** - they show how functions are supposed to be used

---

## 📖 Additional Resources

- **FastAPI docs**: https://fastapi.tiangolo.com/
- **Pydantic docs**: https://docs.pydantic.dev/
- **Python pathlib**: https://docs.python.org/3/library/pathlib.html
- **JavaScript async/await**: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function

---

Happy learning! 🚀

