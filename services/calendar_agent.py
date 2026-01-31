"""
Calendar agent: reads data/variable.json and data/persistent.json,
ensures crop+state exists in persistent (via crop_agent.ensure_crop_data).
Plans from day 1; no current date stored in any file.
When remaking (threshold hit): send past days (1 to day_of_cycle-1) to LLM for context;
save only days day_of_cycle to cycle_duration_days in calendar.json (index from day_of_cycle onward).
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

try:
    from .crop_agent import ensure_crop_data, normalize_crop_key
except ImportError:
    from crop_agent import ensure_crop_data, normalize_crop_key

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
VARIABLE_PATH = _DATA_DIR / "variable.json"
PERSISTENT_PATH = _DATA_DIR / "persistent.json"
CALENDAR_PATH = _DATA_DIR / "calendar.json"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Thresholds: regenerate calendar when current weather deviates from baseline beyond these
TEMP_THRESHOLD_DEG_C = float(os.getenv("CALENDAR_TEMP_THRESHOLD_DEG_C", "7"))
HUMIDITY_THRESHOLD_PCT = float(os.getenv("CALENDAR_HUMIDITY_THRESHOLD_PCT", "40"))
RAIN_THRESHOLD_MM = float(os.getenv("CALENDAR_RAIN_THRESHOLD_MM", "20"))

# OpenAI reasoning model for calendar generation (o1-mini / o3-mini for cost; o1/o3 if available)
OPENAI_CALENDAR_MODEL = os.getenv("CALENDAR_OPENAI_MODEL", "o1-mini")
FORECAST_TIMEOUT = 20


def load_variable() -> dict[str, Any]:
    """Load data/variable.json. Raises if missing or invalid."""
    if not VARIABLE_PATH.exists():
        raise FileNotFoundError(f"Missing {VARIABLE_PATH}; run services/generate_variable.py first.")
    with open(VARIABLE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("variable.json must be a JSON object.")
    return data


def load_persistent() -> dict[str, Any]:
    """Load data/persistent.json; return {} if missing or empty."""
    if not PERSISTENT_PATH.exists() or PERSISTENT_PATH.stat().st_size == 0:
        return {}
    with open(PERSISTENT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def load_calendar() -> dict[str, Any] | None:
    """Load data/calendar.json if it exists and is valid; else return None."""
    if not CALENDAR_PATH.exists() or CALENDAR_PATH.stat().st_size == 0:
        return None
    try:
        with open(CALENDAR_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict) or "weather_baseline" not in data:
        return None
    return data


def ensure_crop_in_persistent(
    crop_name: str, state: str, season: str, persistent: dict[str, Any]
) -> dict[str, Any]:
    """If crop+state not in persistent, run ensure_crop_data and return updated persistent."""
    key = normalize_crop_key(crop_name, state)
    if key in persistent:
        return persistent
    ensure_crop_data(crop_name, state=state, season=season)
    return load_persistent()


def get_cycle_duration_days(persistent_entry: dict[str, Any], season: str) -> int:
    """Return cycle_duration_days for the given season from persistent entry."""
    season_data = (persistent_entry.get("seasons") or {}).get(season) or {}
    return int(season_data.get("cycle_duration_days") or 120)


def get_current_day(variable: dict[str, Any], cycle_duration_days: int) -> int:
    """
    Current day in the crop cycle (1-based). Uses only variable.day_of_cycle.
    Capped to 1..cycle_duration_days. No date used.
    """
    day = variable.get("day_of_cycle")
    if day is not None:
        try:
            d = int(day)
            if 1 <= d <= cycle_duration_days:
                return d
        except (TypeError, ValueError):
            pass
    return 1


def get_calendar_start_day(calendar: dict[str, Any]) -> int:
    """First day_index in calendar (1 if full calendar, or e.g. 5 after a remake from day 5)."""
    if calendar.get("start_day") is not None:
        return int(calendar["start_day"])
    days = calendar.get("days") or []
    if not days or not isinstance(days[0], dict):
        return 1
    return int(days[0].get("day_index", 1))


def should_regenerate(
    current_climate: dict[str, Any],
    calendar: dict[str, Any] | None,
    current_day: int,
) -> bool:
    """
    True only when: no calendar, or current climate (variable.json) for this day
    deviates from that day's weather in calendar.json beyond thresholds.
    Calendar days may start at day_index > 1 (e.g. 5 to 120 after a remake).
    """
    if calendar is None:
        return True
    days = calendar.get("days") or []
    start_day = get_calendar_start_day(calendar)
    # Index of current_day in array: calendar has day_index start_day, start_day+1, ...
    idx = current_day - start_day
    if idx < 0 or idx >= len(days):
        return False
    day_entry = days[idx]
    if not isinstance(day_entry, dict):
        return False
    baseline = day_entry.get("weather")
    if not baseline:
        return False
    for key, threshold in (
        ("temperature_c", TEMP_THRESHOLD_DEG_C),
        ("humidity_percent", HUMIDITY_THRESHOLD_PCT),
        ("rainfall_mm", RAIN_THRESHOLD_MM),
    ):
        cur = current_climate.get(key)
        base = baseline.get(key)
        if cur is None or base is None:
            continue
        try:
            cur_f = float(cur)
            base_f = float(base)
        except (TypeError, ValueError):
            continue
        if abs(cur_f - base_f) > threshold:
            return True
    return False


def fetch_16day_forecast(lat: float, lon: float) -> list[dict[str, Any]]:
    """Fetch 16-day daily forecast from Open-Meteo. Returns list of daily dicts with date, temperature_c, humidity_percent, rainfall_mm."""
    from urllib.request import urlopen

    params = (
        f"latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean,precipitation_sum"
        "&forecast_days=16"
        "&timezone=auto"
    )
    url = f"{FORECAST_URL}?{params}"
    with urlopen(url, timeout=FORECAST_TIMEOUT) as resp:
        data = json.load(resp)
    daily = data.get("daily") or {}
    times = daily.get("time") or []
    t_max = daily.get("temperature_2m_max") or []
    t_min = daily.get("temperature_2m_min") or []
    hum = daily.get("relative_humidity_2m_mean") or []
    prec = daily.get("precipitation_sum") or []
    out = []
    for i in range(min(16, len(times))):
        tmax = t_max[i] if i < len(t_max) else None
        tmin = t_min[i] if i < len(t_min) else None
        temp = (float(tmax) + float(tmin)) / 2 if tmax is not None and tmin is not None else None
        h = hum[i] if i < len(hum) else None
        p = prec[i] if i < len(prec) else None
        out.append({
            "temperature_c": round(temp, 1) if temp is not None else None,
            "humidity_percent": int(h) if h is not None else None,
            "rainfall_mm": round(float(p), 1) if p is not None else None,
        })
    return out


def build_calendar_prompt(
    variable: dict[str, Any],
    persistent_entry: dict[str, Any],
    forecast: list[dict[str, Any]],
    cycle_duration_days: int,
    start_day: int,
    past_days: list[dict[str, Any]] | None = None,
) -> str:
    """Build prompt for OpenAI: full calendar (start_day=1) or from start_day onward (remake). If remake, include past_days for context."""
    loc = variable.get("location") or {}
    crop = variable.get("crop") or {}
    season_name = crop.get("season") or ""
    season_data = (persistent_entry.get("seasons") or {}).get(season_name) or {}
    stages = season_data.get("stages") or []
    pesticides = season_data.get("pesticides") or []
    fertilizers = season_data.get("fertilizers") or []
    sowing_months = season_data.get("sowing_months") or []
    harvesting_months = season_data.get("harvesting_months") or []

    num_days = cycle_duration_days - start_day + 1
    past_section = ""
    if past_days:
        past_section = f"""
