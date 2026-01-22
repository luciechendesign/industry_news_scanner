"""Data models for the Industry News Scanner."""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class Importance(str, Enum):
    """Importance levels for news items."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NewsItem(BaseModel):
    """Raw news item from RSS feed."""
    title: str
    url: str
    source: str
    published_date: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    search_keyword: Optional[str] = None  # Record which keyword found this item (for web search)


class AnalyzedReportItem(BaseModel):
    """Analyzed report item with strategic context."""
    title: str
    source: str
    url: str
    importance: Importance
    confidence: float = Field(ge=0.0, le=1.0)
    why_it_matters: List[str] = Field(min_length=2, max_length=5)
    evidence: str
    second_order_impacts: Optional[str] = None
    recommended_actions: List[str] = Field(min_length=1, max_length=3)
    dedupe_note: Optional[str] = None
    category: Optional[str] = None  # 平台规则/卖家玩法/红人生态/合规/工具链

    @field_validator('importance')
    @classmethod
    def validate_importance(cls, v):
        if isinstance(v, str):
            v = v.lower()
        return Importance(v)


class ScanReport(BaseModel):
    """Complete scan report."""
    total_items: int
    high_importance_count: int
    medium_importance_count: int
    low_importance_count: int
    items: List[AnalyzedReportItem]
    scan_timestamp: str
    rss_feeds_used: List[str]
    search_source: str = "rss"  # "rss" or "web"
    search_keywords_used: Optional[List[str]] = None  # Only for web search

