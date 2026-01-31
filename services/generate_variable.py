"""
Standalone script: no imports from other Python files in the project.
Uses only Python standard library (json, sys, pathlib, urllib).

Prompts in terminal for:
  1) State, City (India)
  2) Crop name
  3) Season: Kharif / Rabi / Summer

Generates variable.json aligned with crop suitability modeling (CropSuite-style):
- Soil: WRB classification + SoilGrids properties (texture, organic carbon, pH,
  bulk density, coarse fragments) at standard depths for suitability membership functions.
- Climate: current temperature, humidity, precipitation (Open-Meteo).
- Structure supports Liebig's law of the minimum (soil + climate inputs for suitability).
"""
import json
import sys
import time
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import urlopen

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
# Data folder at project root; script lives in services/
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
VARIABLE_PATH = _DATA_DIR / "variable.json"
SOIL_FALLBACK = "Unknown (API unavailable)"

VALID_SEASONS = {"kharif", "rabi", "summer"}
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
SOILGRIDS_BASE = "https://rest.isric.org/soilgrids/v2.0"
# CropSuite-relevant SoilGrids properties (texture, soc, pH, bdod, cfvo)
SOILGRIDS_PROPERTIES = ["clay", "sand", "silt", "soc", "phh2o", "bdod", "cfvo"]
SOILGRIDS_DEPTHS = ["0-5cm", "5-15cm", "15-30cm"]
SOILGRIDS_TIMEOUT = 30

# Conventional units for soil_properties (after d_factor scaling)
SOIL_PROPERTIES_UNITS = {
    "clay": "%",
    "sand": "%",
    "silt": "%",
    "soc": "g/kg",
    "phh2o": "pH",
    "bdod": "kg/dm³",
    "cfvo": "vol%",
}

# Units for climate values (no date stored)
CLIMATE_UNITS = {
    "temperature_c": "°C",
    "humidity_percent": "%",
    "rainfall_mm": "mm",
}


def get_input(prompt: str) -> str:
    """Read a line from stdin and strip whitespace."""
    return input(prompt).strip()


def validate_season(season: str) -> str:
    """Return normalized season (title case) or raise ValueError."""
    s = season.strip().lower()
    if s not in VALID_SEASONS:
        raise ValueError(
            f"Invalid season '{season}'. Must be one of: Kharif, Rabi, Summer"
        )
    return s.title()


def geocode(city: str, state: str) -> tuple[float, float]:
    """Resolve city, state in India to (latitude, longitude). Raises on failure."""
    # Prefer shorter query so API returns results; then filter by India and state
    query = f"{city}, India"
    url = f"{GEOCODING_URL}?name={quote(query)}&count=10"
    try:
        with urlopen(url, timeout=10) as resp:
            data = json.load(resp)
    except Exception as e:
        raise RuntimeError(f"Geocoding request failed: {e}") from e

    results = data.get("results") or []
    state_lower = state.strip().lower()
    in_results = [r for r in results if r.get("country_code") == "IN"]
    if not in_results:
        raise ValueError(f"No Indian location found for: {city}, {state}")

    # Prefer result whose admin1 (state) matches; otherwise use first IN result
    for r in in_results:
        if (r.get("admin1") or "").strip().lower() == state_lower:
            return float(r["latitude"]), float(r["longitude"])
    return float(in_results[0]["latitude"]), float(in_results[0]["longitude"])


def _usda_texture_class(clay_pct: float, sand_pct: float) -> str:
    """Derive USDA texture class from clay and sand (%). Silt = 100 - clay - sand."""
    if clay_pct is None or sand_pct is None:
        return "Unknown"
    silt = 100.0 - float(clay_pct) - float(sand_pct)
    c, s, si = float(clay_pct), float(sand_pct), silt
    if c >= 40:
        return "Clay" if si <= 40 else "Silty clay" if s <= 45 else "Sandy clay"
    if c >= 27:
        return "Clay loam" if si < 28 and s <= 52 else "Silty clay loam" if s <= 20 else "Sandy clay loam"
    if c >= 20:
        return "Loam" if (s <= 52 and si >= 28 and si < 50) else "Silt loam" if si >= 50 else "Sandy loam"
    if c >= 12:
        return "Silt loam" if si >= 50 else "Sandy loam" if s >= 43 else "Loam"
    if si >= 50:
        return "Silt"
    if s >= 85:
        return "Sand"
    if s >= 70:
        return "Loamy sand"
    if s >= 43:
        return "Sandy loam"
    if si >= 50:
        return "Silt loam"
    return "Loam"


