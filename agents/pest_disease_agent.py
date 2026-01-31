"""
Pest & Disease Risk Agent
Early warning system for crop health threats based on weather conditions,
crop stage, and environmental factors.

Provides:
- Risk level assessment (low/medium/high/critical)
- Specific pest and disease warnings
- Preventive action recommendations
- Email alerts to farmers (via Node.js nodemailer service)

Uses data from:
- variable.json (current weather, crop info)
- calendar.json (crop stage information)
- Historical pest/disease patterns
"""
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError

from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
_AGENT_DATA_DIR = Path(__file__).resolve().parent / "data"
_AGENT_DATA_DIR.mkdir(parents=True, exist_ok=True)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
VARIABLE_PATH = _DATA_DIR / "variable.json"
CALENDAR_PATH = _DATA_DIR / "calendar.json"

PEST_DISEASE_CACHE = _AGENT_DATA_DIR / "pest_disease_risk.json"

# Node.js email service URL
NODE_EMAIL_SERVICE_URL = os.getenv("NODE_EMAIL_SERVICE_URL", "http://localhost:3000/api/send-pest-alert")

# Risk thresholds
RISK_THRESHOLDS = {
    "low": (0, 30),
    "medium": (30, 60),
    "high": (60, 85),
    "critical": (85, 100)
}

