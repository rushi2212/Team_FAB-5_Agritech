import time
from typing import Dict, Any, List
from urllib.parse import quote_plus
from xml.etree import ElementTree

import requests

DEFAULT_TIMEOUT_SECONDS = 6
CACHE_TTL_SECONDS = 30 * 60
_CACHE: Dict[str, Dict[str, Any]] = {}


def _cache_get(city: str):
    cached = _CACHE.get(city)
    if not cached:
        return None
    if time.time() - cached["ts"] > CACHE_TTL_SECONDS:
        _CACHE.pop(city, None)
        return None
    return cached["value"]


def _cache_set(city: str, value: List[str]):
    _CACHE[city] = {"ts": time.time(), "value": value}


def scrape_crop_news(city: str) -> List[str]:
    city = (city or "").strip()
    if not city:
        return []

    cached = _cache_get(city.lower())
    if cached is not None:
        return cached

    query = f"crop prediction {city}"
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers,
                           timeout=DEFAULT_TIMEOUT_SECONDS)
        res.raise_for_status()
    except requests.RequestException:
        return []

    headlines = []
    try:
        root = ElementTree.fromstring(res.text)
        for item in root.findall(".//item"):
            title = item.findtext("title") or ""
            title = title.strip()
            if title and title not in headlines:
                headlines.append(title)
            if len(headlines) >= 5:
                break
    except ElementTree.ParseError:
        return []

    _cache_set(city.lower(), headlines)
    return headlines