**Past calendar (days 1 to {start_day - 1}) — for context only; already completed. Generate only from day {start_day} onward:**
{json.dumps(past_days, indent=2)}
"""

    prompt = f"""You are an expert agronomist. Plan by **day index** only (do not use any calendar dates). Given the inputs below, produce a crop calendar as a single JSON object.
{past_section}
**Location and crop (from variable.json):**
- State: {loc.get('state')}, City: {loc.get('city')}
- Crop: {crop.get('crop_name')}, Season: {season_name}
- Climate snapshot: {json.dumps(variable.get('climate') or {})}
- Soil type: {variable.get('soil_type')}
- Soil properties (0-5cm): {json.dumps((variable.get('soil_properties') or {}).get('0-5cm') or {})}

**Crop timeline (from persistent.json):**
- Cycle duration: {cycle_duration_days} days (day 1 = start, day {cycle_duration_days} = end)
- Sowing months: {sowing_months}, Harvesting months: {harvesting_months}
- Stages: {json.dumps([{'name': s.get('name'), 'start_pct': s.get('start_pct'), 'end_pct': s.get('end_pct'), 'description': (s.get('description') or '')[:80]} for s in stages])}
- Pesticides: {json.dumps([{'name': p.get('name'), 'stage': p.get('stage'), 'dosage': p.get('dosage')} for p in pesticides])}
- Fertilizers: {json.dumps([{'name': f.get('name'), 'stage': f.get('stage'), 'dosage': f.get('dosage')} for f in fertilizers])}

