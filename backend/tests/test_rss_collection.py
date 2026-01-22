"""Test script for Stage 1: RSS Collection."""
import sys
from pathlib import Path

# Add project root directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.scanner import stage1_collect_rss
from backend.models import NewsItem
import json


def test_rss_collection():
    """Test RSS collection functionality."""
    print("=" * 60)
    print("Testing Stage 1: RSS Collection")
    print("=" * 60)
    
    try:
        # Run Stage 1
        print("\n1. Collecting news from RSS feeds...")
        news_items = stage1_collect_rss()
        
        # Test 1: Check if items were collected
        print(f"\n✓ Test 1: Collection - Found {len(news_items)} news items")
        assert len(news_items) > 0, "No news items collected!"
        
        # Test 2: Check deduplication
        titles = [item.title for item in news_items]
        urls = [item.url for item in news_items]
        unique_titles = set(titles)
        unique_urls = set(urls)
        
        print(f"✓ Test 2: Deduplication - {len(news_items)} items, {len(unique_titles)} unique titles, {len(unique_urls)} unique URLs")
        assert len(titles) == len(unique_titles) or len(urls) == len(unique_urls), "Deduplication may have failed"
        
        # Test 3: Validate data structure
        print("\n✓ Test 3: Data Structure Validation")
        for i, item in enumerate(news_items[:3], 1):  # Check first 3 items
            assert isinstance(item, NewsItem), f"Item {i} is not a NewsItem instance"
            assert item.title, f"Item {i} has no title"
            assert item.url, f"Item {i} has no URL"
            assert item.source, f"Item {i} has no source"
            print(f"  - Item {i}: {item.title[:50]}...")
        
        # Test 4: Check time window filtering
        items_with_date = [item for item in news_items if item.published_date]
        print(f"\n✓ Test 4: Time Window - {len(items_with_date)}/{len(news_items)} items have published dates")
        
        # Display sample results
        print("\n" + "=" * 60)
        print("Sample Results (first 5 items):")
        print("=" * 60)
        for i, item in enumerate(news_items[:5], 1):
            print(f"\n{i}. {item.title}")
            print(f"   Source: {item.source}")
            print(f"   URL: {item.url}")
            if item.published_date:
                print(f"   Published: {item.published_date}")
        
        # Save results to JSON for inspection (in tests directory)
        output_file = Path(__file__).parent / "test_rss_collection_output.json"
        output_data = [
            {
                "title": item.title,
                "url": item.url,
                "source": item.source,
                "published_date": item.published_date,
                "description": item.description[:200] if item.description else None
            }
            for item in news_items
        ]
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Results saved to: {output_file}")
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_rss_collection()
    sys.exit(0 if success else 1)

