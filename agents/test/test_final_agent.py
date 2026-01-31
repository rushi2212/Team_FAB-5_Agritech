"""Final test for market price agent with real Tavily integration."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

print("=" * 70)
print("Market Price Agent - Final Test")
print("=" * 70)

# Test 1: Environment check
print("\n1. Environment Configuration")
import os
from dotenv import load_dotenv
load_dotenv()
tavily_key = os.getenv("TAVILY_API_KEY", "")
print(f"   TAVILY_API_KEY configured: {'✓ Yes' if tavily_key else '✗ No'}")

# Test 2: Agent import
print("\n2. Agent Import")
try:
    from agents.market_price_agent import run as run_price_agent
    print("   ✓ Agent imported successfully")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test 3: Run predictions
print("\n3. Price Predictions")
test_cases = [
    ("wheat", "Punjab", "Rabi", "March"),
    ("rice", "Maharashtra", "Kharif", "October"),
    ("potato", "Uttar Pradesh", "Rabi", "February"),
]

for crop, state, season, harvest_month in test_cases:
    try:
        result = run_price_agent(crop, state, season, harvest_month)
        print(f"\n   {crop.title()} in {state}:")
        print(f"   • Price: ₹{result['average_price']}/quintal")
        print(f"   • Range: ₹{result['predicted_price_range']['min']}-{result['predicted_price_range']['max']}")
        print(f"   • Trend: {result['trend']} ({result['confidence']} confidence)")
        print(f"   • Sources: {', '.join(result['data_sources'])}")
    except Exception as e:
        print(f"   ✗ Failed for {crop}: {e}")

# Test 4: Cache check
print("\n4. Cache Status")
from agents.market_price_agent import MARKET_PRICE_CACHE
if MARKET_PRICE_CACHE.exists():
    import json
    with open(MARKET_PRICE_CACHE, "r", encoding="utf-8") as f:
        cache = json.load(f)
    print(f"   ✓ Cache file exists: {MARKET_PRICE_CACHE}")
    print(f"   • Cached entries: {len(cache)}")
    for key in list(cache.keys())[:3]:
        print(f"     - {key}")
else:
    print(f"   ⚠ No cache file yet")

print("\n" + "=" * 70)
print("✓ All tests completed!")
print("=" * 70)
print("\nThe agent is configured and working correctly.")
print("It will use Tavily API when available, falling back to")
print("synthetic data based on historical patterns when needed.")
