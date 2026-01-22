"""Configuration management for the Industry News Scanner."""
import os
from pathlib import Path
from typing import List, Dict
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
BACKGROUND_MD_PATH = PROJECT_ROOT / "background.md"
RSS_FEEDS_JSON_PATH = PROJECT_ROOT / "rss_feeds.json"

# AI API Configuration
# Support both standard (OpenAI/Anthropic) and custom API configurations
AI_BUILDER_TOKEN = os.getenv("AI_BUILDER_TOKEN", "")
AI_API_KEY = os.getenv("AI_API_KEY") or AI_BUILDER_TOKEN

# Try to read API_URL (handle both "API_URL" and "API URL" formats)
raw_api_url = os.getenv("AI_API_URL") or os.getenv("API_URL", "") or os.getenv("API URL", "")
AI_API_URL = raw_api_url.strip() if raw_api_url else ""

AI_PROVIDER = os.getenv("AI_PROVIDER", "").lower()  # 'openai', 'anthropic', or 'custom'
AI_MODEL = os.getenv("AI_MODEL") or os.getenv("AI_BUILDER_MODEL", "gpt-4")  # Default model name

# Auto-detect provider if not explicitly set
if not AI_PROVIDER:
    # Check if using AI Builders (has AI_BUILDER_TOKEN or model contains supermind)
    if AI_BUILDER_TOKEN or "supermind" in AI_MODEL.lower():
        AI_PROVIDER = "custom"
        if AI_API_URL:
            # Ensure URL ends with /chat/completions if it's a base URL
            if not AI_API_URL.endswith("/chat/completions") and "/chat" not in AI_API_URL:
                AI_API_URL = AI_API_URL.rstrip("/") + "/chat/completions"
        else:
            # Default AI Builders endpoint
            AI_API_URL = "https://space.ai-builders.com/backend/v1/chat/completions"
    elif AI_API_URL:
        AI_PROVIDER = "custom"
    elif "anthropic" in AI_MODEL.lower() or "claude" in AI_MODEL.lower():
        AI_PROVIDER = "anthropic"
    else:
        AI_PROVIDER = "openai"

# RSS Configuration
RSS_TIME_WINDOW_HOURS = int(os.getenv("RSS_TIME_WINDOW_HOURS", "48"))  # Default 48 hours

# Web Search Configuration
WEB_SEARCH_TIME_WINDOW_DAYS = int(os.getenv("WEB_SEARCH_TIME_WINDOW_DAYS", "30"))  # Default 30 days
WEB_SEARCH_API_PROVIDER = os.getenv("WEB_SEARCH_API_PROVIDER", "").lower()

# Auto-detect: if using AI Builders and no explicit search provider, use AI Builders search
if not WEB_SEARCH_API_PROVIDER:
    if AI_BUILDER_TOKEN or "supermind" in AI_MODEL.lower():
        WEB_SEARCH_API_PROVIDER = "ai-builders"
    else:
        WEB_SEARCH_API_PROVIDER = "tavily"  # Default fallback

# Fallback to AI_API_KEY if WEB_SEARCH_API_KEY not set (useful for Perplexity or AI Builders)
WEB_SEARCH_API_KEY = os.getenv("WEB_SEARCH_API_KEY") or AI_API_KEY or ""
WEB_SEARCH_API_URL = os.getenv("WEB_SEARCH_API_URL", "")
WEB_SEARCH_MAX_RESULTS = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "10"))  # Max results per query


def load_rss_feeds() -> List[Dict[str, str]]:
    """Load RSS feeds configuration from rss_feeds.json."""
    if not RSS_FEEDS_JSON_PATH.exists():
        raise FileNotFoundError(
            f"RSS feeds configuration file not found: {RSS_FEEDS_JSON_PATH}"
        )
    
    with open(RSS_FEEDS_JSON_PATH, 'r', encoding='utf-8') as f:
        feeds = json.load(f)
    
    if not isinstance(feeds, list):
        raise ValueError("rss_feeds.json must contain a list of feed objects")
    
    return feeds


def load_background_md() -> str:
    """Load background.md file content."""
    if not BACKGROUND_MD_PATH.exists():
        raise FileNotFoundError(
            f"Background file not found: {BACKGROUND_MD_PATH}"
        )
    
    with open(BACKGROUND_MD_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def validate_config() -> Dict[str, bool]:
    """Validate configuration and return status."""
    status = {
        "background_md_exists": BACKGROUND_MD_PATH.exists(),
        "rss_feeds_exists": RSS_FEEDS_JSON_PATH.exists(),
        "ai_api_key_set": bool(AI_API_KEY),
        "ai_api_url_set": bool(AI_API_URL) if AI_PROVIDER == "custom" else True,
    }
    return status