def _parse_soil_properties_response(data: dict) -> dict:
    """
    Parse SoilGrids properties/query GeoJSON into soil_properties by depth.
    Applies d_factor from API so values are in conventional units:
    - clay, sand, silt: % (d_factor 10: g/kg -> %)
    - phh2o: pH (d_factor 10: stored as pH×10)
    - soc: g/kg (d_factor 10: dg/kg -> g/kg)
    - bdod: kg/dm³ (d_factor 100: cg/cm³ -> kg/dm³)
    - cfvo: vol% (d_factor 10: cm³/dm³ -> cm³/100cm³)
    """
    out: dict[str, dict] = {}
    props = data.get("properties") or {}
    layers = props.get("layers") or []
    for layer in layers:
        name = layer.get("name")
        if not name:
            continue
        um = layer.get("unit_measure") or {}
        d_factor = um.get("d_factor")
        for depth_block in layer.get("depths") or []:
            label = depth_block.get("label") or "0-5cm"
            if label not in out:
                out[label] = {}
            vals = depth_block.get("values") or {}
            val = vals.get("mean")
            if val is None and vals.get("Q0.5") is not None:
                val = vals.get("Q0.5")
            if val is not None and d_factor is not None:
                val = round(float(val) * (1.0 / d_factor), 2)
            out[label][name] = val
    return out


def _all_properties_null(soil_properties: dict) -> bool:
    """True if every depth has all null values."""
    if not soil_properties:
        return True
    for depth_vals in soil_properties.values():
        if any(v is not None for v in (depth_vals or {}).values()):
            return False
    return True


# Offsets (deg) to try when the exact point returns null (e.g. urban mask)
_NEARBY_OFFSETS_DEG = [(0.02, 0), (0, 0.02), (-0.02, 0), (0, -0.02), (0.02, 0.02)]


def fetch_soil_properties(lat: float, lon: float) -> tuple[dict, str | None]:
    """
    Fetch CropSuite-relevant soil properties from SoilGrids properties/query.
    Returns (soil_properties_by_depth, note). If the point returns all null (e.g. urban mask),
    tries nearby offsets to get a rural pixel. note is set when a fallback point was used.
    """
    def _request(la: float, lo: float) -> dict:
        params = {"lat": la, "lon": lo, "value": "mean"}
        query = urlencode(params) + "&" + "&".join(f"property={p}" for p in SOILGRIDS_PROPERTIES)
        query += "&" + "&".join(f"depth={d}" for d in SOILGRIDS_DEPTHS)
        url = f"{SOILGRIDS_BASE}/properties/query?{query}"
        try:
            with urlopen(url, timeout=SOILGRIDS_TIMEOUT) as resp:
                return _parse_soil_properties_response(json.load(resp))
        except Exception:
            return {}

    result = _request(lat, lon)
    note = None
    if _all_properties_null(result):
        note = "Exact point returned no property data (SoilGrids masks urban areas)."
        for dlat, dlon in _NEARBY_OFFSETS_DEG:
            result = _request(lat + dlat, lon + dlon)
            if not _all_properties_null(result):
                note = f"Used nearby point (lat={lat + dlat:.4f}, lon={lon + dlon:.4f}); exact point had no data (urban mask)."
                break
        else:
            note = "No property data at this point or nearby; SoilGrids masks urban areas and some pixels have no data."
    return result, note


def fetch_soil(lat: float, lon: float) -> tuple[str, dict, dict]:
    """
    Fetch region-based soil type and soil map from ISRIC SoilGrids REST API v2.
    - classification/query: WRB soil type and probabilities.
    - properties/query: texture, soc, pH, bdod, cfvo for CropSuite-style suitability.
    If the exact point has no property data (e.g. urban mask), tries a nearby point.
    Returns (soil_type, soil_map, soil_properties). On classification failure uses SOIL_FALLBACK.
    """
    soil_properties, properties_note = fetch_soil_properties(lat, lon)

    params = urlencode({"lat": lat, "lon": lon, "number_classes": 5})
    url = f"{SOILGRIDS_BASE}/classification/query?{params}"
    try:
        with urlopen(url, timeout=SOILGRIDS_TIMEOUT) as resp:
            data = json.load(resp)
    except Exception:
        return SOIL_FALLBACK, {}, soil_properties

    soil_type = (data.get("wrb_class_name") or "").strip() or SOIL_FALLBACK

    # Texture class from top layer (0-5cm) for suitability; CropSuite derives from sand+clay
    texture_class = None
    top = soil_properties.get("0-5cm")
    if not top and soil_properties:
        top = next(iter(soil_properties.values()), None)
    if top and top.get("clay") is not None and top.get("sand") is not None:
        texture_class = _usda_texture_class(top["clay"], top["sand"])

    soil_map = {
        "source": "ISRIC SoilGrids v2",
        "classification_endpoint": "classification/query",
        "properties_endpoint": "properties/query",
        "coordinates": {"lat": lat, "lon": lon},
        "wrb_class_name": data.get("wrb_class_name"),
        "wrb_class_value": data.get("wrb_class_value"),
        "wrb_class_probability": data.get("wrb_class_probability") or [],
        "texture_class_usda": texture_class,
        "depths_available": list(soil_properties.keys()),
    }
    if properties_note:
        soil_map["properties_note"] = properties_note
    return soil_type, soil_map, soil_properties


