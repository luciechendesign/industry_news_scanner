# Quick Reference - File Overview

## 🎯 Essential Files (Read These First)

| File | Purpose | Complexity | Key Concepts |
|------|---------|------------|--------------|
| `backend/models.py` | Data structures | ⭐ Easy | Pydantic models, type safety |
| `backend/config.py` | Configuration | ⭐ Easy | Environment variables, file paths |
| `backend/scanner.py` | Core logic | ⭐⭐⭐ Hard | Two-stage workflow, deduplication |
| `backend/main.py` | API server | ⭐⭐ Medium | FastAPI, endpoints, CORS |
| `frontend/app.js` | Frontend logic | ⭐⭐ Medium | DOM manipulation, async/await |
| `background.md` | Business rules | ⭐⭐ Medium | Strategic context, importance criteria |

## 📁 File Structure

```
Industry_news/
├── backend/
│   ├── models.py          ← Data structures (START HERE)
│   ├── config.py           ← Configuration management
│   ├── scanner.py          ← Core business logic (Two-Stage Scan)
│   ├── ai_client.py        ← AI API communication
│   ├── web_search.py       ← Web search functionality
│   ├── keyword_manager.py  ← Keyword effectiveness tracking
│   ├── main.py             ← FastAPI web server
│   └── tests/              ← Test suite
├── frontend/
│   ├── index.html          ← HTML structure
│   ├── app.js              ← JavaScript logic
│   └── styles.css          ← Styling
├── background.md            ← Strategic context (business logic)
├── rss_feeds.json          ← RSS feed configuration
└── search_keywords.json    ← Keyword statistics (auto-generated)
```

## 🔄 Data Flow

```
User Action
    ↓
frontend/app.js (startScan)
    ↓
POST /api/scan
    ↓
backend/main.py (scan_news)
    ↓
backend/scanner.py (stage1_collect_rss/web)
    ↓ Returns: List[NewsItem]
    ↓
backend/scanner.py (stage2_analyze_with_ai)
    ↓ Uses: backend/ai_client.py
    ↓ Returns: List[AnalyzedReportItem]
    ↓
backend/main.py (create ScanReport)
    ↓ Returns: ScanReport (JSON)
    ↓
frontend/app.js (displayReport)
    ↓
User sees results
```

## 🧩 Key Functions

### Stage 1: Collection
- `stage1_collect_rss()` → `List[NewsItem]`
- `stage1_collect_web()` → `List[NewsItem]`
- `generate_search_keywords()` → `List[str]`

### Stage 2: Analysis
- `stage2_analyze_with_ai(news_items)` → `List[AnalyzedReportItem]`

### API Endpoints
- `GET /health` - Health check
- `POST /api/scan` - Trigger scan

### Configuration
- `load_rss_feeds()` → `List[Dict]`
- `load_background_md()` → `str`
- `validate_config()` → `Dict[str, bool]`

## 📊 Data Models

### NewsItem (Raw News)
```python
{
    "title": str,
    "url": str,
    "source": str,
    "published_date": Optional[str],
    "description": Optional[str],
    "content": Optional[str]
}
```

### AnalyzedReportItem (After AI Analysis)
```python
{
    "title": str,
    "source": str,
    "url": str,
    "importance": "high" | "medium" | "low",
    "confidence": float (0.0-1.0),
    "why_it_matters": List[str],
    "evidence": str,
    "recommended_actions": List[str],
    ...
}
```

### ScanReport (Final Output)
```python
{
    "total_items": int,
    "high_importance_count": int,
    "medium_importance_count": int,
    "low_importance_count": int,
    "items": List[AnalyzedReportItem],
    "scan_timestamp": str,
    "rss_feeds_used": List[str],
    "search_source": "rss" | "web"
}
```

## 🛠️ Common Tasks

### Run Tests
```bash
# Verify setup
python3 backend/tests/test_setup_verification.py

# Test RSS collection
python3 backend/tests/test_rss_collection.py

# Test AI analysis
python3 backend/tests/test_ai_analysis.py

# Test API endpoints
python3 backend/tests/test_api_endpoints.py
```

### Start Server
```bash
python3 -m uvicorn backend.main:app --reload
```

### View API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔍 Where to Find Things

| What You Need | Where to Look |
|---------------|---------------|
| Data structures | `backend/models.py` |
| Configuration | `backend/config.py` |
| RSS collection | `backend/scanner.py` → `stage1_collect_rss()` |
| Web search | `backend/scanner.py` → `stage1_collect_web()` |
| AI analysis | `backend/scanner.py` → `stage2_analyze_with_ai()` |
| API endpoints | `backend/main.py` |
| Frontend logic | `frontend/app.js` |
| Business rules | `background.md` |
| RSS feed list | `rss_feeds.json` |
| Keyword stats | `search_keywords.json` |

## 🎓 Learning Order

1. **Models** (`backend/models.py`) - Understand data structures
2. **Config** (`backend/config.py`) - Understand configuration
3. **Scanner** (`backend/scanner.py`) - Understand core logic
4. **Main** (`backend/main.py`) - Understand API layer
5. **Frontend** (`frontend/app.js`) - Understand user interface
6. **Background** (`background.md`) - Understand business logic

## 💡 Pro Tips

- **Start with models.py** - Everything else uses these data structures
- **Read background.md** - It explains WHY the system works the way it does
- **Use the tests** - They show how functions are supposed to be used
- **Check API docs** - Visit `/docs` when server is running
- **Read error messages** - They often tell you exactly what's wrong

