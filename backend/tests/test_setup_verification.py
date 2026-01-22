"""Setup verification script to check project configuration."""
import sys
from pathlib import Path

# Add project root directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("=" * 60)
print("Project Setup Verification")
print("=" * 60)

# Check imports
print("\n1. Checking imports...")
try:
    from backend.config import load_rss_feeds, load_background_md, validate_config
    print("   ✓ config.py imports successful")
except Exception as e:
    print(f"   ✗ config.py import failed: {e}")
    sys.exit(1)

try:
    from backend.models import NewsItem, AnalyzedReportItem, ScanReport, Importance
    print("   ✓ models.py imports successful")
except Exception as e:
    print(f"   ✗ models.py import failed: {e}")
    sys.exit(1)

try:
    from backend.scanner import stage1_collect_rss, stage2_analyze_with_ai
    print("   ✓ scanner.py imports successful")
except ImportError as e:
    if "feedparser" in str(e):
        print("   ⚠ scanner.py import failed: feedparser not installed")
        print("      Run: pip3 install -r requirements.txt")
    else:
        print(f"   ✗ scanner.py import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ scanner.py import failed: {e}")
    sys.exit(1)

# Check configuration
print("\n2. Checking configuration...")
try:
    config_status = validate_config()
    print(f"   ✓ Background MD exists: {config_status['background_md_exists']}")
    print(f"   ✓ RSS feeds config exists: {config_status['rss_feeds_exists']}")
    print(f"   ✓ AI API key set: {config_status['ai_api_key_set']}")
except Exception as e:
    print(f"   ✗ Configuration check failed: {e}")
    sys.exit(1)

# Check RSS feeds loading
print("\n3. Checking RSS feeds configuration...")
try:
    feeds = load_rss_feeds()
    print(f"   ✓ Loaded {len(feeds)} RSS feeds")
    for feed in feeds:
        print(f"     - {feed.get('name', 'Unknown')}: {feed.get('url', 'No URL')}")
except Exception as e:
    print(f"   ✗ RSS feeds loading failed: {e}")
    sys.exit(1)

# Check background.md loading
print("\n4. Checking background.md...")
try:
    background_content = load_background_md()
    print(f"   ✓ Background MD loaded ({len(background_content)} characters)")
except Exception as e:
    print(f"   ✗ Background MD loading failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All checks passed! Project setup is complete.")
print("=" * 60)
print("\nNext steps:")
print("1. Ensure .env file has your AI_API_KEY or AI_BUILDER_TOKEN")
print("2. Install dependencies: pip3 install -r requirements.txt")
print("3. Run tests: python3 backend/tests/test_rss_collection.py")

