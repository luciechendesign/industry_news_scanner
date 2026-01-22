"""Keyword management with effectiveness tracking."""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .config import PROJECT_ROOT

SEARCH_KEYWORDS_JSON_PATH = PROJECT_ROOT / "search_keywords.json"


class KeywordStats:
    """Statistics for a single keyword."""
    def __init__(self, keyword: str):
        self.keyword = keyword
        self.total_searches = 0
        self.high_importance_count = 0
        self.medium_importance_count = 0
        self.low_importance_count = 0
        self.last_used: Optional[str] = None
        self.effectiveness_score = 0.0  # 0.0-1.0
    
    def calculate_effectiveness(self):
        """Calculate effectiveness score based on high importance results."""
        if self.total_searches == 0:
            self.effectiveness_score = 0.0
            return
        
        # 权重：high=3, medium=1, low=0
        weighted_score = (self.high_importance_count * 3 + 
                         self.medium_importance_count * 1) / self.total_searches
        # 归一化到 0-1
        self.effectiveness_score = min(weighted_score / 3.0, 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyword": self.keyword,
            "total_searches": self.total_searches,
            "high_importance_count": self.high_importance_count,
            "medium_importance_count": self.medium_importance_count,
            "low_importance_count": self.low_importance_count,
            "last_used": self.last_used,
            "effectiveness_score": round(self.effectiveness_score, 3)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeywordStats":
        stats = cls(data["keyword"])
        stats.total_searches = data.get("total_searches", 0)
        stats.high_importance_count = data.get("high_importance_count", 0)
        stats.medium_importance_count = data.get("medium_importance_count", 0)
        stats.low_importance_count = data.get("low_importance_count", 0)
        stats.last_used = data.get("last_used")
        stats.effectiveness_score = data.get("effectiveness_score", 0.0)
        return stats


def load_keyword_stats() -> Dict[str, KeywordStats]:
    """Load keyword statistics from JSON file."""
    if not SEARCH_KEYWORDS_JSON_PATH.exists():
        return {}
    
    try:
        with open(SEARCH_KEYWORDS_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stats_dict = {}
        for item in data.get("keywords", []):
            stats = KeywordStats.from_dict(item)
            stats_dict[stats.keyword] = stats
        
        return stats_dict
    except Exception as e:
        print(f"Error loading keyword stats: {e}")
        return {}


def save_keyword_stats(stats_dict: Dict[str, KeywordStats]):
    """Save keyword statistics to JSON file."""
    keywords_data = [stats.to_dict() for stats in stats_dict.values()]
    
    # Sort by effectiveness score (descending)
    keywords_data.sort(key=lambda x: x["effectiveness_score"], reverse=True)
    
    data = {
        "last_updated": datetime.now().isoformat(),
        "keywords": keywords_data
    }
    
    try:
        with open(SEARCH_KEYWORDS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving keyword stats: {e}")


def update_keyword_stats(
    keyword: str,
    high_count: int,
    medium_count: int,
    low_count: int
):
    """Update statistics for a keyword after analysis."""
    stats_dict = load_keyword_stats()
    
    if keyword not in stats_dict:
        stats_dict[keyword] = KeywordStats(keyword)
    
    stats = stats_dict[keyword]
    stats.total_searches += 1
    stats.high_importance_count += high_count
    stats.medium_importance_count += medium_count
    stats.low_importance_count += low_count
    stats.last_used = datetime.now().isoformat()
    stats.calculate_effectiveness()
    
    save_keyword_stats(stats_dict)


def get_top_keywords(count: int = 5, min_effectiveness: float = 0.0) -> List[str]:
    """Get top N keywords by effectiveness score."""
    stats_dict = load_keyword_stats()
    
    # Filter by minimum effectiveness
    filtered = [
        stats for stats in stats_dict.values()
        if stats.effectiveness_score >= min_effectiveness
    ]
    
    # Sort by effectiveness (descending)
    filtered.sort(key=lambda x: x.effectiveness_score, reverse=True)
    
    return [stats.keyword for stats in filtered[:count]]

