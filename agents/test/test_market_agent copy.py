"""Test script for market price prediction agent and endpoint."""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Test 1: Agent standalone
print("=" * 70)
print("TEST 1: Market Price Agent Standalone")
print("=" * 70)

from agents.market_price_agent import run as run_price_agent

test_cases = [
    ("rice", "Maharashtra", "Kharif", "October"),
    ("wheat", "Punjab", "Rabi", "March"),
    ("cotton", "Gujarat", "Kharif", "November"),
    ("tomato", "Karnataka", "Summer", "May"),
]

for crop, state, season, harvest_month in test_cases:
    print(f"\nTesting: {crop} in {state} ({season}, harvest: {harvest_month})")
    result = run_price_agent(crop, state, season, harvest_month)
    print(f"  Average Price: ₹{result['average_price']}/quintal")
    print(f"  Price Range: ₹{result['predicted_price_range']['min']} - ₹{result['predicted_price_range']['max']}")
    print(f"  Trend: {result['trend']} (Confidence: {result['confidence']})")
    print(f"  Sources: {', '.join(result['data_sources'])}")

print("\n" + "=" * 70)
print("TEST 2: Check cached data")
print("=" * 70)

from agents.market_price_agent import MARKET_PRICE_CACHE

if MARKET_PRICE_CACHE.exists():
    with open(MARKET_PRICE_CACHE, "r", encoding="utf-8") as f:
        cache = json.load(f)
    print(f"\nCache file: {MARKET_PRICE_CACHE}")
    print(f"Cached entries: {len(cache)}")
    for key in cache:
        print(f"  - {key}: last updated {cache[key].get('last_updated', 'unknown')}")
else:
    print("No cache file found.")

print("\n" + "=" * 70)
print("TEST 3: Schema validation")
print("=" * 70)

from services.schemas import MarketPricePrediction

try:
    # Test with valid data
    prediction = MarketPricePrediction(
        crop_name="rice",
        state="Maharashtra",
        season="Kharif",
        harvest_month="October",
        predicted_price_range={"min": 1800, "max": 2200},
        average_price=2000,
        trend="stable",
        confidence="high",
        data_sources=["agmarknet"],
    )
    print("\n✓ Schema validation passed")
    print(f"  Serialized: {prediction.model_dump_json()[:100]}...")
except Exception as e:
    print(f"\n✗ Schema validation failed: {e}")

print("\n" + "=" * 70)
print("All tests completed!")
print("=" * 70)
