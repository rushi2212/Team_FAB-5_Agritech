import json
import os
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI
from dotenv import load_dotenv


DEFAULT_MODEL = "gpt-5-mini"

# Load env vars from crop-prediction/.env
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


def _extract_text(response) -> str:
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text
    try:
        for item in response.output or []:
            for content in getattr(item, "content", []) or []:
                if getattr(content, "type", "") == "output_text":
                    return getattr(content, "text", "") or ""
    except Exception:
        pass
    return ""


def _safe_json_loads(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        return {}


def recommend_with_ai(
    city: str,
    soil_type: str,
    weather: Dict[str, Any],
    rainfall: str,
    news: List[str],
) -> Dict[str, Any]:
    debug = (os.getenv("OPENAI_DEBUG") or "").strip().lower() in {
        "1", "true", "yes"}
    api_key = os.getenv("OPENAI_API_KEY") or ""
    if not api_key:
        return {"crops": [], "rationale": "OPENAI_API_KEY not set"}

    weather_missing = (
        not isinstance(weather, dict)
        or (weather.get("temperature") is None and weather.get("humidity") is None)
    )
    if weather_missing and not news:
        return {
            "crops": [],
            "rationale": "Insufficient external data; cannot recommend crops",
        }

    client = OpenAI(api_key=api_key)

    city_norm = (city or "").strip().lower()
    soil_norm = (soil_type or "").strip().lower()

    news_text = " ".join(news).lower()
    signals: List[str] = []
    if "drought" in news_text or "dry" in news_text:
        signals.append("drought risk")
    if "flood" in news_text or "heavy rainfall" in news_text or "extremely heavy" in news_text:
        signals.append("flood risk")
    if "rainfall" in news_text and "low" in news_text:
        signals.append("low rainfall mentioned")

    climate_signal = {
        "temperature_c": weather.get("temperature") if isinstance(weather, dict) else None,
        "humidity_pct": weather.get("humidity") if isinstance(weather, dict) else None,
        "rainfall_bucket": rainfall,
        "news_signals": signals,
    }

    system = (
        "You are an agronomy assistant. Provide final crop recommendations "
        "based on the provided data. Return strict JSON only with keys: "
        "crops (array of 3 strings), rationale (short string). "
        "Prioritize crops that are commonly cultivated in the given location and are "
        "suitable for the soil type and climate signals. Avoid crops that are primarily "
        "arid-region crops if the location indicates a humid/subtropical region unless "
        "news signals strongly indicate prolonged drought."
    )

    user = {
        "city": city,
        "soil_type": soil_type,
        "weather": weather,
        "rainfall": rainfall,
        "news_headlines": news,
        "climate_signal": climate_signal,
        "location_hint": city_norm,
        "soil_hint": soil_norm,
    }

    try:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user)},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "crop_recommendation",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "crops": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 1,
                                "maxItems": 3,
                            },
                            "rationale": {"type": "string"},
                        },
                        "required": ["crops", "rationale"],
                        "additionalProperties": False,
                    },
                },
            },
        )
    except TypeError:
        try:
            response = client.responses.create(
                model=DEFAULT_MODEL,
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(user)},
                ],
            )
        except Exception as exc:
            message = f"AI request failed: {exc.__class__.__name__}"
            if debug and str(exc):
                message = f"{message}: {str(exc)}"
            return {"crops": [], "rationale": message}
    except Exception as exc:
        message = f"AI request failed: {exc.__class__.__name__}"
        if debug and str(exc):
            message = f"{message}: {str(exc)}"
        return {"crops": [], "rationale": message}

    text = _extract_text(response).strip()
    data = _safe_json_loads(text)

    crops = data.get("crops") if isinstance(data, dict) else None
    rationale = data.get("rationale") if isinstance(data, dict) else None

    if not isinstance(crops, list) or len(crops) == 0:
        message = "AI response unavailable"
        if debug and text:
            message = f"{message}: {text[:200]}"
        return {"crops": [], "rationale": message}

    return {
        "crops": crops[:3],
        "rationale": rationale or "AI recommendation",
    }