**16-day weather forecast (apply to days 1–16; days 17+ get repeated 16th day):**
{json.dumps(forecast, indent=2)}

**Task:** For each day from **{start_day}** to **{cycle_duration_days}**, determine the crop stage (from the stages list, using start_pct/end_pct of cycle) and list **detailed tasks** for that day. Use only day_index. Output valid JSON only, no markdown or explanation.

**Required JSON shape:** A single object with a "days" array. Each element: {{ "day_index": N, "stage_name": "...", "tasks": [...] }}. For day_index 47 and above you may add "weather_note": "Short aggregate outlook". Do not include "date" or "weather" in any object.

Provide exactly **{num_days}** objects in the "days" array, for day_index **{start_day}** through **{cycle_duration_days}** in order. Do NOT include days 1 to {start_day - 1} in the output. Be specific and practical with tasks."""
    return prompt


def _parse_json_response(content: str) -> dict[str, Any]:
    """Parse LLM JSON; fix common issues (trailing commas) and retry on failure."""
    content = content.strip()
    for attempt in range(2):
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            if attempt == 0:
                # Remove trailing commas before ] or }
                content = re.sub(r",\s*([}\]])", r"\1", content)
            else:
                raise ValueError(f"Invalid JSON from model (e.g. line {e.lineno}): {e}") from e
    return {}  # unreachable


def call_openai_reasoning(prompt: str, cycle_duration_days: int, start_day: int) -> dict[str, Any]:
    """Call OpenAI reasoning model; returns days array for day_index start_day to cycle_duration_days."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY not set in .env")

    try:
        response = client.chat.completions.create(
            model=OPENAI_CALENDAR_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=16000,
        )
    except Exception as e:
        err_msg = str(e).lower()
        if ("o1" in OPENAI_CALENDAR_MODEL or "o3" in OPENAI_CALENDAR_MODEL) and (
            "model" in err_msg or "not found" in err_msg or "invalid" in err_msg
        ):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=16000,
            )
        else:
            raise

    if not response.choices:
        raise ValueError("No choices in OpenAI response.")
    choice = response.choices[0]
    message = choice.message if hasattr(choice, "message") else getattr(choice, "message", None)
    content = (getattr(message, "content", None) or "") if message else ""
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
    if json_match:
        content = json_match.group(1).strip()
    raw = _parse_json_response(content)
    if "days" not in raw or not isinstance(raw["days"], list):
        raise ValueError("Model response missing 'days' array.")
    num_days = cycle_duration_days - start_day + 1
    days = raw["days"]
    if len(days) > num_days:
        days = days[:num_days]
    while len(days) < num_days:
        days.append({
            "day_index": start_day + len(days),
            "stage_name": "Unknown",
            "tasks": ["See previous/next stage for context."],
        })
    for i in range(len(days)):
        if not isinstance(days[i], dict):
            days[i] = {"day_index": start_day + i, "stage_name": "Unknown", "tasks": []}
        days[i]["day_index"] = start_day + i
        if (start_day + i) >= 47 and "weather_note" not in days[i]:
            days[i]["weather_note"] = "See seasonal outlook for this period."
    raw["days"] = days
    return raw


def merge_forecast_into_days(
    days: list[dict[str, Any]],
    forecast: list[dict[str, Any]],
    cycle_duration_days: int,
) -> None:
    """In-place: fill weather by day_index. Days 1-16 get forecast; day 17+ get repeated 16th day. Works when days array starts at day_index > 1."""
    if not forecast:
        return
    last = forecast[min(15, len(forecast) - 1)]
    repeat_weather = {
        "temperature_c": last.get("temperature_c"),
        "humidity_percent": last.get("humidity_percent"),
        "rainfall_mm": last.get("rainfall_mm"),
    }
    for target in days:
        if not isinstance(target, dict):
            continue
        day_idx = int(target.get("day_index", 0))
        if day_idx < 1 or day_idx > cycle_duration_days:
            continue
        if day_idx <= 16 and day_idx <= len(forecast):
            target["weather"] = {
                "temperature_c": forecast[day_idx - 1].get("temperature_c"),
                "humidity_percent": forecast[day_idx - 1].get("humidity_percent"),
                "rainfall_mm": forecast[day_idx - 1].get("rainfall_mm"),
            }
        else:
            target["weather"] = dict(repeat_weather)


