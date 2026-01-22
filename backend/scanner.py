"""Two-Stage Scan workflow implementation."""
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Tuple
import time
import re
import feedparser
from .models import NewsItem, AnalyzedReportItem, Importance
from .config import load_rss_feeds, RSS_TIME_WINDOW_HOURS, load_background_md, WEB_SEARCH_TIME_WINDOW_DAYS
from .ai_client import AIClient
from .web_search import WebSearchClient


def stage1_collect_rss() -> List[NewsItem]:
    """
    Stage 1: Collect news from RSS feeds.
    
    Returns:
        List of NewsItem objects, deduplicated by title and URL.
    """
    feeds = load_rss_feeds()
    all_news_items: List[NewsItem] = []
    seen_items: Set[str] = set()  # For deduplication: (title, url) tuples as strings
    
    # Calculate time threshold
    time_threshold = datetime.now() - timedelta(hours=RSS_TIME_WINDOW_HOURS)
    
    for feed_config in feeds:
        feed_url = feed_config.get("url")
        feed_name = feed_config.get("name", "Unknown")
        
        if not feed_url:
            print(f"Warning: Feed '{feed_name}' has no URL, skipping")
            continue
        
        try:
            # Parse RSS feed
            parsed_feed = feedparser.parse(feed_url)
            
            if parsed_feed.bozo:
                print(f"Warning: Feed '{feed_name}' parsing error: {parsed_feed.bozo_exception}")
                continue
            
            # Process each entry
            for entry in parsed_feed.entries:
                # Extract basic information
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                
                if not title or not link:
                    continue
                
                # Check for duplicates using title + URL combination
                dedupe_key = f"{title.lower()}|{link}"
                if dedupe_key in seen_items:
                    continue
                seen_items.add(dedupe_key)
                
                # Parse published date
                published_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published_date = datetime(*entry.published_parsed[:6]).isoformat()
                        # Check if item is within time window
                        item_date = datetime(*entry.published_parsed[:6])
                        if item_date < time_threshold:
                            continue  # Skip items older than time window
                    except (ValueError, TypeError):
                        pass
                
                # Extract description/content
                description = entry.get("description", "")
                content = None
                if hasattr(entry, "content"):
                    content = entry.content[0].value if entry.content else None
                
                # Create NewsItem
                news_item = NewsItem(
                    title=title,
                    url=link,
                    source=feed_name,
                    published_date=published_date,
                    description=description,
                    content=content or description
                )
                
                all_news_items.append(news_item)
        
        except Exception as e:
            print(f"Error processing feed '{feed_name}': {str(e)}")
            continue
    
    print(f"Stage 1 completed: Collected {len(all_news_items)} unique news items from {len(feeds)} feeds")
    return all_news_items


def generate_search_keywords() -> List[str]:
    """
    Generate search keywords using AI based on background.md.
    Prioritizes high-effectiveness keywords from previous searches.
    
    Returns:
        List of search keyword strings
    """
    from .keyword_manager import get_top_keywords
    
    # Get top keywords by effectiveness
    top_keywords = get_top_keywords(count=5, min_effectiveness=0.3)
    
    # If we have good keywords, use them + generate new ones
    if top_keywords:
        print(f"Using top {len(top_keywords)} effective keywords: {top_keywords}")
        # Use top keywords + generate new ones
        try:
            background_context = load_background_md()
            ai_client = AIClient()
            new_keywords = ai_client.generate_search_keywords(background_context)
            # Combine: top keywords + new keywords (avoid duplicates)
            combined = list(dict.fromkeys(top_keywords + new_keywords))[:10]
            print(f"Combined keywords ({len(combined)}): {combined}")
            return combined
        except Exception as e:
            print(f"Error generating new keywords: {e}")
            # Fallback keywords to use when AI generation fails
            fallback_keywords = [
                "Amazon influencer program updates",
                "influencer marketing trends 2025",
                "e-commerce platform rules 2025",
                "FTC influencer disclosure rules",
                "Agentio funding news",
                "Aha influencer tool updates",
                "Amazon seller compliance 2025",
                "influencer marketing tools 2025"
            ]
            # If we have top keywords, use them + fallback keywords
            if top_keywords:
                # Combine top keywords with fallback (avoid duplicates)
                combined = list(dict.fromkeys(top_keywords + fallback_keywords))[:10]
                print(f"Using top keywords + fallback ({len(combined)}): {combined}")
                return combined
            else:
                # No top keywords, use fallback only
                return fallback_keywords[:10]
    
    # Fallback to AI generation
    try:
        background_context = load_background_md()
        ai_client = AIClient()
        keywords = ai_client.generate_search_keywords(background_context)
        print(f"Generated {len(keywords)} search keywords: {keywords}")
        return keywords
    except Exception as e:
        print(f"Error generating search keywords: {e}")
        # Fallback keywords (expanded list)
        return [
            "Amazon seller policy changes 2025",
            "Amazon influencer program updates",
            "influencer marketing trends 2025",
            "e-commerce platform rules 2025",
            "FTC influencer disclosure rules",
            "Agentio funding news",
            "Aha influencer tool updates",
            "Amazon seller compliance 2025"
        ]


