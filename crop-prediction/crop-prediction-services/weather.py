import os
import time
from typing import Dict, Any, Optional, Tuple

import requests

DEFAULT_TIMEOUT_SECONDS = 6
CACHE_TTL_SECONDS = 15 * 60
_CACHE: Dict[str, Dict[str, Any]] = {}


def _cache_get(city: str):
    cached = _CACHE.get(city)
    if not cached:
        return None
    if time.time() - cached["ts"] > CACHE_TTL_SECONDS:
        _CACHE.pop(city, None)
        return None
    return cached["value"]


def _cache_set(city: str, value: Dict[str, Any]):
    _CACHE[city] = {"ts": time.time(), "value": value}


def _geocode_city(city: str) -> Optional[Tuple[float, float]]:
    try:
        res = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1,
                    "language": "en", "format": "json"},
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        res.raise_for_status()
        data = res.json()
        results = data.get("results") or []
        if not results:
            return None
        return results[0].get("latitude"), results[0].get("longitude")
    except requests.RequestException:
        return None


def _open_meteo_weather(city: str) -> Dict[str, Any]:
    coords = _geocode_city(city)
    if not coords or coords[0] is None or coords[1] is None:
        return {"temperature": None, "humidity": None, "condition": "unknown"}

    try:
        res = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": coords[0],
                "longitude": coords[1],
                "current": "temperature_2m,relative_humidity_2m,weather_code",
                "timezone": "auto",
            },
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        res.raise_for_status()
        data = res.json()
    except requests.RequestException:
        return {"temperature": None, "humidity": None, "condition": "unknown"}

    current = data.get("current") or {}
    code = current.get("weather_code")
    condition = "unknown"
    if isinstance(code, int):
        if code in {0, 1}:
            condition = "Clear"
        elif code in {2, 3}:
            condition = "Clouds"
        elif code in {45, 48}:
            condition = "Fog"
        elif code in {51, 53, 55, 61, 63, 65, 80, 81, 82}:
            condition = "Rain"
        elif code in {71, 73, 75, 77, 85, 86}:
            condition = "Snow"
        elif code in {95, 96, 99}:
            condition = "Thunderstorm"

    return {
        "temperature": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "condition": condition,
    }


def get_weather(city: str) -> Dict[str, Any]:
    city = (city or "").strip()
    if not city:
        return {"temperature": None, "humidity": None, "condition": "unknown"}

    cached = _cache_get(city.lower())
    if cached:
        return cached

    api_key = os.getenv("OPENWEATHER_API_KEY") or ""
    weather: Dict[str, Any]

    if api_key:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": api_key, "units": "metric"}

        try:
            res = requests.get(url, params=params,
                               timeout=DEFAULT_TIMEOUT_SECONDS)
            res.raise_for_status()
            data = res.json()
            weather = {
                "temperature": data.get("main", {}).get("temp"),
                "humidity": data.get("main", {}).get("humidity"),
                "condition": (data.get("weather") or [{}])[0].get("main", "unknown"),
            }
        except requests.RequestException:
            weather = _open_meteo_weather(city)
    else:
        weather = _open_meteo_weather(city)

    _cache_set(city.lower(), weather)
    return weather
