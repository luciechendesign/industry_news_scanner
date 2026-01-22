"""Test script for Stage 2: AI Analysis."""
import sys
from pathlib import Path
from datetime import datetime

# Add project root directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.scanner import stage1_collect_rss, stage2_analyze_with_ai
from backend.models import AnalyzedReportItem, Importance
import json


def test_ai_analysis():
    """Test AI analysis functionality."""
    print("=" * 60)
    print("Testing Stage 2: AI Analysis")
    print("=" * 60)
    
    try:
        # Step 1: Collect news (or use limited set for testing)
        print("\n1. Collecting news from RSS feeds (Stage 1)...")
        news_items = stage1_collect_rss()
        
        if not news_items:
            print("✗ No news items collected. Cannot test Stage 2.")
            return False
        
        # Limit to first 3 items for testing (to save API calls)
        test_items = news_items[:3]
        print(f"   Using {len(test_items)} items for testing (to save API calls)")
        
        # Step 2: Analyze with AI
        print("\n2. Analyzing news items with AI (Stage 2)...")
        print("   This may take a few minutes...")
        analyzed_items = stage2_analyze_with_ai(test_items)
        
        # Test 1: Check if items were analyzed
        print(f"\n✓ Test 1: Analysis - Analyzed {len(analyzed_items)} items")
        assert len(analyzed_items) > 0, "No items were analyzed!"
        assert len(analyzed_items) <= len(test_items), "More analyzed items than input items!"
        
        # Test 2: Validate data structure
        print("\n✓ Test 2: Data Structure Validation")
        for i, item in enumerate(analyzed_items, 1):
            assert isinstance(item, AnalyzedReportItem), f"Item {i} is not an AnalyzedReportItem instance"
            assert item.title, f"Item {i} has no title"
            assert item.url, f"Item {i} has no URL"
            assert item.source, f"Item {i} has no source"
            assert item.importance in [Importance.HIGH, Importance.MEDIUM, Importance.LOW], \
                f"Item {i} has invalid importance: {item.importance}"
            assert 0.0 <= item.confidence <= 1.0, \
                f"Item {i} has invalid confidence: {item.confidence}"
            assert len(item.why_it_matters) >= 2, \
                f"Item {i} has insufficient why_it_matters: {len(item.why_it_matters)}"
            assert len(item.why_it_matters) <= 5, \
                f"Item {i} has too many why_it_matters: {len(item.why_it_matters)}"
            assert item.evidence, f"Item {i} has no evidence"
            assert len(item.recommended_actions) >= 1, \
                f"Item {i} has no recommended_actions"
            assert len(item.recommended_actions) <= 3, \
                f"Item {i} has too many recommended_actions: {len(item.recommended_actions)}"
            print(f"  - Item {i}: {item.title[:50]}... [{item.importance.value.upper()}]")
        
        # Test 3: Check importance distribution
        high_items = [item for item in analyzed_items if item.importance == Importance.HIGH]
        medium_items = [item for item in analyzed_items if item.importance == Importance.MEDIUM]
        low_items = [item for item in analyzed_items if item.importance == Importance.LOW]
        
        print(f"\n✓ Test 3: Importance Distribution")
        print(f"   - High: {len(high_items)}")
        print(f"   - Medium: {len(medium_items)}")
        print(f"   - Low: {len(low_items)}")
        
        # Test 4: Check sorting (High > Medium > Low)
        print("\n✓ Test 4: Sorting Validation")
        importance_order = [item.importance for item in analyzed_items]
        expected_order = sorted(importance_order, key=lambda x: {
            Importance.HIGH: 0,
            Importance.MEDIUM: 1,
            Importance.LOW: 2
        }.get(x, 3))
        assert importance_order == expected_order, "Items are not sorted by importance!"
        print("   ✓ Items are correctly sorted (High > Medium > Low)")
        
        # Test 5: Check why_it_matters references to Goals
        print("\n✓ Test 5: why_it_matters Validation")
        for i, item in enumerate(analyzed_items, 1):
            # Check if why_it_matters mentions Goal 1/2/3 or related concepts
            why_text = " ".join(item.why_it_matters).lower()
            has_goal_reference = any(
                keyword in why_text for keyword in 
                ["goal 1", "goal 2", "goal 3", "priority 1", "priority 2", "priority 3",
                 "行业洞察", "产品", "竞争", "风险", "合规", "平台", "红人"]
            )
            if not has_goal_reference:
                print(f"   ⚠ Item {i} why_it_matters may not reference Goals 1/2/3")
            else:
                print(f"   ✓ Item {i} why_it_matters references strategic goals")
        
        # Display sample results
        print("\n" + "=" * 60)
        print("Sample Results:")
        print("=" * 60)
        for i, item in enumerate(analyzed_items[:2], 1):  # Show first 2
            print(f"\n{i}. {item.title}")
            print(f"   Importance: {item.importance.value.upper()}")
            print(f"   Confidence: {item.confidence:.2f}")
            print(f"   Category: {item.category or 'N/A'}")
            print(f"   Why it matters:")
            for reason in item.why_it_matters:
                print(f"     - {reason}")
            print(f"   Evidence: {item.evidence[:100]}...")
            print(f"   Recommended actions:")
            for action in item.recommended_actions:
                print(f"     - {action}")
        
        # Save results to JSON for inspection (in tests directory)
        output_file = Path(__file__).parent / "test_ai_analysis_output.json"
        output_data = [
            {
                "title": item.title,
                "source": item.source,
                "url": item.url,
                "importance": item.importance.value,
                "confidence": item.confidence,
                "why_it_matters": item.why_it_matters,
                "evidence": item.evidence,
                "second_order_impacts": item.second_order_impacts,
                "recommended_actions": item.recommended_actions,
                "dedupe_note": item.dedupe_note,
                "category": item.category
            }
            for item in analyzed_items
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
    success = test_ai_analysis()
    sys.exit(0 if success else 1)

