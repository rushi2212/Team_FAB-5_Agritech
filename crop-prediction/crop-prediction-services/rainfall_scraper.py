import time
from typing import Dict, Any, Optional, Tuple

import requests
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT_SECONDS = 6
CACHE_TTL_SECONDS = 6 * 60 * 60
_CACHE: Dict[str, Dict[str, Any]] = {}


def _cache_get(city: str):
    cached = _CACHE.get(city)
    if not cached:
        return None
    if time.time() - cached["ts"] > CACHE_TTL_SECONDS:
        _CACHE.pop(city, None)
        return None
    return cached["value"]


def _cache_set(city: str, value: str):
    _CACHE[city] = {"ts": time.time(), "value": value}


def _bucket_rainfall(mm: float) -> str:
    if mm >= 200:
        return "high"
    if mm >= 80:
        return "moderate"
    return "low"


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


def _open_meteo_rainfall(city: str) -> Optional[str]:
    coords = _geocode_city(city)
    if not coords or coords[0] is None or coords[1] is None:
        return None

    try:
        res = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": coords[0],
                "longitude": coords[1],
                "daily": "precipitation_sum",
                "timezone": "auto",
                "forecast_days": 7,
            },
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        res.raise_for_status()
        data = res.json()
    except requests.RequestException:
        return None

    daily = data.get("daily") or {}
    values = daily.get("precipitation_sum") or []
    if not values:
        return None
    avg_mm = sum(values) / len(values)
    return _bucket_rainfall(avg_mm)


def scrape_rainfall(city: str) -> str:
    city = (city or "").strip()
    if not city:
        return "moderate"

    cached = _cache_get(city.lower())
    if cached:
        return cached

    rainfall = _open_meteo_rainfall(city)
    if rainfall is None:
        url = f"https://www.timeanddate.com/weather/india/{city.lower()}/climate"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            res = requests.get(url, headers=headers,
                               timeout=DEFAULT_TIMEOUT_SECONDS)
            res.raise_for_status()
        except requests.RequestException:
            return "moderate"

        soup = BeautifulSoup(res.text, "lxml")

        rainfall = "moderate"
        if "rain" in soup.get_text(" ", strip=True).lower():
            rainfall = "high"

    _cache_set(city.lower(), rainfall)
    return rainfall