# Pest and disease database by crop
PEST_DISEASE_DB = {
    "rice": {
        "pests": {
            "stem_borer": {
                "name": "Stem Borer",
                "stages": ["Vegetative", "Tillering", "Panicle Initiation"],
                "humidity_range": (70, 100),
                "temp_range": (25, 32),
                "rainfall_trigger": 5,
                "severity_base": 40,
                "description": "Larvae bore into stem causing dead hearts and white ears"
            },
            "brown_planthopper": {
                "name": "Brown Planthopper",
                "stages": ["Tillering", "Panicle Initiation", "Flowering"],
                "humidity_range": (80, 100),
                "temp_range": (25, 30),
                "rainfall_trigger": 0,
                "severity_base": 35,
                "description": "Sucks sap from plants, causes hopper burn"
            },
            "leaf_folder": {
                "name": "Leaf Folder",
                "stages": ["Vegetative", "Tillering"],
                "humidity_range": (75, 95),
                "temp_range": (20, 30),
                "rainfall_trigger": 3,
                "severity_base": 25,
                "description": "Folds leaves and feeds inside, reducing photosynthesis"
            }
        },
        "diseases": {
            "blast": {
                "name": "Blast Disease",
                "stages": ["Nursery", "Vegetative", "Panicle Initiation"],
                "humidity_range": (85, 100),
                "temp_range": (20, 28),
                "rainfall_trigger": 10,
                "severity_base": 50,
                "description": "Fungal disease causing diamond-shaped lesions on leaves"
            },
            "sheath_blight": {
                "name": "Sheath Blight",
                "stages": ["Tillering", "Panicle Initiation", "Flowering"],
                "humidity_range": (80, 100),
                "temp_range": (28, 35),
                "rainfall_trigger": 5,
                "severity_base": 45,
                "description": "Fungal disease affecting leaf sheaths, spreads rapidly"
            },
            "bacterial_blight": {
                "name": "Bacterial Leaf Blight",
                "stages": ["Vegetative", "Tillering", "Panicle Initiation"],
                "humidity_range": (70, 100),
                "temp_range": (25, 34),
                "rainfall_trigger": 15,
                "severity_base": 40,
                "description": "Bacterial infection causing water-soaked lesions"
            }
        }
    },
    "wheat": {
        "pests": {
            "aphids": {
                "name": "Aphids",
                "stages": ["Vegetative", "Flowering", "Grain Filling"],
                "humidity_range": (60, 80),
                "temp_range": (15, 25),
                "rainfall_trigger": 0,
                "severity_base": 30,
                "description": "Suck plant sap, transmit viral diseases"
            },
            "termites": {
                "name": "Termites",
                "stages": ["Germination", "Vegetative"],
                "humidity_range": (50, 70),
                "temp_range": (20, 35),
                "rainfall_trigger": 0,
                "severity_base": 35,
                "description": "Attack roots and stems at soil level"
            }
        },
        "diseases": {
            "rust": {
                "name": "Rust (Yellow/Brown/Black)",
                "stages": ["Vegetative", "Flowering", "Grain Filling"],
                "humidity_range": (70, 100),
                "temp_range": (15, 25),
                "rainfall_trigger": 2,
                "severity_base": 55,
                "description": "Fungal disease causing rust-colored pustules on leaves"
            },
            "powdery_mildew": {
                "name": "Powdery Mildew",
                "stages": ["Vegetative", "Flowering"],
                "humidity_range": (60, 90),
                "temp_range": (15, 22),
                "rainfall_trigger": 0,
                "severity_base": 40,
                "description": "White powdery fungal growth on leaves"
            }
        }
    },
    "cotton": {
        "pests": {
            "bollworm": {
                "name": "Bollworm",
                "stages": ["Flowering", "Boll Formation"],
                "humidity_range": (60, 80),
                "temp_range": (25, 35),
                "rainfall_trigger": 0,
                "severity_base": 60,
                "description": "Larvae feed on squares, flowers, and bolls"
            },
            "whitefly": {
                "name": "Whitefly",
                "stages": ["Vegetative", "Flowering"],
                "humidity_range": (70, 90),
                "temp_range": (27, 35),
                "rainfall_trigger": 0,
                "severity_base": 45,
                "description": "Sucks sap and transmits leaf curl virus"
            }
        },
        "diseases": {
            "wilt": {
                "name": "Wilt",
                "stages": ["Vegetative", "Flowering"],
                "humidity_range": (70, 100),
                "temp_range": (25, 35),
                "rainfall_trigger": 10,
                "severity_base": 50,
                "description": "Fungal disease causing wilting and plant death"
            }
        }
    },
    "tomato": {
        "pests": {
            "fruit_borer": {
                "name": "Fruit Borer",
                "stages": ["Flowering", "Fruiting"],
                "humidity_range": (65, 85),
                "temp_range": (20, 30),
                "rainfall_trigger": 0,
                "severity_base": 50,
                "description": "Larvae bore into fruits causing damage"
            },
            "whitefly": {
                "name": "Whitefly",
                "stages": ["Vegetative", "Flowering", "Fruiting"],
                "humidity_range": (70, 90),
                "temp_range": (25, 32),
                "rainfall_trigger": 0,
                "severity_base": 40,
                "description": "Transmits tomato leaf curl virus"
            }
        },
        "diseases": {
            "early_blight": {
                "name": "Early Blight",
                "stages": ["Vegetative", "Flowering", "Fruiting"],
                "humidity_range": (80, 100),
                "temp_range": (24, 29),
                "rainfall_trigger": 5,
                "severity_base": 45,
                "description": "Fungal disease causing concentric ring spots on leaves"
            },
            "late_blight": {
                "name": "Late Blight",
                "stages": ["Flowering", "Fruiting"],
                "humidity_range": (90, 100),
                "temp_range": (10, 25),
                "rainfall_trigger": 10,
                "severity_base": 60,
                "description": "Devastating fungal disease affecting leaves and fruits"
            }
        }
    },
    "potato": {
        "pests": {
            "aphids": {
                "name": "Aphids",
                "stages": ["Vegetative", "Tuber Formation"],
                "humidity_range": (60, 80),
                "temp_range": (18, 25),
                "rainfall_trigger": 0,
                "severity_base": 35,
                "description": "Transmit viral diseases, reduce yield"
            }
        },
        "diseases": {
            "late_blight": {
                "name": "Late Blight",
                "stages": ["Vegetative", "Tuber Formation"],
                "humidity_range": (90, 100),
                "temp_range": (10, 25),
                "rainfall_trigger": 10,
                "severity_base": 65,
                "description": "Most destructive potato disease, causes rapid death"
            }
        }
    }
}

