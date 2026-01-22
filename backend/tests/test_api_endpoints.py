"""Test script for Backend API endpoints."""
import sys
import requests
import json
from pathlib import Path

# Add project root directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

BASE_URL = "http://localhost:8000"


def test_health_endpoint():
    """Test health check endpoint."""
    print("=" * 60)
    print("Testing GET /health endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed")
            print(f"  Status: {data.get('status')}")
            print(f"  Config: {data.get('config')}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Is it running?")
        print("  Start server with: uvicorn backend.main:app --reload")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_root_endpoint():
    """Test root endpoint."""
    print("\n" + "=" * 60)
    print("Testing GET / endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Root endpoint works")
            print(f"  API Name: {data.get('name')}")
            print(f"  Version: {data.get('version')}")
            return True
        else:
            print(f"✗ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_scan_endpoint():
    """Test scan endpoint."""
    print("\n" + "=" * 60)
    print("Testing POST /api/scan endpoint")
    print("=" * 60)
    print("This may take a few minutes...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/scan", timeout=300)  # 5 minute timeout
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Scan completed successfully")
            print(f"  Total items: {data.get('total_items')}")
            print(f"  High importance: {data.get('high_importance_count')}")
            print(f"  Medium importance: {data.get('medium_importance_count')}")
            print(f"  Low importance: {data.get('low_importance_count')}")
            print(f"  RSS feeds used: {len(data.get('rss_feeds_used', []))}")
            
            # Validate structure
            assert "total_items" in data
            assert "high_importance_count" in data
            assert "medium_importance_count" in data
            assert "low_importance_count" in data
            assert "items" in data
            assert "scan_timestamp" in data
            assert "rss_feeds_used" in data
            
            print(f"\n✓ Data structure validation passed")
            
            # Save results (in tests directory)
            output_file = Path(__file__).parent / "test_api_endpoints_output.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Results saved to: {output_file}")
            
            # Show sample items
            items = data.get("items", [])
            if items:
                print(f"\nSample items (first 3):")
                for i, item in enumerate(items[:3], 1):
                    print(f"  {i}. {item.get('title', 'N/A')[:60]}...")
                    print(f"     Importance: {item.get('importance', 'N/A').upper()}")
                    print(f"     Confidence: {item.get('confidence', 0)}")
            
            return True
        else:
            print(f"✗ Scan failed: {response.status_code}")
            print(f"  Response: {response.text[:500]}")
            return False
    except requests.exceptions.Timeout:
        print("✗ Request timed out (scan took too long)")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all API tests."""
    print("\n" + "=" * 60)
    print("Backend API Integration Tests")
    print("=" * 60)
    print("\nMake sure the server is running:")
    print("  uvicorn backend.main:app --reload")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    results = []
    
    # Test health endpoint
    results.append(("Health Check", test_health_endpoint()))
    
    # Test root endpoint
    results.append(("Root Endpoint", test_root_endpoint()))
    
    # Test scan endpoint (optional, takes time)
    print("\n" + "=" * 60)
    print("Scan endpoint test (this will take several minutes)")
    print("Skip? (y/n): ", end="")
    try:
        skip_scan = input().strip().lower() == 'y'
    except KeyboardInterrupt:
        skip_scan = True
    
    if not skip_scan:
        results.append(("Scan Endpoint", test_scan_endpoint()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

