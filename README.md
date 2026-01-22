# Industry News Scanner MVP

A web application that performs a Two-Stage Scan workflow to collect and analyze industry news based on strategic context defined in `background.md`.

## 📚 Learning Resources

- **[LEARNING_GUIDE.md](LEARNING_GUIDE.md)** - Comprehensive beginner-friendly guide with architecture overview, file-by-file explanations, and learning exercises
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference for file structure, data flow, and common tasks

## Project Structure

```
Industry_news/
├── backend/           # FastAPI backend
│   ├── main.py       # API endpoints
│   ├── scanner.py    # Two-Stage Scan workflow
│   ├── config.py     # Configuration management
│   ├── models.py     # Data models
│   └── tests/        # Test suite
│       ├── test_rss_collection.py
│       ├── test_ai_analysis.py
│       ├── test_api_endpoints.py
│       └── test_setup_verification.py
├── frontend/         # Vanilla JS frontend
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── background.md     # Strategic context
├── rss_feeds.json    # RSS feed configuration
├── .env.example      # Environment variables template
└── README.md         # This file
```

## Setup

### 1. Install Dependencies

```bash
cd backend
pip3 install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API key:

```bash
cp .env.example .env
# Edit .env and add your AI_API_KEY
```

### 3. Configure RSS Feeds

Edit `rss_feeds.json` to add or modify RSS feed sources.

## Running the Application

### Start the Backend Server

**推荐方式**（使用 python3 -m uvicorn）：

```bash
cd /Users/luqianchen/Documents/Industry_news
python3 -m uvicorn backend.main:app --reload
```

或者使用启动脚本：

```bash
./start_server.sh
```

或者从backend目录：

```bash
cd backend
python3 -m uvicorn main:app --reload
```

**注意**: 如果直接使用 `uvicorn` 命令提示未找到，请使用 `python3 -m uvicorn` 的方式。

The API will be available at `http://localhost:8000`

### API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /api/scan` - Trigger Two-Stage Scan workflow

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

### Setup Verification

Verify your project setup:

```bash
python3 backend/tests/test_setup_verification.py
```

This checks:
- All imports are working
- Configuration files exist
- RSS feeds are configured
- Environment variables are set

### RSS Collection Test

Test Stage 1 (RSS collection):

```bash
python3 backend/tests/test_rss_collection.py
```

This will:
- Collect news from configured RSS feeds
- Test deduplication
- Validate data structures
- Save results to `backend/tests/test_rss_collection_output.json`

### AI Analysis Test

Test Stage 2 (AI analysis):

```bash
python3 backend/tests/test_ai_analysis.py
```

This will:
- Run Stage 1 to collect news (uses first 3 items to save API calls)
- Analyze news items with AI
- Validate data structures and importance classification
- Save results to `backend/tests/test_ai_analysis_output.json`

**Note**: Requires valid API credentials in `.env` file.

### API Endpoints Test

Test the backend API:

1. Start the server:
   ```bash
   python3 -m uvicorn backend.main:app --reload
   ```

2. Test with curl:
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # Trigger scan
   curl -X POST http://localhost:8000/api/scan
   ```

3. Or use the test script:
   ```bash
   python3 backend/tests/test_api_endpoints.py
   ```

### Step 4: Frontend UI

1. Start the backend server:
   ```bash
   python3 -m uvicorn backend.main:app --reload
   ```

2. Open the frontend:
   - **Option 1**: Visit http://localhost:8000 (if static files are mounted)
   - **Option 2**: Open `frontend/index.html` directly in browser
   - **Option 3**: Use Python HTTP server:
     ```bash
     cd frontend
     python3 -m http.server 8080
     ```
     Then visit http://localhost:8080

3. Click "Start Scan" button and wait for results

## Quick Start

1. **Install dependencies**:
   ```bash
   cd backend
   pip3 install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   # Edit .env file with your API keys
   cp .env.example .env
   ```

3. **Start backend**:
   ```bash
   python3 -m uvicorn backend.main:app --reload
   ```

4. **Open frontend**:
   - Open `frontend/index.html` in your browser
   - Or visit http://localhost:8000 if static files are configured

5. **Click "Start Scan"** and wait for results!

## Development Status

- [x] Step 1: RSS Collection ✓
- [x] Step 2: AI Analysis ✓
- [x] Step 3: Backend API ✓
- [x] Step 4: Frontend UI ✓

## Environment Variables

- `AI_API_KEY`: Your AI service API key (OpenAI or Anthropic)
- `AI_PROVIDER`: `openai` or `anthropic` (default: `openai`)
- `AI_MODEL`: Model name (default: `gpt-4`)
- `RSS_TIME_WINDOW_HOURS`: Hours to look back for news (default: `48`)