# Preventive actions database
PREVENTIVE_ACTIONS = {
    "low": [
        "Monitor crop regularly for early signs of pests/diseases",
        "Maintain field sanitation and remove crop residues",
        "Ensure proper drainage to prevent waterlogging",
        "Use pheromone traps for pest monitoring"
    ],
    "medium": [
        "Increase monitoring frequency to twice weekly",
        "Remove and destroy infected plants immediately",
        "Apply recommended bio-pesticides (Neem-based products)",
        "Ensure adequate plant spacing for air circulation",
        "Apply sticky traps to monitor insect populations",
        "Spray Trichoderma for fungal disease prevention"
    ],
    "high": [
        "Apply recommended chemical pesticides immediately",
        "Increase field inspection to daily monitoring",
        "Set up pheromone traps at 20-25 traps per hectare",
        "Apply systemic fungicides for disease prevention",
        "Consider emergency spraying schedule (every 7 days)",
        "Consult with agricultural extension officer",
        "Isolate affected field areas to prevent spread"
    ],
    "critical": [
        "⚠️ URGENT: Apply emergency pest/disease control measures NOW",
        "Contact agricultural extension officer IMMEDIATELY",
        "Implement emergency spray schedule (every 3-5 days)",
        "Isolate and quarantine severely affected areas",
        "Consider crop loss mitigation and insurance claims",
        "Daily monitoring and treatment REQUIRED",
        "Deploy all available IPM (Integrated Pest Management) strategies",
        "Prepare for potential crop salvage or early harvest"
    ]
}


