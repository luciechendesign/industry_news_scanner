"""FastAPI application for Industry News Scanner."""
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .scanner import stage1_collect_rss, stage1_collect_web, stage2_analyze_with_ai, generate_search_keywords
from .models import ScanReport, AnalyzedReportItem
from .config import load_rss_feeds, validate_config, PROJECT_ROOT


class ScanRequest(BaseModel):
    """Request model for scan endpoint."""
    search_source: str = "rss"  # "rss" or "web"

app = FastAPI(
    title="Industry News Scanner API",
    description="Two-Stage Scan workflow for strategic news analysis",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
frontend_path = PROJECT_ROOT / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    
    # Serve index.html at root
    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        from fastapi.responses import FileResponse
        index_path = frontend_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"message": "Frontend not found. API is available at /docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        config_status = validate_config()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "config": config_status
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.post("/api/scan", response_model=ScanReport)
async def scan_news(request: ScanRequest = ScanRequest()):
    """
    Trigger Two-Stage Scan workflow.
    
    Stage 1: Collect news from RSS feeds or web search (based on search_source)
    Stage 2: Analyze news with AI based on background.md
    
    Args:
        request: ScanRequest with search_source ("rss" or "web")
    
    Returns:
        ScanReport with analyzed news items sorted by importance
    """
    try:
        search_source = request.search_source.lower()
        
        # Stage 1: Collect news based on search source
        if search_source == "web":
            print("Starting Stage 1: Web Search Collection...")
            news_items = stage1_collect_web()
            search_keywords = generate_search_keywords()
            feed_names = []
        else:
            # Default to RSS
            print("Starting Stage 1: RSS Collection...")
            news_items = stage1_collect_rss()
            feeds = load_rss_feeds()
            feed_names = [feed.get("name", "Unknown") for feed in feeds]
            search_keywords = None
        
        if not news_items:
            # Return empty report if no news collected
            return ScanReport(
                total_items=0,
                high_importance_count=0,
                medium_importance_count=0,
                low_importance_count=0,
                items=[],
                scan_timestamp=datetime.now().isoformat(),
                rss_feeds_used=feed_names,
                search_source=search_source,
                search_keywords_used=search_keywords
            )
        
        # Stage 2: Analyze with AI
        print("Starting Stage 2: AI Analysis...")
        analyzed_items = stage2_analyze_with_ai(news_items)
        
        # Count by importance
        high_count = sum(1 for item in analyzed_items if item.importance.value == "high")
        medium_count = sum(1 for item in analyzed_items if item.importance.value == "medium")
        low_count = sum(1 for item in analyzed_items if item.importance.value == "low")
        
        # Create scan report
        report = ScanReport(
            total_items=len(analyzed_items),
            high_importance_count=high_count,
            medium_importance_count=medium_count,
            low_importance_count=low_count,
            items=analyzed_items,
            scan_timestamp=datetime.now().isoformat(),
            rss_feeds_used=feed_names,
            search_source=search_source,
            search_keywords_used=search_keywords
        )
        
        return report
        
    except Exception as e:
        print(f"Error in scan workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Scan failed: {str(e)}"
        )


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Industry News Scanner API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "scan": "/api/scan (POST)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

