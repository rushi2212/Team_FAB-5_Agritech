"""Simple test for FastAPI endpoint - run this while the server is running."""
import sys

try:
    import requests
except ImportError:
    print("Installing requests library...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("Testing FastAPI Market Price Prediction Endpoint")
print("=" * 70)

# Test 1: Check if server is running
print("\n1. Checking server health...")
try:
    response = requests.get(f"{BASE_URL}/")
    print(f"   ✓ Server is running")
    print(f"   Available endpoints: {list(response.json().keys())}")
except requests.exceptions.ConnectionError:
    print("   ✗ Server is not running. Start it with:")
    print("     python -m uvicorn main:app --reload --port 8000")
    sys.exit(1)

# Test 2: Market price prediction
print("\n2. Testing market price prediction endpoint...")
test_payload = {
    "crop_name": "wheat",
    "state": "Punjab",
    "season": "Rabi",
    "harvest_month": "March"
}

try:
    response = requests.post(
        f"{BASE_URL}/predict-market-price",
        json=test_payload
    )
    response.raise_for_status()
    result = response.json()
    
    print(f"   ✓ Prediction successful!")
    print(f"   Crop: {result['crop_name']} ({result['season']})")
    print(f"   State: {result['state']}")
    print(f"   Harvest Month: {result['harvest_month']}")
    print(f"   Average Price: ₹{result['average_price']}/quintal")
    print(f"   Price Range: ₹{result['predicted_price_range']['min']} - ₹{result['predicted_price_range']['max']}")
    print(f"   Trend: {result['trend']}")
    print(f"   Confidence: {result['confidence']}")
    print(f"   Data Sources: {', '.join(result['data_sources'])}")
    
except requests.exceptions.RequestException as e:
    print(f"   ✗ Request failed: {e}")
    sys.exit(1)

# Test 3: Multiple predictions
print("\n3. Testing multiple predictions...")
test_cases = [
    {"crop_name": "rice", "state": "Maharashtra", "season": "Kharif", "harvest_month": "October"},
    {"crop_name": "cotton", "state": "Gujarat", "season": "Kharif", "harvest_month": "November"},
]

for i, payload in enumerate(test_cases, 1):
    response = requests.post(f"{BASE_URL}/predict-market-price", json=payload)
    result = response.json()
    print(f"   {i}. {payload['crop_name']}: ₹{result['average_price']}/quintal ({result['trend']})")

# Test 4: Error handling
print("\n4. Testing error handling...")
try:
    response = requests.post(
        f"{BASE_URL}/predict-market-price",
        json={"crop_name": "", "state": "Punjab"}  # Invalid: missing required fields
    )
    if response.status_code in [400, 422]:
        print(f"   ✓ Validation error handled correctly (status: {response.status_code})")
    else:
        print(f"   ⚠ Unexpected status code: {response.status_code}")
except Exception as e:
    print(f"   ⚠ Error test failed: {e}")

print("\n" + "=" * 70)
print("All FastAPI endpoint tests completed!")
print("=" * 70)