def load_variable() -> dict[str, Any]:
    """Load variable.json with current crop and weather data."""
    if not VARIABLE_PATH.exists():
        raise FileNotFoundError(f"variable.json not found at {VARIABLE_PATH}")
    with open(VARIABLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_calendar() -> dict[str, Any] | None:
    """Load calendar.json with crop stage information."""
    if not CALENDAR_PATH.exists():
        return None
    try:
        with open(CALENDAR_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def get_current_stage(calendar: dict[str, Any], day_of_cycle: int) -> str:
    """Extract current crop stage from calendar based on day of cycle."""
    if not calendar or "days" not in calendar:
        return "Unknown"
    
    # Find the day entry
    for day_entry in calendar["days"]:
        if day_entry.get("day_index") == day_of_cycle:
            return day_entry.get("stage_name", "Unknown")
    
    # If exact day not found, find closest
    for day_entry in calendar["days"]:
        if day_entry.get("day_index", 0) >= day_of_cycle:
            return day_entry.get("stage_name", "Unknown")
    
    return "Unknown"


def assess_pest_risk(
    pest_data: dict[str, Any],
    current_stage: str,
    temp: float,
    humidity: float,
    rainfall: float
) -> tuple[bool, float, str]:
    """
    Assess risk for a specific pest.
    Returns (at_risk, severity_score, reason)
    """
    # Check if current stage is vulnerable
    if current_stage not in pest_data["stages"]:
        return False, 0, "Not vulnerable at this stage"
    
    severity = 0
    reasons = []
    
    # Check humidity
    h_min, h_max = pest_data["humidity_range"]
    if h_min <= humidity <= h_max:
        severity += pest_data["severity_base"] * 0.4
        reasons.append(f"humidity {humidity}% in risk range")
    
    # Check temperature
    t_min, t_max = pest_data["temp_range"]
    if t_min <= temp <= t_max:
        severity += pest_data["severity_base"] * 0.4
        reasons.append(f"temperature {temp}°C favorable")
    
    # Check rainfall
    if rainfall >= pest_data["rainfall_trigger"]:
        severity += pest_data["severity_base"] * 0.2
        reasons.append(f"rainfall {rainfall}mm triggers risk")
    
    # Vulnerable stage bonus
    severity += 10
    
    at_risk = severity > 20
    reason = "; ".join(reasons) if reasons else "Conditions not favorable"
    
    return at_risk, severity, reason


def calculate_risk_level(score: float) -> str:
    """Convert numerical risk score to risk level."""
    for level, (min_val, max_val) in RISK_THRESHOLDS.items():
        if min_val <= score < max_val:
            return level
    return "critical" if score >= 85 else "low"


def assess_risks(
    crop_name: str,
    crop_stage: str,
    temperature: float,
    humidity: float,
    rainfall: float,
    day_of_cycle: int
) -> dict[str, Any]:
    """
    Main risk assessment function.
    Returns complete risk analysis with pests, diseases, and recommendations.
    """
    print(f"[Pest Risk Agent] Assessing risks for {crop_name} at stage {crop_stage}")
    print(f"[Pest Risk Agent] Weather: {temperature}°C, {humidity}% humidity, {rainfall}mm rain")
    
    crop_lower = crop_name.lower()
    
    # Get crop database or use default
    if crop_lower not in PEST_DISEASE_DB:
        print(f"[Pest Risk Agent] No specific data for {crop_name}, using general assessment")
        return {
            "crop_name": crop_name,
            "crop_stage": crop_stage,
            "day_of_cycle": day_of_cycle,
            "risk_level": "low",
            "risk_score": 15.0,
            "pest_risks": [],
            "disease_risks": [],
            "preventive_actions": PREVENTIVE_ACTIONS["low"],
            "weather_factors": {
                "temperature_c": temperature,
                "humidity_percent": humidity,
                "rainfall_mm": rainfall
            },
            "email_sent": False,
            "last_updated": date.today().isoformat()
        }
    
    crop_db = PEST_DISEASE_DB[crop_lower]
    
    pest_risks = []
    disease_risks = []
    total_score = 0
    risk_count = 0
    
    # Assess pests
    for pest_id, pest_data in crop_db.get("pests", {}).items():
        at_risk, severity, reason = assess_pest_risk(
            pest_data, crop_stage, temperature, humidity, rainfall
        )
        if at_risk:
            pest_risks.append({
                "name": pest_data["name"],
                "severity": calculate_risk_level(severity),
                "score": round(severity, 1),
                "description": pest_data["description"],
                "reason": reason
            })
            total_score += severity
            risk_count += 1
    
    # Assess diseases (same logic as pests)
    for disease_id, disease_data in crop_db.get("diseases", {}).items():
        at_risk, severity, reason = assess_pest_risk(
            disease_data, crop_stage, temperature, humidity, rainfall
        )
        if at_risk:
            disease_risks.append({
                "name": disease_data["name"],
                "severity": calculate_risk_level(severity),
                "score": round(severity, 1),
                "description": disease_data["description"],
                "reason": reason
            })
            total_score += severity
            risk_count += 1
    
    # Calculate overall risk score
    risk_score = (total_score / risk_count) if risk_count > 0 else 0
    risk_level = calculate_risk_level(risk_score)
    
    # Get preventive actions
    actions = PREVENTIVE_ACTIONS.get(risk_level, PREVENTIVE_ACTIONS["low"]).copy()
    
    # Add specific actions for identified risks
    if pest_risks:
        actions.append(f"Target pests: {', '.join([p['name'] for p in pest_risks])}")
    if disease_risks:
        actions.append(f"Target diseases: {', '.join([d['name'] for d in disease_risks])}")
    
    print(f"[Pest Risk Agent] Risk assessment complete: {risk_level.upper()} ({risk_score:.1f}/100)")
    print(f"[Pest Risk Agent] Found {len(pest_risks)} pest risks, {len(disease_risks)} disease risks")
    
    return {
        "crop_name": crop_name,
        "crop_stage": crop_stage,
        "day_of_cycle": day_of_cycle,
        "risk_level": risk_level,
        "risk_score": round(risk_score, 1),
        "pest_risks": pest_risks,
        "disease_risks": disease_risks,
        "preventive_actions": actions,
        "weather_factors": {
            "temperature_c": temperature,
            "humidity_percent": humidity,
            "rainfall_mm": rainfall
        },
        "email_sent": False,
        "last_updated": date.today().isoformat()
    }


def assess_pest_disease_risk(variable_data: dict[str, Any], current_stage: str | None = None) -> dict[str, Any]:
    """Compatibility helper used by the chatbot for quick risk lookups."""
    try:
        if not isinstance(variable_data, dict):  # Ensure dict access
            variable_data = {}

        crop_info = variable_data.get("crop", {})
        crop_name = (
            crop_info.get("crop_name")
            or crop_info.get("name")
            or variable_data.get("crop_name")
            or "Unknown"
        )

        day_of_cycle = variable_data.get("day_of_cycle", 1)

        climate = variable_data.get("climate", {})
        temperature = (
            climate.get("temperature_c")
            or climate.get("temperature_2m")
            or variable_data.get("temperature_c")
            or 25
        )
        humidity = (
            climate.get("humidity_percent")
            or climate.get("relative_humidity_2m")
            or variable_data.get("humidity_percent")
            or 70
        )
        rainfall = (
            climate.get("rainfall_mm")
            or climate.get("precipitation")
            or variable_data.get("rainfall_mm")
            or 0
        )

        if not current_stage or current_stage == "Unknown":
            calendar = load_calendar()
            if calendar:
                current_stage = get_current_stage(calendar, day_of_cycle)
            else:
                current_stage = variable_data.get("current_stage", "Unknown")

        risk_details = assess_risks(
            crop_name=crop_name,
            crop_stage=current_stage,
            temperature=float(temperature),
            humidity=float(humidity),
            rainfall=float(rainfall),
            day_of_cycle=day_of_cycle,
        )

        return {
            "overall_risk_level": risk_details.get("risk_level", "unknown"),
            "risk_score": risk_details.get("risk_score", 0),
            "pests": risk_details.get("pest_risks", []),
            "diseases": risk_details.get("disease_risks", []),
            "preventive_actions": risk_details.get("preventive_actions", []),
            "weather": risk_details.get("weather_factors", {}),
            "crop_stage": current_stage,
        }
    except Exception as exc:
        return {
            "overall_risk_level": "unknown",
            "risk_score": 0,
            "pests": [],
            "diseases": [],
            "error": str(exc),
        }


def send_alert_email(risk_data: dict[str, Any], recipient_email: str) -> bool:
    """
    Send email alert to farmer about pest/disease risks via Node.js nodemailer service.
    Returns True if email sent successfully.
    """
    if not recipient_email:
        print("[Pest Risk Agent] No recipient email provided")
        return False
    
    try:
        # Prepare request payload
        payload = {
            "riskData": risk_data,
            "recipientEmail": recipient_email
        }
        
        # Call Node.js email service
        print(f"[Pest Risk Agent] Sending alert email to {recipient_email} via Node.js service...")
        
        req = Request(
            NODE_EMAIL_SERVICE_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if result.get('success'):
                print("[Pest Risk Agent] ✓ Email sent successfully via Node.js")
                return True
            else:
                print(f"[Pest Risk Agent] ✗ Email service returned error: {result.get('error', 'Unknown')}")
                return False
                
    except URLError as e:
        print(f"[Pest Risk Agent] ✗ Failed to connect to email service: {e.reason}")
        print(f"[Pest Risk Agent]   Make sure Node.js server is running on port 3000")
        return False
    except Exception as e:
        print(f"[Pest Risk Agent] ✗ Email failed: {e}")
        return False


def run(user_email: str = "") -> dict[str, Any]:
    """
    Main entry point for pest & disease risk agent.
    Reads variable.json and calendar.json, assesses risks, sends email if needed.
    """
    # Load data
    variable = load_variable()
    calendar = load_calendar()
    
    # Extract data
    crop_name = variable.get("crop", {}).get("crop_name", "Unknown")
    day_of_cycle = variable.get("day_of_cycle", 1)
    
    # Get current stage from calendar
    crop_stage = "Unknown"
    if calendar:
        crop_stage = get_current_stage(calendar, day_of_cycle)
    
    # Get current weather from variable (baseline climate)
    climate = variable.get("climate", {})
    temperature = climate.get("temperature_c", 25)
    humidity = climate.get("humidity_percent", 70)
    rainfall = climate.get("rainfall_mm", 0)
    
    # Assess risks
    risk_data = assess_risks(
        crop_name=crop_name,
        crop_stage=crop_stage,
        temperature=temperature,
        humidity=humidity,
        rainfall=rainfall,
        day_of_cycle=day_of_cycle
    )
    
    # Send email if risk is medium or higher
    if user_email and risk_data["risk_level"] in ["medium", "high", "critical"]:
        email_sent = send_alert_email(risk_data, user_email)
        risk_data["email_sent"] = email_sent
    
    # Cache result
    with open(PEST_DISEASE_CACHE, "w", encoding="utf-8") as f:
        json.dump(risk_data, f, indent=2, ensure_ascii=False)
    
    return risk_data


if __name__ == "__main__":
    """Test the agent standalone."""
    import sys
    
    user_email = sys.argv[1] if len(sys.argv) > 1 else ""
    
    result = run(user_email)
    print("\n" + "="*70)
    print("PEST & DISEASE RISK ASSESSMENT")
    print("="*70)
    print(json.dumps(result, indent=2, ensure_ascii=False))