def save_calendar(
    variable: dict[str, Any],
    forecast: list[dict[str, Any]],
    days: list[dict[str, Any]],
    cycle_duration_days: int,
    start_day: int,
) -> None:
    """Write data/calendar.json. No current date stored. start_day = first day_index in days (1 or e.g. 5 after remake)."""
    climate = variable.get("climate") or {}
    weather_baseline = {
        "temperature_c": climate.get("temperature_c"),
        "humidity_percent": climate.get("humidity_percent"),
        "rainfall_mm": climate.get("rainfall_mm"),
    }
    forecast_snapshot = [
        {"temperature_c": d.get("temperature_c"), "humidity_percent": d.get("humidity_percent"), "rainfall_mm": d.get("rainfall_mm")}
        for d in forecast
    ]
    calendar = {
        "weather_baseline": weather_baseline,
        "cycle_duration_days": cycle_duration_days,
        "start_day": start_day,
        "forecast_days": 16,
        "location": variable.get("location"),
        "crop": variable.get("crop"),
        "season": variable.get("crop", {}).get("season"),
        "days": days,
        "forecast_snapshot": forecast_snapshot,
    }
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CALENDAR_PATH, "w", encoding="utf-8") as f:
        json.dump(calendar, f, indent=2, ensure_ascii=False)
    end_day = days[-1].get("day_index", start_day) if days else start_day
    print(f"Written to {CALENDAR_PATH} (days {start_day}–{end_day})")


def run() -> None:
    """Load variable and persistent; ensure crop; decide regenerate; fetch 16-day forecast; generate full calendar; save."""
    variable = load_variable()
    persistent = load_persistent()

    loc = variable.get("location") or {}
    crop = variable.get("crop") or {}
    state = (loc.get("state") or "").strip()
    city = (loc.get("city") or "").strip()
    crop_name = (crop.get("crop_name") or "").strip()
    season = (crop.get("season") or "").strip()

    if not crop_name:
        print("Error: variable.json missing crop.crop_name.", file=sys.stderr)
        sys.exit(1)

    persistent = ensure_crop_in_persistent(crop_name, state, season, persistent)
    crop_key = normalize_crop_key(crop_name, state)
    if crop_key not in persistent:
        print("Error: crop entry not in persistent after ensure_crop_data.", file=sys.stderr)
        sys.exit(1)
    persistent_entry = persistent[crop_key]

    cycle_duration_days = get_cycle_duration_days(persistent_entry, season)
    current_day = get_current_day(variable, cycle_duration_days)

    calendar = load_calendar()
    current_climate = variable.get("climate") or {}

    if calendar is None:
        do_regenerate = True
    else:
        do_regenerate = should_regenerate(current_climate, calendar, current_day)
        if not do_regenerate:
            print("No significant change; calendar unchanged.")
            return

    coords = loc.get("coordinates") or {}
    lat = coords.get("lat")
    lon = coords.get("lon")
    if lat is None or lon is None:
        print("Error: variable.json missing location.coordinates (lat, lon).", file=sys.stderr)
        sys.exit(1)

    forecast = fetch_16day_forecast(float(lat), float(lon))
    if len(forecast) < 16:
        print("Warning: forecast returned fewer than 16 days.", file=sys.stderr)

    # When remaking (threshold hit): send past days 1 to day_of_cycle-1 to LLM for context; save only day_of_cycle to 120
    is_remake = calendar is not None
    start_day = current_day if is_remake else 1

    past_days = None
    if is_remake and start_day > 1:
        # Past data (days 1 to start_day-1) for LLM context (only if current calendar has those days)
        all_days = calendar.get("days") or []
        past_days = [d for d in all_days if isinstance(d, dict) and (d.get("day_index") or 0) < start_day]
        past_days.sort(key=lambda d: d.get("day_index", 0))

    prompt = build_calendar_prompt(
        variable, persistent_entry, forecast, cycle_duration_days, start_day, past_days=past_days
    )
    days_payload = call_openai_reasoning(prompt, cycle_duration_days, start_day)
    new_days = days_payload.get("days") or []

    # Save only days start_day to cycle_duration_days (index from start_day onward; do not prepend past days)
    final_days = new_days

    merge_forecast_into_days(final_days, forecast, cycle_duration_days)
    save_calendar(variable, forecast, final_days, cycle_duration_days, start_day)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