def _is_video_source(url: str) -> bool:
    """Check if URL is from a video platform."""
    video_domains = [
        'youtube.com', 'youtu.be',
        'vimeo.com',
        'tiktok.com',
        'instagram.com',  # Instagram has video content
        'twitch.tv',
        'dailymotion.com'
    ]
    url_lower = url.lower()
    return any(domain in url_lower for domain in video_domains)


def _extract_and_validate_date(title: str, url: str, description: str, time_threshold: datetime) -> Tuple[Optional[str], bool]:
    """
    Extract date from title, URL, or description and validate against time threshold.
    
    Returns:
        Tuple of (published_date_iso_string or None, should_skip: bool)
    """
    published_date = None
    date_found = False
    
    # Date patterns to match
    date_patterns = [
        # ISO format: 2025-01-15, 2025/01/15
        (r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', ['%Y-%m-%d', '%Y/%m/%d']),
        # US format: 01-15-2025, 01/15/2025
        (r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})', ['%m-%d-%Y', '%m/%d/%Y']),
        # Full month name: January 15, 2025
        (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', ['%B %d, %Y', '%B %d %Y']),
        # Day month year: 15 January 2025
        (r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', ['%d %B %Y']),
        # Short month: Jan 15, 2025
        (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s+(\d{4})', ['%b %d, %Y', '%b %d %Y']),
    ]
    
    # Try to extract date from description
    for pattern, formats in date_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            try:
                date_str = match.group(0)
                for fmt in formats:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        if parsed_date >= time_threshold:
                            published_date = parsed_date.isoformat()
                            date_found = True
                            return published_date, False
                        else:
                            # Date is too old
                            date_found = True
                            return None, True
                    except ValueError:
                        continue
                if date_found:
                    break
            except (ValueError, IndexError):
                continue
    
    # Try to extract date from URL (common pattern: /2025/01/15/)
    if not date_found:
        url_date_match = re.search(r'/(\d{4})/(\d{1,2})/(\d{1,2})/', url)
        if url_date_match:
            try:
                year, month, day = url_date_match.groups()
                parsed_date = datetime(int(year), int(month), int(day))
                if parsed_date >= time_threshold:
                    published_date = parsed_date.isoformat()
                    date_found = True
                    return published_date, False
                else:
                    # Date in URL is too old
                    return None, True
            except (ValueError, TypeError):
                pass
    
    # If we still can't determine date, check for year in title/description
    # If year is clearly old (e.g., 2023, 2024 when it's 2025), skip
    if not date_found:
        current_year = datetime.now().year
        year_pattern = r'\b(20\d{2})\b'
        years_found = re.findall(year_pattern, title + " " + description)
        if years_found:
            # Check if all years found are older than current year - 1
            years = [int(y) for y in years_found if y.isdigit()]
            if years and max(years) < current_year - 1:
                # All years are at least 2 years old, likely old content
                return None, True
    
    return None, False


def stage1_collect_web() -> List[NewsItem]:
    """
    Stage 1: Collect news from web search.
    
    Uses AI to generate search keywords based on background.md,
    then performs web searches and converts results to NewsItem format.
    Prioritizes video sources (YouTube, etc.) over articles.
    
    Returns:
        List of NewsItem objects, deduplicated by title and URL, with videos prioritized.
    """
    import json
    from pathlib import Path
    log_path = Path(__file__).parent.parent / ".cursor" / "debug.log"
    
    try:
        # Generate search keywords using AI
        print("Generating search keywords from strategic context...")
        keywords = generate_search_keywords()
        
        if not keywords:
            print("No keywords generated, using fallback keywords")
            keywords = [
                "Amazon seller policy changes 2025",
                "Amazon influencer program updates",
                "influencer marketing trends 2025",
                "e-commerce platform rules 2025",
                "FTC influencer disclosure rules",
                "Agentio funding news",
                "Aha influencer tool updates",
                "Amazon seller compliance 2025"
            ]
        
        # Initialize web search client
        try:
            web_search = WebSearchClient()
        except ValueError as e:
            print(f"Web search client initialization failed: {e}")
            raise
        
        all_news_items: List[NewsItem] = []
        seen_items: Set[str] = set()  # For deduplication
        
        # Calculate time threshold for filtering (last N days)
        time_threshold = datetime.now() - timedelta(days=WEB_SEARCH_TIME_WINDOW_DAYS)
        print(f"Filtering results to last {WEB_SEARCH_TIME_WINDOW_DAYS} days (since {time_threshold.strftime('%Y-%m-%d')})")
        print("Prioritizing video sources (YouTube, etc.) over articles...")
        
        # Search for each keyword - prioritize video searches
        for keyword in keywords:
            print(f"Searching web for: {keyword}")
            
            # First, try searching specifically for videos
            video_query = f"{keyword} video"
            try:
                print(f"  Searching videos: {video_query}")
                search_results = web_search.search(video_query)
                
                for result in search_results:
                    title = result.get("title", "").strip()
                    url = result.get("url", "").strip()
                    description = result.get("description", "").strip()
                    source = result.get("source", "Web Search")
                    
                    if not title or not url:
                        continue
                    
                    # Only process video sources in this pass
                    if not _is_video_source(url):
                        continue
                    
                    # Check for duplicates
                    dedupe_key = f"{title.lower()}|{url}"
                    if dedupe_key in seen_items:
                        continue
                    seen_items.add(dedupe_key)
                    
                    # Extract and validate date
                    published_date, should_skip = _extract_and_validate_date(title, url, description, time_threshold)
                    if should_skip:
                        continue
                    
                    # Create NewsItem with keyword tracking
                    news_item = NewsItem(
                        title=title,
                        url=url,
                        source=source,
                        published_date=published_date,  # May be None if date couldn't be determined
                        description=description,
                        content=description,  # Use description as content
                        search_keyword=keyword  # Record which keyword found this item
                    )
                    
                    all_news_items.append(news_item)
                    
            except Exception as e:
                print(f"  Error searching videos for keyword '{keyword}': {e}")
                # Continue to regular search even if video search fails
            
            # Then, search with original keyword (will include both videos and articles)
            try:
                search_results = web_search.search(keyword)
                
                for result in search_results:
                    title = result.get("title", "").strip()
                    url = result.get("url", "").strip()
                    description = result.get("description", "").strip()
                    source = result.get("source", "Web Search")
                    
                    if not title or not url:
                        continue
                    
                    # Check for duplicates
                    dedupe_key = f"{title.lower()}|{url}"
                    if dedupe_key in seen_items:
                        continue
                    seen_items.add(dedupe_key)
                    
                    # Extract and validate date
                    published_date, should_skip = _extract_and_validate_date(title, url, description, time_threshold)
                    if should_skip:
                        continue
                    
                    # Create NewsItem with keyword tracking
                    news_item = NewsItem(
                        title=title,
                        url=url,
                        source=source,
                        published_date=published_date,  # May be None if date couldn't be determined
                        description=description,
                        content=description,  # Use description as content
                        search_keyword=keyword  # Record which keyword found this item
                    )
                    
                    all_news_items.append(news_item)
                    
            except Exception as e:
                print(f"Error searching for keyword '{keyword}': {e}")
                continue
        
        # Sort results: videos first, then articles
        def get_sort_key(item: NewsItem) -> tuple:
            """Return sort key: (is_video, ...) to prioritize videos."""
            is_video = _is_video_source(item.url)
            return (not is_video, item.title)  # False (videos) sorts before True (articles)
        
        all_news_items.sort(key=get_sort_key)
        
        video_count = sum(1 for item in all_news_items if _is_video_source(item.url))
        print(f"Stage 1 (Web Search) completed: Collected {len(all_news_items)} unique news items ({video_count} videos, {len(all_news_items) - video_count} articles) from {len(keywords)} keywords")
        return all_news_items
        
    except Exception as e:
        print(f"Error in stage1_collect_web: {e}")
        import traceback
        traceback.print_exc()
        raise


def stage2_analyze_with_ai(news_items: List[NewsItem]) -> List[AnalyzedReportItem]:
    """
    Stage 2: Analyze news items with AI based on background.md.
    
    Args:
        news_items: List of NewsItem objects from Stage 1
        
    Returns:
        List of AnalyzedReportItem objects, sorted by importance (High > Medium > Low)
    """
    if not news_items:
        print("No news items to analyze")
        return []
    
    # Load background context
    print("Loading strategic context from background.md...")
    background_context = load_background_md()
    
    # Initialize AI client
    print("Initializing AI client...")
    try:
        ai_client = AIClient()
    except ValueError as e:
        print(f"Error initializing AI client: {e}")
        raise
    
    analyzed_items: List[AnalyzedReportItem] = []
    
    # Track keyword statistics for web search
    from .keyword_manager import update_keyword_stats
    keyword_results: Dict[str, Dict[str, int]] = {}  # {keyword: {high: 0, medium: 0, low: 0}}
    
    # Analyze each news item
    total_items = len(news_items)
    print(f"Analyzing {total_items} news items with AI...")
    
    for idx, news_item in enumerate(news_items, 1):
        print(f"  [{idx}/{total_items}] Analyzing: {news_item.title[:60]}...")
        
        # Add delay between requests to avoid rate limiting and SSL connection issues
        if idx > 1:
            time.sleep(1)  # 1 second delay between requests
        
        try:
            # Convert NewsItem to dict for AI client
            news_dict = {
                "title": news_item.title,
                "url": news_item.url,
                "source": news_item.source,
                "description": news_item.description or "",
                "content": news_item.content or news_item.description or ""
            }
            
            # Call AI API
            ai_result = ai_client.analyze_news_item(news_dict, background_context)
            
            # Validate and create AnalyzedReportItem
            try:
                analyzed_item = AnalyzedReportItem(
                    title=news_item.title,
                    source=news_item.source,
                    url=news_item.url,
                    importance=ai_result.get("importance", "low").lower(),
                    confidence=float(ai_result.get("confidence", 0.5)),
                    why_it_matters=ai_result.get("why_it_matters", []),
                    evidence=ai_result.get("evidence", ""),
                    second_order_impacts=ai_result.get("second_order_impacts"),
                    recommended_actions=ai_result.get("recommended_actions", []),
                    dedupe_note=ai_result.get("dedupe_note"),
                    category=ai_result.get("category")
                )
                analyzed_items.append(analyzed_item)
                print(f"    ✓ Analyzed: {analyzed_item.importance.upper()} importance")
                
                # Track results by keyword (for web search)
                if news_item.search_keyword:
                    keyword = news_item.search_keyword
                    if keyword not in keyword_results:
                        keyword_results[keyword] = {"high": 0, "medium": 0, "low": 0}
                    importance = analyzed_item.importance.value
                    keyword_results[keyword][importance] += 1
            except Exception as e:
                print(f"    ✗ Validation error: {e}")
                print(f"    AI result: {ai_result}")
                continue
                
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Handle SSL/connection errors with retry logic
            if "SSL" in error_msg or "EOF" in error_msg or "connection" in error_msg.lower():
                print(f"    ⚠ Connection error detected, waiting 3 seconds before continuing...")
                time.sleep(3)
                # Try once more with longer delay
                try:
                    time.sleep(2)
                    ai_result = ai_client.analyze_news_item(news_dict, background_context)
                    # If retry succeeds, continue with validation
                    try:
                        analyzed_item = AnalyzedReportItem(
                            title=news_item.title,
                            source=news_item.source,
                            url=news_item.url,
                            importance=ai_result.get("importance", "low").lower(),
                            confidence=float(ai_result.get("confidence", 0.5)),
                            why_it_matters=ai_result.get("why_it_matters", []),
                            evidence=ai_result.get("evidence", ""),
                            second_order_impacts=ai_result.get("second_order_impacts"),
                            recommended_actions=ai_result.get("recommended_actions", []),
                            dedupe_note=ai_result.get("dedupe_note"),
                            category=ai_result.get("category")
                        )
                        analyzed_items.append(analyzed_item)
                        print(f"    ✓ Analyzed (after retry): {analyzed_item.importance.upper()} importance")
                        
                        # Track results by keyword (for web search)
                        if news_item.search_keyword:
                            keyword = news_item.search_keyword
                            if keyword not in keyword_results:
                                keyword_results[keyword] = {"high": 0, "medium": 0, "low": 0}
                            importance = analyzed_item.importance.value
                            keyword_results[keyword][importance] += 1
                        continue
                    except Exception as validation_error:
                        print(f"    ✗ Validation error after retry: {validation_error}")
                        continue
                except Exception as retry_error:
                    print(f"    ✗ Retry failed: {retry_error}")
                    continue
            
            print(f"    ✗ Error analyzing item ({error_type}): {e}")
            continue
    
    # Update keyword statistics (for web search)
    if keyword_results:
        print(f"\nUpdating keyword effectiveness statistics...")
        for keyword, counts in keyword_results.items():
            update_keyword_stats(
                keyword,
                counts["high"],
                counts["medium"],
                counts["low"]
            )
            print(f"  {keyword}: {counts['high']} high, {counts['medium']} medium, {counts['low']} low")
    
    # Sort by importance: High > Medium > Low
    importance_order = {Importance.HIGH: 0, Importance.MEDIUM: 1, Importance.LOW: 2}
    analyzed_items.sort(key=lambda x: importance_order.get(x.importance, 3))
    
    # Count by importance
    high_count = sum(1 for item in analyzed_items if item.importance == Importance.HIGH)
    medium_count = sum(1 for item in analyzed_items if item.importance == Importance.MEDIUM)
    low_count = sum(1 for item in analyzed_items if item.importance == Importance.LOW)
    
    print(f"\nStage 2 completed: Analyzed {len(analyzed_items)} items")
    print(f"  - High importance: {high_count}")
    print(f"  - Medium importance: {medium_count}")
    print(f"  - Low importance: {low_count}")
    
    return analyzed_items

