"""Test script for pest & disease risk agent."""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

print("=" * 70)
print("Pest & Disease Risk Agent - Test")
print("=" * 70)

# Test 1: Check data files
print("\n1. Data Files Check")
from agents.pest_disease_agent import VARIABLE_PATH, CALENDAR_PATH

variable_exists = VARIABLE_PATH.exists()
calendar_exists = CALENDAR_PATH.exists()

print(f"   variable.json: {'✓ Found' if variable_exists else '✗ Missing'}")
print(f"   calendar.json: {'✓ Found' if calendar_exists else '✗ Missing'}")

if not variable_exists:
    print("\n   ⚠ Cannot proceed without variable.json")
    print("   Run: POST /generate-variable first")
    sys.exit(1)

# Test 2: Load and display current crop info
print("\n2. Current Crop Information")
try:
    from agents.pest_disease_agent import load_variable, load_calendar, get_current_stage
    
    variable = load_variable()
    calendar = load_calendar()
    
    crop_name = variable.get("crop", {}).get("crop_name", "Unknown")
    season = variable.get("crop", {}).get("season", "Unknown")
    day_of_cycle = variable.get("day_of_cycle", 1)
    climate = variable.get("climate", {})
    
    crop_stage = "Unknown"
    if calendar:
        crop_stage = get_current_stage(calendar, day_of_cycle)
    
    print(f"   Crop: {crop_name} ({season})")
    print(f"   Stage: {crop_stage} (Day {day_of_cycle})")
    print(f"   Temperature: {climate.get('temperature_c', 'N/A')}°C")
    print(f"   Humidity: {climate.get('humidity_percent', 'N/A')}%")
    print(f"   Rainfall: {climate.get('rainfall_mm', 'N/A')}mm")
except Exception as e:
    print(f"   ✗ Error loading data: {e}")
    sys.exit(1)

# Test 3: Run risk assessment (no email)
print("\n3. Risk Assessment")
try:
    from agents.pest_disease_agent import run as run_pest_agent
    
    result = run_pest_agent(user_email="")
    
    print(f"\n   Overall Risk: {result['risk_level'].upper()} ({result['risk_score']}/100)")
    
    if result['pest_risks']:
        print(f"\n   🐛 Pest Risks ({len(result['pest_risks'])}):")
        for pest in result['pest_risks']:
            print(f"      • {pest['name']} ({pest['severity']}): {pest['description']}")
    else:
        print("\n   ✓ No pest risks detected")
    
    if result['disease_risks']:
        print(f"\n   🦠 Disease Risks ({len(result['disease_risks'])}):")
        for disease in result['disease_risks']:
            print(f"      • {disease['name']} ({disease['severity']}): {disease['description']}")
    else:
        print("\n   ✓ No disease risks detected")
    
    print(f"\n   🛡️ Preventive Actions ({len(result['preventive_actions'])}):")
    for i, action in enumerate(result['preventive_actions'][:5], 1):
        print(f"      {i}. {action}")
    if len(result['preventive_actions']) > 5:
        print(f"      ... and {len(result['preventive_actions']) - 5} more")
    
except Exception as e:
    print(f"   ✗ Risk assessment failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check cache
print("\n4. Cache Status")
from agents.pest_disease_agent import PEST_DISEASE_CACHE

if PEST_DISEASE_CACHE.exists():
    print(f"   ✓ Cache saved: {PEST_DISEASE_CACHE}")
    with open(PEST_DISEASE_CACHE, "r", encoding="utf-8") as f:
        cache_data = json.load(f)
    print(f"   Last updated: {cache_data.get('last_updated', 'Unknown')}")
else:
    print("   ⚠ No cache file created")

# Test 5: Email configuration check
print("\n5. Email Configuration")
import os
smtp_user = os.getenv("SMTP_USER", "")
smtp_pass = os.getenv("SMTP_PASSWORD", "")

if smtp_user and smtp_pass:
    print(f"   ✓ Email configured: {smtp_user[:10]}...")
    print("   Ready to send alerts when risk >= medium")
else:
    print("   ⚠ Email not configured")
    print("   Set SMTP_USER and SMTP_PASSWORD in .env to enable alerts")

print("\n" + "=" * 70)
print("✓ All tests completed!")
print("=" * 70)

# Show full result
print("\nFull Assessment Result:")
print(json.dumps(result, indent=2, ensure_ascii=False))