def _weather_fallback() -> dict:
    """Fallback climate when Open-Meteo is unreachable (e.g. SSL/network error)."""
    return {
        "temperature_c": None,
        "humidity_percent": None,
        "rainfall_mm": None,
        "note": "Weather API unavailable (e.g. SSL/network error). Fill manually if needed.",
    }


def fetch_weather(lat: float, lon: float, retries: int = 3) -> dict:
    """Fetch current temp, humidity and today's precipitation from Open-Meteo. Retries on SSL/connection errors."""
    params = (
        f"latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m"
        "&daily=precipitation_sum&forecast_days=1"
        "&timezone=auto"
    )
    url = f"{FORECAST_URL}?{params}"
    last_err = None
    for attempt in range(retries):
        try:
            with urlopen(url, timeout=15) as resp:
                data = json.load(resp)
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(2)
            continue
        current = data.get("current") or {}
        daily = data.get("daily") or {}
        time_list = daily.get("time") or []
        precip_list = daily.get("precipitation_sum") or []
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        return {
            "temperature_c": temp if temp is not None else 0.0,
            "humidity_percent": humidity if humidity is not None else 0,
            "rainfall_mm": precip_list[0] if precip_list else 0.0,
        }
    raise RuntimeError(f"Weather request failed after {retries} attempts: {last_err}") from last_err


def main() -> None:
    print("Enter the following (India):")
    print("1) State, City")
    state = get_input("State: ")
    city = get_input("City: ")
    print("2) Crop name")
    crop_name = get_input("Crop name: ")
    print("3) Kharif / Rabi / Summer")
    season_raw = get_input("Season: ")

    if not state:
        print("Error: State cannot be empty.", file=sys.stderr)
        sys.exit(1)
    if not city:
        print("Error: City cannot be empty.", file=sys.stderr)
        sys.exit(1)
    if not crop_name:
        print("Error: Crop name cannot be empty.", file=sys.stderr)
        sys.exit(1)

    try:
        season = validate_season(season_raw)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        lat, lon = geocode(city, state)
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    soil_type, soil_map, soil_properties = fetch_soil(lat, lon)

    try:
        weather = fetch_weather(lat, lon)
    except RuntimeError as e:
        print(f"Warning: {e}", file=sys.stderr)
        print("Writing variable.json with placeholder climate (fill manually if needed).", file=sys.stderr)
        weather = _weather_fallback()

    # CropSuite-style structure: location + soil (WRB + properties by depth) + climate
    # Plan from day 1; day_of_cycle = current day (1-based). No current date stored.
    out = {
        "location": {
            "state": state,
            "city": city,
            "coordinates": {"lat": lat, "lon": lon},
        },
        "crop": {
            "crop_name": crop_name.strip(),
            "season": season,
        },
        "day_of_cycle": 1,
        "soil_type": soil_type,
        "soil_map": soil_map,
        "soil_properties": soil_properties,
        "soil_properties_units": SOIL_PROPERTIES_UNITS,
        "climate": weather,
        "climate_units": CLIMATE_UNITS,
    }

    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(VARIABLE_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Written to {VARIABLE_PATH}")


def generate_variable(state: str, city: str, crop_name: str, season: str) -> dict:
    """
    Non-interactive: generate variable.json from state, city, crop_name, season.
    Writes to data/variable.json and returns the generated dict.
    Raises ValueError on validation, RuntimeError on geocoding/weather failure.
    """
    state = (state or "").strip()
    city = (city or "").strip()
    crop_name = (crop_name or "").strip()
    season_raw = (season or "").strip()
    if not state:
        raise ValueError("State cannot be empty.")
    if not city:
        raise ValueError("City cannot be empty.")
    if not crop_name:
        raise ValueError("Crop name cannot be empty.")
    try:
        season = validate_season(season_raw)
    except ValueError as e:
        raise ValueError(str(e)) from e
    try:
        lat, lon = geocode(city, state)
    except (ValueError, RuntimeError) as e:
        raise RuntimeError(str(e)) from e
    soil_type, soil_map, soil_properties = fetch_soil(lat, lon)
    try:
        weather = fetch_weather(lat, lon)
    except RuntimeError:
        weather = _weather_fallback()
    out = {
        "location": {"state": state, "city": city, "coordinates": {"lat": lat, "lon": lon}},
        "crop": {"crop_name": crop_name, "season": season},
        "day_of_cycle": 1,
        "soil_type": soil_type,
        "soil_map": soil_map,
        "soil_properties": soil_properties,
        "soil_properties_units": SOIL_PROPERTIES_UNITS,
        "climate": weather,
        "climate_units": CLIMATE_UNITS,
    }
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(VARIABLE_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return out


if __name__ == "__main__":
    main()
