#!/usr/bin/env python3
"""Test script to verify scrapers work without API keys."""
import sys
sys.path.insert(0, "backend")
sys.path.insert(0, "scrapers")

from scrapers import get_all_scrapers

def test_scrapers():
    """Test all no-API scrapers."""
    print("\n" + "="*60)
    print("🚀 Testing Social Data Vault - No API Key Mode")
    print("="*60 + "\n")

    scrapers = get_all_scrapers()

    for platform, scraper in scrapers.items():
        print(f"\n📱 Testing {platform.upper()}...")
        print("-" * 40)

        try:
            # Test search
            results = list(scraper.search(
                keywords=["technology", "news"],
                limit=3
            ))

            if results:
                print(f"  ✅ Found {len(results)} records")
                for i, record in enumerate(results[:2], 1):
                    content = record.get("post_content", "")[:80]
                    print(f"     {i}. {content}...")
            else:
                print(f"  ⚠️  No results (may need proxy/auth)")

        except Exception as e:
            print(f"  ❌ Error: {e}")

        finally:
            scraper.close()

    print("\n" + "="*60)
    print("✅ Test completed!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_scrapers()
